"""Evaluate declared active job-search classifiers without target leakage."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


SEED = 12
THRESHOLD = .5
MIN_N = 30
TARGET = "planos_mudar_emprego_6m"
FEATURES = ["senioridade_declarada", "nivel_ensino", "vinculo_grupo", "modelo_trabalho_declarado", "experiencia_dados_faixa"]
ACTIVE = {
    "Estou em busca de oportunidades dentro ou fora do Brasil": 1,
    "Estou em busca de oportunidades, mas apenas fora do Brasil": 1,
    "Não estou buscando, mas me considero aberto a outras oportunidades": 0,
    "Não estou buscando e não pretendo mudar de emprego nos próximos 6 meses": 0,
}
NAMES = {"majoritaria": "Classe majoritaria", "logistica": "Regressao logistica", "arvore": "Arvore simples"}
ORDER = list(NAMES)
NE = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def active_target(series):
    if (series.notna() & ~series.isin(ACTIVE)).any():
        raise ValueError("Unmapped job-search answer; review the target before training.")
    return series.map(ACTIVE).astype("Int64")


def eligible(frame):
    frame = frame.loc[frame.vive_no_brasil.fillna(False)].copy()
    frame["alvo_busca_ativa"] = active_target(frame[TARGET])
    return frame.loc[frame.alvo_busca_ativa.notna()].copy().reset_index(drop=True)


def features(frame):
    """Select only neutral profile categories, never the raw work-status answer."""
    result = frame.loc[:, FEATURES].copy()
    for field in FEATURES:
        result[field] = result[field].astype(object).where(result[field].notna(), np.nan)
    return result


def split_indices(frame):
    if frame.respondente_id.isna().any() or frame.respondente_id.duplicated().any():
        raise ValueError("Respondent row identifiers must be unique and nonmissing.")
    y = frame.alvo_busca_ativa.astype(int).to_numpy()
    if set(y) != {0, 1}:
        raise ValueError("Both target classes are required.")
    return train_test_split(np.arange(len(frame)), test_size=.2, stratify=y, random_state=SEED)


def make_model(key):
    if key == "majoritaria":
        return DummyClassifier(strategy="prior")
    if key == "logistica":
        estimator = LogisticRegression(C=1., solver="lbfgs", max_iter=2000, random_state=SEED)
    elif key == "arvore":
        estimator = DecisionTreeClassifier(max_depth=4, min_samples_leaf=40, random_state=SEED)
    else:
        raise ValueError(key)
    return Pipeline([
        ("imputar", SimpleImputer(strategy="constant", fill_value="Nao informado", keep_empty_features=True)),
        ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ("modelo", estimator),
    ])


def positive_probability(model, x):
    classes = list(model.classes_)
    if 1 not in classes:
        raise ValueError("The model has no active-search class.")
    return model.predict_proba(x)[:, classes.index(1)]


def labels(probabilities, threshold=THRESHOLD):
    p = np.asarray(probabilities, dtype=float)
    if not 0 <= threshold <= 1 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid probabilities or threshold")
    return (p >= threshold).astype(int)


def metricas(y, probabilities, threshold=THRESHOLD):
    y = np.asarray(y)
    p = np.asarray(probabilities, dtype=float)
    if not len(y) or len(y) != len(p) or not set(y).issubset({0, 1}):
        raise ValueError("Invalid binary targets")
    y = y.astype(int)
    predicted = labels(p, threshold)
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    both = len(np.unique(y)) == 2
    return {"n": len(y), "n_ativos": int(y.sum()), "n_previstos_ativos": int(predicted.sum()),
            "limiar": threshold, "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "acuracia": float(accuracy_score(y, predicted)),
            "precisao": float(precision_score(y, predicted, zero_division=0)),
            "recall": float(recall_score(y, predicted, zero_division=0)),
            "f1": float(f1_score(y, predicted, zero_division=0)),
            "roc_auc": float(roc_auc_score(y, p)) if both else None,
            "average_precision": float(average_precision_score(y, p)) if both else None,
            "brier": float(brier_score_loss(y, p))}


def winner(validation):
    return validation.sort_values(["ap_media", "ordem"], ascending=[False, True], kind="stable").iloc[0].modelo


class Classificacao:
    def __init__(self, area):
        self.area = Path(area).resolve()
        self.data = self.area.parent / "datasets"
        self.outputs, self.local = self.area / "resultados", self.area / "resultados_locais"
        for folder in [self.outputs / "graficos", self.outputs / "tabelas", self.local]:
            folder.mkdir(parents=True, exist_ok=True)
        path = self.data / "tratados/state_of_data_brasil.parquet"
        preparation = json.loads((self.data / "qualidade/execucao_preparacao.json").read_text(encoding="utf-8"))
        expected = next(p["sha256"] for p in preparation["produtos"] if p["arquivo"] == "tratados/state_of_data_brasil.parquet")
        self.source_hash = digest(path)
        if self.source_hash != expected:
            raise ValueError("State of Data changed after stage 02. Revalidate preparation first.")
        self.source = pd.read_parquet(path)
        self.frame = eligible(self.source)
        self.train_idx, self.test_idx = split_indices(self.frame)
        self.x = features(self.frame)
        self.y = self.frame.alvo_busca_ativa.astype(int).to_numpy()
        self.x_train, self.x_test = self.x.iloc[self.train_idx], self.x.iloc[self.test_idx]
        self.y_train, self.y_test = self.y[self.train_idx], self.y[self.test_idx]
        self.results, self.models, self.test_probabilities = {}, {}, {}
        spec = importlib.util.spec_from_file_location("radar_classification_theme", self.area.parents[1] / "app/theme.py")
        self.theme = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.theme)
        self.colors = [self.theme.TEXTO_SECUNDARIO, self.theme.LARANJA, self.theme.GRAFITE]
        self.styles = ["--", "-", "-."]
        plt.rcParams.update({"font.family": ["DejaVu Sans"], "font.size": 10, "axes.spines.top": False,
                             "axes.spines.right": False, "axes.edgecolor": self.theme.BORDA_CLARA,
                             "grid.color": self.theme.TRILHO_GRAFICO, "text.color": self.theme.TEXTO})

    def figure(self, cols=1, size=(11, 6.3)):
        return plt.subplots(1, cols, figsize=size, squeeze=False)

    def finish(self, fig, key, title, note=""):
        fig.suptitle(textwrap.fill(title, 94), fontsize=14, fontweight="bold", x=.02, y=.98, ha="left")
        fig.tight_layout(rect=(0, .15, 1, .90), pad=1.8)
        caption = "State of Data Brazil 2024-2025; residentes no Brasil; alvo respondido. Classe 1 = busca ativa declarada. " + note
        fig.text(.02, .025, textwrap.fill(caption, 145), fontsize=8, color=self.theme.TEXTO_SECUNDARIO)
        path = self.outputs / "graficos" / f"{key}.png"
        fig.savefig(path, dpi=140, facecolor=self.theme.BRANCO)
        plt.close(fig)
        return path

    def register(self, key, tables, figures, interpretation):
        for name, table in tables.items():
            table.to_csv(self.outputs / "tabelas" / f"{key}_{name}.csv", index=False, encoding="utf-8-sig")
        result = {"tabelas": tables, "graficos": figures, "interpretacao": interpretation}
        self.results[key] = result
        return result

    def scope(self):
        counts = pd.DataFrame([{"particao": name, "n": len(y), "sem_busca_ativa": int((y == 0).sum()),
                                "busca_ativa": int(y.sum()), "proporcao_ativa": float(y.mean())}
                               for name, y in [("Treino (80%)", self.y_train), ("Teste (20%)", self.y_test)]])
        missing = pd.DataFrame([{"variavel": field, "ausentes_treino": int(self.x_train[field].isna().sum()),
                                 "ausentes_teste": int(self.x_test[field].isna().sum()),
                                 "tratamento": "categoria explicita; sem inferir senioridade"} for field in FEATURES])
        fig, axes = self.figure(size=(10.5, 5.5))
        ax = axes[0, 0]
        ax.barh(range(2), 1-counts.proporcao_ativa, color=self.theme.NEUTRO_GRAFICO, label="0: sem busca ativa")
        ax.barh(range(2), counts.proporcao_ativa, left=1-counts.proporcao_ativa, color=self.theme.LARANJA, label="1: busca ativa")
        ax.set_yticks(range(2), [f"{r.particao} (n={r.n:,})" for r in counts.itertuples()])
        for i, row in enumerate(counts.itertuples()):
            ax.text((1-row.proporcao_ativa)/2, i, f"{row.sem_busca_ativa:,}", ha="center", va="center")
            ax.text(1-row.proporcao_ativa/2, i, f"{row.busca_ativa:,}", ha="center", va="center")
        ax.set(xlim=(0, 1), xlabel="Proporcao em cada particao")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        handles, legend_labels = ax.get_legend_handles_labels()
        fig.legend(handles, legend_labels, loc="upper right", bbox_to_anchor=(.98, .89), ncol=2, fontsize=9)
        missing_target = len(self.source) - len(self.frame)
        note = (f"Dos {len(self.source):,} residentes no Brasil, {missing_target} nao tem alvo respondido e nao recebem classe 0. "
                f"Restam {len(self.frame):,} respostas, {int(self.y.sum()):,} positivas ({100*self.y.mean():.1f}%). "
                f"A separacao estratificada, semente 12, reserva {len(self.y_test)} respostas para teste e {len(self.y_train)} para treino. "
                "A classe 0 inclui pessoas abertas a oportunidades, mas que nao declaram busca ativa. O alvo e intencao contemporanea, "
                "nao mudanca de emprego futura. As ausencias se concentram em ramos do questionario; os elegiveis nao representam todos os desempregados "
                "ou toda a populacao de TI. Senioridade ausente nao vira Junior. Vinculo agrupado remove mencoes de busca presentes no texto bruto.")
        return self.register("C0", {"particoes_classes": counts, "cobertura_entradas": missing}, [self.finish(fig, "C0_classes_particoes", "Busca ativa declarada: equilibrio das classes no treino e teste", "Estratificacao 80/20; contagens nas barras. Alvo ausente excluido, nunca convertido em 0.")], note)

    def fit(self):
        splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        folds = list(splitter.split(self.x_train, self.y_train))
        fold_rows, validation_rows = [], []
        self.oof = {}
        for order, key in enumerate(ORDER):
            probabilities = np.full(len(self.y_train), np.nan)
            for fold, (train, validation) in enumerate(folds, start=1):
                model = make_model(key)
                model.fit(self.x_train.iloc[train], self.y_train[train])
                p = positive_probability(model, self.x_train.iloc[validation])
                probabilities[validation] = p
                fold_rows.append({"modelo": key, "fold": fold, **metricas(self.y_train[validation], p)})
            if not np.isfinite(probabilities).all():
                raise ValueError("Out-of-fold predictions are incomplete")
            self.oof[key] = probabilities
            rows = pd.DataFrame([row for row in fold_rows if row["modelo"] == key])
            validation_rows.append({"modelo": key, "ordem": order, "ap_media": rows.average_precision.mean(),
                                    "ap_desvio_folds": rows.average_precision.std(ddof=1), "f1_medio_limiar_05": rows.f1.mean(),
                                    "roc_auc_media": rows.roc_auc.mean(), "n_folds": 5})
        self.validation = pd.DataFrame(validation_rows)
        self.selected = winner(self.validation)
        test_rows = []
        local_test = self.frame.iloc[self.test_idx][["respondente_id"]].reset_index(drop=True).copy()
        local_test["alvo_observado"] = self.y_test
        local_train = self.frame.iloc[self.train_idx][["respondente_id"]].reset_index(drop=True).copy()
        local_train["alvo_observado"] = self.y_train
        for key in ORDER:
            model = make_model(key).fit(self.x_train, self.y_train)
            self.models[key] = model
            p = positive_probability(model, self.x_test)
            self.test_probabilities[key] = p
            local_test[f"probabilidade_{key}"] = p
            local_test[f"classe_{key}"] = labels(p)
            local_train[f"probabilidade_oof_{key}"] = self.oof[key]
            test_rows.append({"modelo": key, **metricas(self.y_test, p)})
        self.metrics = pd.DataFrame(test_rows)
        local_test.to_parquet(self.local / "previsoes_teste.parquet", index=False)
        local_train.to_parquet(self.local / "previsoes_oof_treino.parquet", index=False)
        encoder = self.models["logistica"].named_steps["codificar"]
        categories = {field: list(values) for field, values in zip(FEATURES, encoder.categories_)}
        self.audit = {"fonte_sha256": self.source_hash, "alvo_original": TARGET, "classe_positiva": 1,
                      "mapeamento_alvo": ACTIVE, "entradas": FEATURES, "semente": SEED, "fracao_teste": .2,
                      "n_treino": len(self.y_train), "n_teste": len(self.y_test), "limiar_fixo": THRESHOLD,
                      "selecao": "Maior Average Precision media em 5 folds estratificados do treino; empate favorece simplicidade",
                      "modelo_escolhido_antes_do_teste": self.selected, "categorias_aprendidas_treino": categories,
                      "hiperparametros_fixos": {"logistica": {"C": 1., "solver": "lbfgs", "max_iter": 2000},
                                               "arvore": {"max_depth": 4, "min_samples_leaf": 40}},
                      "hash_ids_treino": hashlib.sha256("\n".join(local_train.respondente_id).encode()).hexdigest(),
                      "hash_ids_teste": hashlib.sha256("\n".join(local_test.respondente_id).encode()).hexdigest(),
                      "sem_pesos_ou_reamostragem": True, "sem_ajuste_pelo_teste": True,
                      "privacidade": "IDs e probabilidades individuais apenas em resultados_locais, ignorados pelo Git"}
        (self.outputs / "auditoria_modelagem.json").write_text(json.dumps(self.audit, ensure_ascii=False, indent=2), encoding="utf-8")
        selected = self.validation.set_index("modelo").loc[self.selected]
        note = (f"A escolha feita somente no treino foi **{NAMES[self.selected]}**, com Average Precision media {selected.ap_media:.3f} "
                f"em cinco folds (desvio entre folds {selected.ap_desvio_folds:.3f}, nao intervalo de confianca). "
                "Cada fold ajusta imputacao, categorias e modelo apenas nos seus dados de treino. A referencia aprende a proporcao das classes "
                "no treino e decide a classe majoritaria. Os tres modelos sao depois reajustados nos 80% e avaliados nos mesmos 20% reservados. "
                "C, profundidade e tamanho minimo de folha sao fixos; limiar 0,5 definido previamente, sem otimizacao. "
                "O teste nao decide modelo, hiperparametros ou limiar. As probabilidades OOF sao usadas apenas para diagnostico interno.")
        return self.register("C1", {"validacao_folds": pd.DataFrame(fold_rows), "selecao_treino": self.validation, "metricas_teste": self.metrics}, [], note)

    def performance(self):
        fig, axes = self.figure(size=(12, 6.4))
        ax = axes[0, 0]
        fields = ["acuracia", "precisao", "recall", "f1"]
        for i, key in enumerate(ORDER):
            row = self.metrics.set_index("modelo").loc[key]
            positions = np.arange(len(fields)) + (i-1)*.24
            values = [row[field] for field in fields]
            ax.bar(positions, values, width=.22, color=self.colors[i], label=NAMES[key])
            for x, value in zip(positions, values):
                ax.text(x, value+.018, f"{value:.3f}", ha="center", fontsize=9)
        ax.set_xticks(range(4), ["Acuracia", "Precisao (1)", "Recall (1)", "F1 (1)"])
        ax.set(ylim=(0, 1.16), ylabel="Metrica (0 a 1)")
        ax.set_yticks(np.linspace(0, 1, 6))
        handles, legend_labels = ax.get_legend_handles_labels()
        fig.legend(handles, legend_labels, loc="upper right", bbox_to_anchor=(.98, .89), ncol=3, fontsize=9)
        ax.grid(axis="y", alpha=.5)
        ax.set_axisbelow(True)
        baseline = self.metrics.set_index("modelo").loc["majoritaria"]
        chosen = self.metrics.set_index("modelo").loc[self.selected]
        note = (f"A referencia acerta {100*baseline.acuracia:.1f}% simplesmente escolhendo a classe 0, mas nao identifica "
                "nenhuma busca ativa: recall e F1 iguais a zero. Por isso acuracia sozinha seria enganosa. "
                f"O modelo escolhido tem acuracia {chosen.acuracia:.3f}, precisao {chosen.precisao:.3f}, recall {chosen.recall:.3f} "
                f"e F1 {chosen.f1:.3f} no limiar 0,5. Precisao descreve a fracao correta entre positivos previstos; recall, "
                "a fracao de buscas ativas identificadas. Precisao sem positivos previstos e registrada como 0 por convencao zero_division=0, "
                "nao como evidencia de taxa populacional. F1 combina precisao e recall, mas ignora os verdadeiros negativos. "
                f"O escolhido deixa de identificar {100*(1-chosen.recall):.1f}% dos positivos; este desempenho e limitado "
                "e nao valida uma ferramenta de deteccao individual. O limiar nao foi alterado para melhorar os resultados do teste.")
        return self.register("C2", {}, [self.finish(fig, "C2_comparacao_metricas", "Teste reservado: acuracia nao conta toda a historia", f"n={len(self.y_test)}; limiar fixo=0,5; precisao/recall/F1 para classe 1. Sem ajuste no teste.")], note)

    def matrices(self):
        fig, axes = self.figure(cols=3, size=(14, 6))
        records = []
        for ax, key in zip(axes[0], ORDER):
            prediction = labels(self.test_probabilities[key])
            matrix = confusion_matrix(self.y_test, prediction, labels=[0, 1])
            rates = matrix / matrix.sum(axis=1, keepdims=True)
            ax.imshow(rates, vmin=0, vmax=1, cmap="Greys", aspect="equal")
            for row in range(2):
                for col in range(2):
                    ax.text(col, row, f"{matrix[row, col]}\n({100*rates[row, col]:.1f}%)", ha="center", va="center",
                            color=self.theme.BRANCO if rates[row, col] > .55 else self.theme.TEXTO, fontsize=12)
                    records.append({"modelo": key, "classe_observada": row, "classe_prevista": col,
                                    "n": int(matrix[row, col]), "proporcao_na_classe_observada": rates[row, col]})
            ax.set_xticks([0, 1], ["0: sem busca", "1: ativa"])
            ax.set_yticks([0, 1], ["0: sem busca", "1: ativa"])
            ax.set(title=NAMES[key], xlabel="Classe prevista", ylabel="Classe observada")
        chosen = self.metrics.set_index("modelo").loc[self.selected]
        note = (f"Para {NAMES[self.selected]}, ha {int(chosen.tp)} verdadeiros positivos, {int(chosen.fn)} falsos negativos, "
                f"{int(chosen.fp)} falsos positivos e {int(chosen.tn)} verdadeiros negativos. Um falso negativo e uma pessoa que declara "
                "busca ativa e recebe classe 0; um falso positivo recebe classe 1 sem declarar busca ativa. As porcentagens usam "
                "a classe observada como denominador e cada linha soma 100%; as contagens preservam o tamanho real das classes. "
                "Esses erros impedem usar a classificacao para rotular empregados ou orientar decisoes de contratacao, desligamento ou vigilancia.")
        return self.register("C3", {"matrizes_confusao": pd.DataFrame(records)}, [self.finish(fig, "C3_matrizes_confusao", "Matrizes de confusao: onde cada classificador erra", "Contagens e porcentagens por linha observada. Cores de 0% a 100%; limiar=0,5; mesma amostra.")], note)

    def roc(self):
        fig, axes = self.figure()
        ax = axes[0, 0]
        records = []
        for i, key in enumerate(ORDER):
            false_positive, true_positive, thresholds = roc_curve(self.y_test, self.test_probabilities[key])
            auc = self.metrics.set_index("modelo").loc[key, "roc_auc"]
            ax.plot(false_positive, true_positive, color=self.colors[i], linestyle=self.styles[i], linewidth=2,
                    label=f"{NAMES[key]} (AUC={auc:.3f})")
            records.extend({"modelo": key, "taxa_falso_positivo": fp, "taxa_verdadeiro_positivo": tp,
                            "limiar": float(threshold) if np.isfinite(threshold) else None} for fp, tp, threshold in zip(false_positive, true_positive, thresholds))
        ax.plot([0, 1], [0, 1], color=self.theme.NEUTRO_GRAFICO, linestyle=":", label="Referencia sem discriminacao")
        ax.set(xlim=(0, 1), ylim=(0, 1.03), xlabel="Taxa de falsos positivos (FP / negativos)", ylabel="Taxa de verdadeiros positivos (recall)")
        ax.legend(loc="lower right", fontsize=9)
        auc = self.metrics.set_index("modelo").loc[self.selected, "roc_auc"]
        note = (f"O modelo previamente escolhido tem ROC-AUC {auc:.3f}. A curva usa escores/probabilidades, nao somente "
                "as classes do limiar 0,5; mostra o compromisso entre falsos positivos e recall. A referencia constante tem AUC 0,5. "
                "AUC e capacidade de ordenacao, nao acuracia, probabilidade de acerto individual ou prova de causalidade. "
                "A classe positiva e 1 em todos os calculos. O teste e uma avaliacao da mesma pesquisa, nao validacao temporal externa.")
        return self.register("C4", {"curvas_roc": pd.DataFrame(records)}, [self.finish(fig, "C4_curvas_roc", "Curvas ROC: discriminacao no teste reservado", "ROC calculada com probabilidades da classe 1; AUC=0,5 indica referencia constante/sem discriminacao.")], note)

    def precision_recall(self):
        fig, axes = self.figure()
        ax = axes[0, 0]
        records = []
        for i, key in enumerate(ORDER):
            precision, recall, thresholds = precision_recall_curve(self.y_test, self.test_probabilities[key])
            ap = self.metrics.set_index("modelo").loc[key, "average_precision"]
            ax.step(recall, precision, where="post", color=self.colors[i], linestyle=self.styles[i], linewidth=2,
                    label=f"{NAMES[key]} (AP={ap:.3f})")
            records.extend({"modelo": key, "recall": r, "precisao": p, "limiar": float(thresholds[j]) if j < len(thresholds) else None}
                           for j, (p, r) in enumerate(zip(precision, recall)))
        prevalence = self.y_test.mean()
        ax.axhline(prevalence, color=self.theme.NEUTRO_GRAFICO, linestyle=":", label=f"Prevalencia no teste ({prevalence:.3f})")
        ax.set(xlim=(0, 1), ylim=(0, 1.03), xlabel="Recall da classe 1", ylabel="Precisao da classe 1")
        ax.set_xticks(np.linspace(0, 1, 6), [f"{x:.1f}" for x in np.linspace(0, 1, 6)])
        ax.set_yticks(np.linspace(0, 1, 6), [f"{x:.1f}" for x in np.linspace(0, 1, 6)])
        ax.tick_params(labelleft=True, labelbottom=True)
        ax.legend(loc="upper right", fontsize=9)
        ap = self.metrics.set_index("modelo").loc[self.selected, "average_precision"]
        note = (f"Average Precision (AP) do escolhido: {ap:.3f}; referencia constante: prevalencia de {prevalence:.3f}. "
                "AP resume a curva ponderando os incrementos de recall e nao e a area trapezoidal generica sob a PR. "
                "A leitura considera que buscas ativas sao a classe minoritaria. Ganhar recall costuma incluir mais falsos positivos. "
                "O ultimo ponto convencional da curva tem precisao 1 e recall 0, sem observacoes previstas positivas; nao prova um classificador perfeito. "
                "A precisao e a AP dependem da prevalencia, portanto nao podem ser transferidas diretamente para outra populacao.")
        return self.register("C5", {"curvas_precision_recall": pd.DataFrame(records)}, [self.finish(fig, "C5_precision_recall", "Precision-recall: qualidade ao identificar a classe minoritaria", "Average Precision (AP), nao area trapezoidal. Linha horizontal = proporcao de positivos no teste.")], note)

    def thresholds(self):
        p = self.oof[self.selected]
        table = pd.DataFrame([metricas(self.y_train, p, float(t)) for t in np.round(np.linspace(.05, .95, 19), 2)])
        fig, axes = self.figure()
        ax = axes[0, 0]
        for field, color, style in zip(["precisao", "recall", "f1"], [self.theme.LARANJA, self.theme.GRAFITE, self.theme.TEXTO_SECUNDARIO], ["-", "--", "-."]):
            ax.plot(table.limiar, table[field], label=field.capitalize(), color=color, linestyle=style, linewidth=2)
        ax.axvline(THRESHOLD, color=self.theme.NEUTRO_GRAFICO, linestyle=":", label="Limiar adotado antes do teste (0,5)")
        ax.set(xlim=(0, 1), ylim=(0, 1.03), xlabel="Limiar da probabilidade estimada", ylabel="Metrica da classe 1")
        ax.set_xticks(np.linspace(0, 1, 6), [f"{x:.1f}" for x in np.linspace(0, 1, 6)])
        ax.set_yticks(np.linspace(0, 1, 6), [f"{x:.1f}" for x in np.linspace(0, 1, 6)])
        ax.tick_params(labelleft=True, labelbottom=True)
        ax.legend(loc="upper right", fontsize=9)
        note = ("Esta curva usa somente previsoes out-of-fold do treino: cada linha foi prevista por um pipeline que nao a usou "
                "no ajuste daquele fold. O modelo foi selecionado com os mesmos folds, portanto a curva e um diagnostico interno e pode ser otimista. "
                "Limiar 0,5 permanece fixo; nenhum ponto foi escolhido por maximizar F1 nesta curva ou no teste. Reduzir o limiar "
                "tende a ampliar recall e alertas falsos; aumentar pode deixar mais buscas ativas sem identificacao. Uma alteracao futura "
                "exige objetivo/custos definidos e nova validacao, nao reutilizar este teste como treino.")
        return self.register("C6", {"limiares_oof_treino": table}, [self.finish(fig, "C6_limiares_treino", "Efeito do limiar: diagnostico apenas dentro do treino", f"Modelo escolhido: {NAMES[self.selected]}; escores OOF dos {len(self.y_train)} participantes de treino; sem selecionar novo limiar.")], note)

    def calibration(self):
        frame = pd.DataFrame({"probabilidade": self.test_probabilities[self.selected], "ativo": self.y_test})
        frame["faixa"] = pd.cut(frame.probabilidade, bins=np.linspace(0, 1, 6), include_lowest=True)
        table = frame.groupby("faixa", observed=True).agg(n=("ativo", "size"), probabilidade_media=("probabilidade", "mean"), proporcao_ativa=("ativo", "mean")).reset_index()
        table["faixa"] = table.faixa.astype(str)
        table["suficiente"] = table.n.ge(MIN_N)
        table.loc[~table.suficiente, ["probabilidade_media", "proporcao_ativa"]] = np.nan
        fig, axes = self.figure()
        ax = axes[0, 0]
        ax.plot([0, 1], [0, 1], color=self.theme.NEUTRO_GRAFICO, linestyle="--", label="Probabilidade = frequencia")
        shown = table[table.suficiente]
        ax.plot(shown.probabilidade_media, shown.proporcao_ativa, color=self.theme.LARANJA, marker="o", linewidth=2, label="Faixas com n>=30")
        for row in shown.itertuples():
            ax.annotate(f"n={row.n}", (row.probabilidade_media, row.proporcao_ativa), xytext=(7, 8), textcoords="offset points", fontsize=9)
        ax.set(xlim=(0, 1), ylim=(0, 1.03), xlabel="Probabilidade estimada media na faixa", ylabel="Fracao observada de buscas ativas")
        ax.legend(loc="upper left", fontsize=9)
        brier = self.metrics.set_index("modelo").loc[self.selected, "brier"]
        note = (f"Brier score do escolhido: {brier:.3f} (menor e melhor). O grafico agrupa probabilidades do teste em cinco "
                "intervalos fixos e mostra apenas faixas com n>=30; nao recalibra o modelo. Distancia da diagonal representa "
                "diferenca entre escore medio e frequencia observada. As probabilidades nao foram calibradas externamente e nao sao "
                "riscos pessoais comprovados de demissao ou mudanca futura. Discriminacao e calibracao sao conceitos distintos.")
        return self.register("C7", {"calibracao_faixas": table}, [self.finish(fig, "C7_calibracao", "Calibracao descritiva: escores versus frequencia observada", "Cinco intervalos fixos de probabilidade; faixas com n<30 suprimidas; diagnostico sem reajuste.")], note)

    def coverage(self):
        frame = self.frame.iloc[self.test_idx].reset_index(drop=True)
        groups = [("regiao", "Brasil", np.ones(len(frame), dtype=bool)),
                  ("regiao", "Nordeste", frame.uf_sigla.isin(NE).to_numpy()),
                  ("regiao", "Pernambuco", frame.uf_sigla.eq("PE").to_numpy())]
        seniority = frame.senioridade_declarada.fillna("Nao informado")
        groups += [("senioridade", str(value), seniority.eq(value).to_numpy()) for value in sorted(seniority.unique())]
        records = []
        for dimension, group, mask in groups:
            row = {"dimensao": dimension, "grupo": group, "n": int(mask.sum()), "suficiente": bool(mask.sum() >= MIN_N)}
            if mask.sum() >= MIN_N:
                row.update(metricas(self.y_test[mask], self.test_probabilities[self.selected][mask]))
            records.append(row)
        groups_table = pd.DataFrame(records)
        encoder = self.models["logistica"].named_steps["codificar"]
        imputed = self.models["logistica"].named_steps["imputar"].transform(self.x_test)
        unknown = pd.DataFrame([{"variavel": field, "n_categoria_nova": int((~pd.Series(imputed[:, i]).isin(cats)).sum()), "n_teste": len(self.y_test)} for i, (field, cats) in enumerate(zip(FEATURES, encoder.categories_))])
        missing_by_work = self.source.assign(alvo_ausente=self.source[TARGET].isna()).groupby("vinculo_grupo").agg(n=(TARGET, "size"), alvo_ausente=("alvo_ausente", "sum")).reset_index()
        pe = groups_table[groups_table.grupo.eq("Pernambuco")].iloc[0]
        note = (f"Pernambuco tem n={int(pe.n)} no teste; " + ("metricas regionais disponiveis na tabela." if pe.suficiente else "n<30, portanto suas metricas foram suprimidas.") +
                " Brasil/NE/PE sao recortes aninhados, nao somaveis. A tabela por vinculo evidencia quem ficou sem alvo, "
                "reforcando o vies de elegibilidade do questionario; a exclusao nao equivale a nao buscar emprego. "
                "Nulos de senioridade podem vir de ramificacoes do formulario, inclusive gestao: nao representam senioridade baixa. "
                "Categorias novas do teste sao ignoradas pelo encoder sem ajustar novamente. Nao foi feita auditoria de equidade, "
                "validacao com outra pesquisa ou avaliacao temporal externa. Nao aplicar estes modelos para rotular pessoas em decisoes laborais.")
        return self.register("C8", {"cobertura_recortes": groups_table, "categorias_novas": unknown, "ausencia_alvo_por_vinculo": missing_by_work}, [], note)

    def run(self, key):
        return {"C0": self.scope, "C1": self.fit, "C2": self.performance, "C3": self.matrices, "C4": self.roc,
                "C5": self.precision_recall, "C6": self.thresholds, "C7": self.calibration, "C8": self.coverage}[key]()

    def summary(self):
        parts = ["# Sintese da classificacao de busca ativa", "Etapa 05. State of Data Brazil 2024-2025; avaliacao de intencao declarada, nao de desligamento futuro."]
        for key, result in self.results.items():
            parts += [f"## {key}", result["interpretacao"]]
        parts += ["## Uso e limites", "Estudo exploratorio com pesquisa voluntaria e um teste estratificado da mesma coleta. "
                  "Nao representa todos os profissionais de TI, nao identifica causalidade e nao valida uso em contratacao, demissao, "
                  "monitoramento de empregados ou aconselhamento individual automatizado. Nenhuma fonte CAGED ou G12 foi adicionada. "
                  "Probabilidades por participante ficam locais; resultados versionaveis sao agregados. A etapa 06 ainda exige integracao, "
                  "narrativa, usabilidade e revisao de privacidade; nenhum classificador foi integrado automaticamente ao aplicativo."]
        (self.area / "sintese_achados.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")

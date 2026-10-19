"""Temporal salary regression, using only the prepared CAGED source."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC = ["idade", "horas_contratuais"]
CATEGORICAL = ["cbo_codigo", "uf_sigla", "grau_instrucao"]
FEATURES = NUMERIC + CATEGORICAL
MODEL_NAMES = {"mediana": "Mediana do treino", "idade": "Linear: idade", "multipla": "Linear: cinco variaveis"}
ORDER = list(MODEL_NAMES)
NE = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
MIN_N = 30


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def money(value):
    return "R$ " + f"{value:,.0f}".replace(",", ".")


def number(value):
    return f"{int(value):,}".replace(",", ".")


def features(frame):
    """An explicit allowlist prevents salary, source and identifier leakage."""
    result = frame.loc[:, FEATURES].copy()
    for field, flag in [("idade", "idade_valida"), ("horas_contratuais", "horas_validas")]:
        result[field] = pd.to_numeric(result[field], errors="coerce").astype(float)
        result.loc[~frame[flag].fillna(False), field] = np.nan
    for field in CATEGORICAL:
        result[field] = result[field].astype(object).where(result[field].notna(), np.nan)
    return result


def temporal_split(frame):
    months = set(frame.competencia.astype(str).unique())
    if months != {"202501", "202502", "202503"}:
        raise ValueError(f"Expected Jan-Mar/2025 exactly, got {sorted(months)}")
    if frame.registro_id.duplicated().any():
        raise ValueError("Duplicate source row identifiers; review preparation.")
    train = frame.loc[frame.competencia.isin(["202501", "202502"])].copy()
    test = frame.loc[frame.competencia.eq("202503")].copy()
    if train.empty or test.empty:
        raise ValueError("Empty temporal partition")
    return train, test


def make_model(key):
    if key == "mediana":
        return DummyRegressor(strategy="median")
    numeric = ["idade"] if key == "idade" else NUMERIC
    if key not in {"idade", "multipla"}:
        raise ValueError(key)
    transformers = [("numericas", Pipeline([
        ("imputar", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("escala", StandardScaler()),
    ]), numeric)]
    if key == "multipla":
        transformers.append(("categoricas", Pipeline([
            ("imputar", SimpleImputer(strategy="constant", fill_value="Nao informado")),
            ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), CATEGORICAL))
    return Pipeline([
        ("preparar", ColumnTransformer(transformers, remainder="drop")),
        ("modelo", LinearRegression() if key == "idade" else Ridge(alpha=10.0, solver="cholesky")),
    ])


def metricas(y, prediction):
    y, prediction = np.asarray(y, dtype=float), np.asarray(prediction, dtype=float)
    if not len(y) or len(y) != len(prediction) or not np.isfinite(prediction).all() or not np.isfinite(y).all():
        raise ValueError("Invalid observed/predicted arrays")
    residual = y - prediction
    return {"n": len(y), "mae": float(mean_absolute_error(y, prediction)),
            "rmse": float(np.sqrt(mean_squared_error(y, prediction))),
            "r2": float(r2_score(y, prediction)) if len(y) >= 2 else None,
            "mediana_erro_absoluto": float(np.median(np.abs(residual))),
            "residuo_medio": float(residual.mean()), "previsoes_negativas": int((prediction < 0).sum())}


def winner(validation):
    """Only February validation can select a model, never March diagnostics."""
    return validation.sort_values(["mae", "ordem"], kind="stable").iloc[0].modelo


class Regressao:
    def __init__(self, area):
        self.area = Path(area).resolve()
        self.data = self.area.parent / "datasets"
        self.outputs = self.area / "resultados"
        self.local = self.area / "resultados_locais"
        for folder in [self.outputs / "graficos", self.outputs / "tabelas", self.local]:
            folder.mkdir(parents=True, exist_ok=True)
        path = self.data / "tratados/caged_ti.parquet"
        prepared = json.loads((self.data / "qualidade/execucao_preparacao.json").read_text(encoding="utf-8"))
        expected = next(p["sha256"] for p in prepared["produtos"] if p["arquivo"] == "tratados/caged_ti.parquet")
        self.source_hash = digest(path)
        if self.source_hash != expected:
            raise ValueError("CAGED changed since stage 02. Revalidate preparation first.")
        source = pd.read_parquet(path)
        self.raw_n = len(source)
        self.admissions_n = int(source.saldo.eq(1).sum())
        self.admissions = source.loc[source.saldo.eq(1) & source.salario_valido.fillna(False)].copy()
        if not np.isfinite(self.admissions.salario_real.astype(float)).all() or not self.admissions.salario_real.gt(0).all():
            raise ValueError("The salary validity flag is inconsistent with the target.")
        self.train, self.test = temporal_split(self.admissions)
        self.X_train, self.X_test = features(self.train), features(self.test)
        self.y_train = self.train.salario_real.astype(float).to_numpy()
        self.y_test = self.test.salario_real.astype(float).to_numpy()
        self.results, self.models = {}, {}
        spec = importlib.util.spec_from_file_location("radar_regression_theme", self.area.parents[1] / "app/theme.py")
        self.theme = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.theme)
        self.colors = [self.theme.NEUTRO_GRAFICO, self.theme.GRAFITE, self.theme.LARANJA]
        plt.rcParams.update({"font.family": ["DejaVu Sans"], "font.size": 10, "axes.spines.top": False,
                             "axes.spines.right": False, "axes.edgecolor": self.theme.BORDA_CLARA,
                             "grid.color": self.theme.TRILHO_GRAFICO, "text.color": self.theme.TEXTO})

    def figure(self, cols=1, size=None):
        return plt.subplots(1, cols, figsize=size or (11, 6), squeeze=False)

    def finish(self, fig, name, title, note=""):
        fig.suptitle(textwrap.fill(title, 94), fontsize=14, fontweight="bold", x=.02, y=.98, ha="left")
        fig.tight_layout(rect=(0, .14, 1, .90), pad=1.8)
        caption = "Novo CAGED MOV; admissoes de TI; salario mensal real em R$ de mar/2025. " + note
        fig.text(.02, .025, textwrap.fill(caption, 143), fontsize=8, color=self.theme.TEXTO_SECUNDARIO)
        path = self.outputs / "graficos" / f"{name}.png"
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
        records = []
        for month, frame in self.admissions.groupby("competencia", observed=True):
            records.append({"competencia": str(month), "uso": "teste final" if month == "202503" else "treino final",
                            "n": len(frame), "idade_invalida_ou_ausente": int((~frame.idade_valida.fillna(False)).sum()),
                            "horas_invalidas_ou_ausentes": int((~frame.horas_validas.fillna(False)).sum()),
                            "mediana_salario": float(frame.salario_real.median())})
        fields = pd.DataFrame([
            {"variavel": "salario_real", "papel": "alvo", "tratamento": "R$/mes; IPCA mar/2025; somente salario_valido"},
            {"variavel": "idade", "papel": "entrada numerica", "tratamento": "idade_valida=False vira ausente; mediana do treino e indicador"},
            {"variavel": "horas_contratuais", "papel": "entrada numerica", "tratamento": "horas_validas=False vira ausente; mediana do treino e indicador"},
            {"variavel": "cbo_codigo / uf_sigla / grau_instrucao", "papel": "entradas categoricas", "tratamento": "one-hot sem ordem; categorias aprendidas so no treino"},
            {"variavel": "salarios derivados / faixas / escalas do alvo", "papel": "excluidas", "tratamento": "evitar vazamento direto do alvo"},
            {"variavel": "IDs / arquivo / mes / sexo / raca-cor / outras fontes", "papel": "excluidas", "tratamento": "fora do conjunto inicial de entradas; IDs/mes servem apenas para auditoria/particao"},
        ])
        note = (f"Dos {number(self.raw_n)} movimentos, ha {number(self.admissions_n)} admissoes. "
                f"A modelagem usa {number(len(self.admissions))} salarios validos; {number(self.admissions_n-len(self.admissions))} "
                f"salarios sinalizados ficam fora desta tarefa, sem alterar a fonte. Treino final: {number(len(self.train))} eventos "
                f"de jan-fev; teste final: {number(len(self.test))} de marco. Idade e horas invalidas viram ausentes nas entradas, "
                "sem excluir eventos; imputacao, escala e categorias sao ajustadas somente no treino. Linhas de eventos semelhantes "
                "sao preservadas: nao existe identificador de pessoa/vinculo. Nenhum dado de State of Data ou G12 entra nesta etapa.")
        return self.register("R0", {"particoes": pd.DataFrame(records), "variaveis": fields}, [], note)

    def fit(self):
        january = self.train.competencia.eq("202501").to_numpy()
        february = ~january
        rows = []
        for order, key in enumerate(ORDER):
            model = make_model(key)
            model.fit(self.X_train.iloc[np.flatnonzero(january)], self.y_train[january])
            metrics = metricas(self.y_train[february], model.predict(self.X_train.iloc[np.flatnonzero(february)]))
            rows.append({"modelo": key, "ordem": order, **metrics})
        self.validation = pd.DataFrame(rows)
        self.selected = winner(self.validation)
        self.predictions = self.test[["registro_id", "competencia", "uf_sigla", "area_ti", "cbo_codigo"]].copy().reset_index(drop=True)
        self.predictions["salario_observado"] = self.y_test
        evaluation, fit_metrics = [], []
        for key in ORDER:
            model = make_model(key)
            model.fit(self.X_train, self.y_train)
            self.models[key] = model
            prediction = model.predict(self.X_test)
            self.predictions[f"previsto_{key}"] = prediction
            self.predictions[f"residuo_{key}"] = self.y_test - prediction
            evaluation.append({"modelo": key, **metricas(self.y_test, prediction)})
            fit_metrics.append({"modelo": key, **metricas(self.y_train, model.predict(self.X_train))})
        self.metrics = pd.DataFrame(evaluation)
        self.fit_metrics = pd.DataFrame(fit_metrics)
        baseline_mae = self.metrics.loc[self.metrics.modelo.eq("mediana"), "mae"].iloc[0]
        self.metrics["ganho_mae_vs_mediana_pct"] = 100 * (1 - self.metrics.mae / baseline_mae)
        self.predictions.to_parquet(self.local / "previsoes_marco.parquet", index=False)
        self.visual_limit = float(np.quantile(self.y_train, .99))
        model = self.models["multipla"]
        prep = model.named_steps["preparar"]
        names = prep.get_feature_names_out()
        self.coefficients = pd.DataFrame({"termo": names, "coeficiente_modelo": model.named_steps["modelo"].coef_})
        self.coefficients["escala"] = "categoria nominal ou indicador/numerica padronizada"
        self.coefficients.to_csv(self.outputs / "tabelas/coeficientes_modelo_multiplo.csv", index=False, encoding="utf-8-sig")
        audit = {"entradas": FEATURES, "alvo": "salario_real", "treino": ["202501", "202502"], "teste": ["202503"],
                 "validacao_interna": {"ajuste": "202501", "avaliacao": "202502", "criterio": "menor MAE; empate preserva modelo mais simples"},
                 "modelo_escolhido_antes_do_teste": self.selected, "alpha_ridge_fixo": 10.0,
                 "mediana_treino": float(np.median(self.y_train)), "p99_treino_limite_apenas_visual": self.visual_limit,
                 "coeficiente_idade_simples_reais_ano": float(self.models["idade"].named_steps["modelo"].coef_[0] / self.models["idade"].named_steps["preparar"].named_transformers_["numericas"].named_steps["escala"].scale_[0]),
                 "intercepto_multiplo": float(model.named_steps["modelo"].intercept_),
                 "medianas_imputacao_treino": prep.named_transformers_["numericas"].named_steps["imputar"].statistics_.tolist(),
                 "categorias_treino": {field: list(values) for field, values in zip(CATEGORICAL, prep.named_transformers_["categoricas"].named_steps["codificar"].categories_)},
                 "sha256_fonte": self.source_hash,
                 "previsoes_negativas": "mantidas e contadas; nenhuma correcao ou truncamento pos-teste"}
        self.audit = audit
        (self.outputs / "auditoria_modelagem.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
        best = self.metrics.set_index("modelo").loc[self.selected]
        note = (f"A validacao jan->fev escolheu **{MODEL_NAMES[self.selected]}**, antes do teste. Todos os modelos foram depois "
                f"reajustados em jan-fev. Em marco, o modelo escolhido tem MAE {money(best.mae)}, RMSE {money(best.rmse)} e "
                f"R2={best.r2:.3f}. A referencia constante usa apenas a mediana de jan-fev ({money(np.median(self.y_train))}). "
                "MAE foi definido para a escolha; a mediana minimiza erro absoluto, nao erro quadratico. "
                "A regressao simples usa idade; a multipla e linear com penalizacao Ridge fixa alpha=10, sem busca de hiperparametros. "
                "Março nao ajusta imputacao, escalas, categorias, coeficientes, alpha ou escolha de modelo. Previsoes negativas, se houver, nao sao recortadas.")
        return self.register("R1", {"validacao_fevereiro": self.validation, "ajuste_jan_fev": self.fit_metrics, "teste_marco": self.metrics}, [], note)

    def trend(self):
        valid = self.test.idade_valida.fillna(False).to_numpy()
        frame = self.test.loc[valid, ["idade", "salario_real"]].astype(float)
        sample = frame.sample(n=min(6000, len(frame)), random_state=12)
        ages = np.linspace(float(frame.idade.min()), float(frame.idade.max()), 150)
        synthetic = pd.DataFrame({"idade": ages})
        prediction = self.models["idade"].predict(synthetic)
        grouped = frame.groupby("idade").salario_real.agg(n="size", mediana="median").reset_index()
        visible = grouped.n.ge(MIN_N)
        fig, axes = self.figure(size=(11, 6.4))
        ax = axes[0, 0]
        ax.scatter(sample.idade, sample.salario_real, s=9, alpha=.14, color=self.theme.NEUTRO_GRAFICO, label="Marco: amostra visual fixa")
        ax.plot(ages, prediction, color=self.theme.LARANJA, linewidth=2.5, label="Reta ajustada em jan-fev")
        ax.plot(grouped.loc[visible, "idade"], grouped.loc[visible, "mediana"], color=self.theme.GRAFITE, linewidth=1.4, label="Marco: mediana por idade (n>=30)")
        ax.set(xlabel="Idade (anos; nao equivale a experiencia)", ylabel="Salario mensal real", ylim=(0, self.visual_limit))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        ax.legend(fontsize=9, loc="upper left")
        omitted = int((sample.salario_real > self.visual_limit).sum())
        slope = self.audit["coeficiente_idade_simples_reais_ano"]
        note = (f"A reta simples ajustada em jan-fev varia {money(slope)} por ano de idade. Isso e associacao marginal, nao efeito "
                "causal, experiencia profissional ou crescimento individual. A mediana por idade em marco nao e a reta OLS, "
                "que aproxima a media condicional sob especificacao linear. O teto do grafico e o p99 do salario do treino; "
                f"{omitted} dos {len(sample)} pontos da amostra visual ficam acima dele. Todos os registros entram nas metricas e nos residuos.")
        return self.register("R2", {"medianas_idade_marco": grouped}, [self.finish(fig, "R2_idade_tendencia", "Idade e salario: dispersao, reta de treino e medianas observadas", f"Teste: n={len(frame)}; amostra visual: n={len(sample)}; {omitted} pontos acima do teto visual p99 do treino.")], note)

    def predicted_observed(self):
        fig, axes = self.figure(cols=2, size=(13, 6.4))
        records = []
        for ax, key in zip(axes[0], ["idade", "multipla"]):
            predicted = self.predictions[f"previsto_{key}"].to_numpy()
            lower = min(0., float(predicted.min()))
            ax.hexbin(predicted, self.y_test, gridsize=45, extent=(lower, self.visual_limit, 0, self.visual_limit), mincnt=1, norm=LogNorm(), cmap="Greys")
            ax.plot([lower, self.visual_limit], [lower, self.visual_limit], color=self.theme.LARANJA, linestyle="--", label="Previsao = observado")
            outside = int(((predicted > self.visual_limit) | (self.y_test > self.visual_limit)).sum())
            records.append({"modelo": key, "n_total": len(predicted), "fora_janela_p99_treino": outside})
            ax.set(title=MODEL_NAMES[key], xlabel="Salario previsto", ylabel="Salario observado", xlim=(lower, self.visual_limit), ylim=(0, self.visual_limit))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
            ax.text(.03, .96, f"n={len(predicted):,}; fora da janela={outside:,}", transform=ax.transAxes, va="top", fontsize=9)
            ax.legend(loc="lower right", fontsize=8)
        note = ("A diagonal representa previsao exata. Concentracao sistematica acima da diagonal indica subestimacao. "
                "O grafico compara os dois regressores, sem escolher pelo teste; usa densidade em hexagonos e janela limitada pelo p99 do treino "
                "nos dois eixos. O numero fora da janela e informado por modelo, sem exclui-lo da avaliacao. "
                "A regressao linear pode comprimir a dispersao e errar salarios altos: ela nao fornece um intervalo salarial individual confiavel.")
        return self.register("R3", {"cobertura_visual": pd.DataFrame(records)}, [self.finish(fig, "R3_observado_previsto", "Teste de marco: salarios observados versus previstos", "Hexagonos indicam densidade local (escala log); diagonal tracejada = previsao exata; janela p99 do treino.")], note)

    def residuals(self):
        key = self.selected
        predicted = self.predictions[f"previsto_{key}"].to_numpy()
        residual = self.y_test - predicted
        fig, axes = self.figure(cols=2, size=(13, 6.4))
        ax, hist = axes[0]
        ax.hexbin(predicted, residual, gridsize=45, mincnt=1, norm=LogNorm(), cmap="Greys")
        ax.axhline(0, color=self.theme.LARANJA, linestyle="--", linewidth=2)
        ax.set(xlabel="Salario previsto", ylabel="Residuo = observado - previsto", title="Residuos: todos os eventos do teste")
        hist.hist(residual, bins=100, color=self.theme.NEUTRO_GRAFICO)
        hist.axvline(0, color=self.theme.LARANJA, linestyle="--", linewidth=2)
        hist.set(xlabel="Residuo mensal real (R$)", ylabel="Eventos", title="Distribuicao completa dos residuos")
        for axis in [ax, hist]:
            axis.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
        q = np.quantile(residual, [.1, .5, .9])
        summary = pd.DataFrame([{"modelo": key, "n": len(residual), "p10_residuo": q[0], "mediana_residuo": q[1], "p90_residuo": q[2], "media_residuo": residual.mean(), "minimo": residual.min(), "maximo": residual.max()}])
        note = (f"Para {MODEL_NAMES[key]}, o residuo observado-previsto tem mediana {money(q[1])}, p10 {money(q[0])} e p90 {money(q[2])}. "
                "Residuo positivo significa subestimacao; negativo, superestimacao. Ambos os paineis incluem a amplitude completa, sem corte de cauda. "
                "Assimetria, caudas e variacao da dispersao indicam limites da aproximacao linear; nao se presume normalidade, homocedasticidade "
                "ou independencia entre eventos. Nao foram calculados p-valores, intervalos de confianca ou de previsao.")
        return self.register("R4", {"residuos_marco": summary}, [self.finish(fig, "R4_residuos", f"Diagnostico de residuos: {MODEL_NAMES[key]}", f"Modelo definido na validacao de fevereiro; teste de marco: n={len(residual)}. Amplitude completa.")], note)

    def performance(self):
        fig, axes = self.figure(cols=2, size=(12, 6.1))
        for ax, field, label in zip(axes[0], ["mae", "rmse"], ["Erro absoluto medio (MAE)", "Raiz do erro quadratico medio (RMSE)"]):
            for i, key in enumerate(ORDER):
                value = self.metrics.set_index("modelo").loc[key, field]
                ax.barh(i, value, color=self.colors[i])
                ax.text(value, i, " " + money(value), va="center", fontsize=9)
            ax.set_yticks(range(3), [MODEL_NAMES[k] for k in ORDER])
            ax.set(title=label, xlabel="R$ por mes; menor e melhor")
            ax.set_xlim(0, self.metrics[field].max() * 1.32)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
            ax.grid(axis="x", alpha=.5)
            ax.set_axisbelow(True)
        base = self.metrics.set_index("modelo").loc["mediana"]
        chosen = self.metrics.set_index("modelo").loc[self.selected]
        gains = chosen.ganho_mae_vs_mediana_pct
        negatives = int(chosen.previsoes_negativas)
        note = (f"No teste, a mediana do treino tem MAE {money(base.mae)}; o modelo previamente escolhido tem MAE {money(chosen.mae)}, "
                f"variacao de {gains:.1f}% em relacao a referencia (positivo = reducao). Seu RMSE e {money(chosen.rmse)}, "
                f"metrica mais sensivel a erros extremos. Foram geradas {negatives} previsoes negativas "
                f"({100*negatives/len(self.test):.1f}% do teste), valores sem sentido salarial, mantidos para expor o limite da forma linear. "
                "Isso impede tratar a melhoria global como validacao de uma calculadora salarial individual; nenhum valor foi corrigido apos olhar o teste. "
                "A tabela inclui R2 e erro absoluto mediano. Desempenho em um unico mes nao demonstra generalizacao para 2026 ou outros mercados. "
                "Nao houve reescolha de modelo a partir deste grafico.")
        return self.register("R5", {"comparacao_teste": self.metrics.copy()}, [self.finish(fig, "R5_comparacao_modelos", "Marco reservado: comparacao dos modelos e da referencia", f"Mesmo conjunto de {len(self.test)} eventos para os tres modelos; referencia ajustada somente em jan-fev.")], note)

    def subgroups(self):
        records = []
        groups = [("recorte", "Brasil", np.ones(len(self.test), dtype=bool)),
                  ("recorte", "Nordeste", self.predictions.uf_sigla.isin(NE).to_numpy()),
                  ("recorte", "Pernambuco", self.predictions.uf_sigla.eq("PE").to_numpy())]
        for field in ["uf_sigla", "area_ti"]:
            groups += [(field, str(value), self.predictions[field].eq(value).to_numpy()) for value in sorted(self.predictions[field].dropna().unique())]
        for dimension, group, mask in groups:
            for key in ORDER:
                row = {"dimensao": dimension, "grupo": group, "modelo": key, "n": int(mask.sum()), "suficiente": bool(mask.sum() >= MIN_N)}
                if mask.sum() >= MIN_N:
                    row.update(metricas(self.y_test[mask], self.predictions.loc[mask, f"previsto_{key}"]))
                records.append(row)
        table = pd.DataFrame(records)
        fig, axes = self.figure(size=(11.5, 6.1))
        ax = axes[0, 0]
        for index, key in enumerate(ORDER):
            rows = table[table.dimensao.eq("recorte") & table.modelo.eq(key)]
            ax.barh(np.arange(3) + (index-1)*.23, rows.mae, height=.21, color=self.colors[index], label=MODEL_NAMES[key])
        regions = table[table.dimensao.eq("recorte") & table.modelo.eq("mediana")]
        ax.set_yticks(range(3), [f"{r.grupo} (n={r.n:,})" for r in regions.itertuples()])
        ax.set_xlabel("MAE mensal real (R$); menor e melhor")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        ax.set_xlim(0, table.loc[table.dimensao.eq("recorte"), "mae"].max()*1.12)
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, fontsize=9, loc="upper right", bbox_to_anchor=(.98, .89), ncol=3)
        pe = table[table.dimensao.eq("recorte") & table.grupo.eq("Pernambuco") & table.modelo.eq(self.selected)].iloc[0]
        suppressed = table[~table.suficiente][["dimensao", "grupo"]].drop_duplicates()
        note = (f"Em Pernambuco, o modelo escolhido tem MAE {money(pe.mae)} em {int(pe.n)} admissoes de marco. "
                f"Ha {len(suppressed)} recortes UF/area com n<30 e metricas suprimidas (o n permanece). "
                "A referencia usada por regiao continua sendo a mediana global do treino, nao uma mediana local recalculada no teste. "
                "Brasil, Nordeste e PE sao recortes aninhados e nao devem ser somados. Diferencas refletem composicao de cargos e salarios; "
                "nao constituem auditoria de equidade nem avaliacao individual. Tabelas completas por UF e area acompanham o notebook.")
        return self.register("R6", {"metricas_recortes": table}, [self.finish(fig, "R6_erros_regionais", "Erros por regiao no mesmo teste temporal", "Recortes aninhados: nao somar. Metricas de UF/area divulgadas apenas com n>=30.")], note)

    def calibration(self):
        prediction = self.predictions[f"previsto_{self.selected}"].to_numpy()
        frame = pd.DataFrame({"previsto": prediction, "observado": self.y_test})
        frame["faixa_previsao"] = pd.qcut(frame.previsto, 10, duplicates="drop") if frame.previsto.nunique() > 1 else "Previsao constante"
        table = frame.groupby("faixa_previsao", observed=True).agg(n=("observado", "size"), previsto_medio=("previsto", "mean"), observado_medio=("observado", "mean"), observado_p10=("observado", lambda x: x.quantile(.1)), observado_p90=("observado", lambda x: x.quantile(.9))).reset_index()
        table["faixa_previsao"] = table.faixa_previsao.astype(str)
        table["residuo_medio"] = table.observado_medio - table.previsto_medio
        fig, axes = self.figure(size=(10.5, 6.3))
        ax = axes[0, 0]
        upper = max(table.previsto_medio.max(), table.observado_p90.max()) * 1.08
        ax.plot([0, upper], [0, upper], color=self.theme.NEUTRO_GRAFICO, linestyle="--", label="Medias iguais")
        ax.vlines(table.previsto_medio, table.observado_p10, table.observado_p90, color=self.theme.FAIXA_PREENCHIMENTO, linewidth=6, label="Observado: p10-p90")
        ax.plot(table.previsto_medio, table.observado_medio, color=self.theme.LARANJA, marker="o", label="Media observada por faixa")
        ax.set(xlabel="Media prevista por faixa de previsao", ylabel="Salario observado (R$)", xlim=(0, upper), ylim=(0, upper))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f} mil"))
        ax.legend(loc="upper left", fontsize=9)
        note = ("As faixas usam os quantis das previsoes de marco apenas para diagnostico, sem novo ajuste ou calibracao. "
                "A curva aproxima medias previstas e observadas; as faixas verticais sao p10-p90 dos salarios observados, "
                "nao intervalos de confianca/previsao. Distancia da diagonal revela erro medio sistematico; a largura da faixa "
                "mostra variacao de salarios entre eventos com previsoes semelhantes. Nao se recomenda esse modelo como calculadora salarial pessoal.")
        return self.register("R7", {"calibracao_descritiva": table}, [self.finish(fig, "R7_calibracao_descritiva", "Calibracao descritiva e dispersao que o modelo nao explica", f"Modelo escolhido: {MODEL_NAMES[self.selected]}; faixas definidas pelas previsoes do teste; n por faixa na tabela.")], note)

    def sensitivity(self):
        cutoff = self.visual_limit
        records = []
        for label, mask in [("Todos (avaliacao principal)", np.ones(len(self.y_test), dtype=bool)),
                            ("Salario <= p99 do treino", self.y_test <= cutoff),
                            ("Salario > p99 do treino", self.y_test > cutoff)]:
            for key in ORDER:
                records.append({"recorte": label, "modelo": key, **metricas(self.y_test[mask], self.predictions.loc[mask, f"previsto_{key}"])})
        table = pd.DataFrame(records)
        model = self.models["multipla"]
        encoder = model.named_steps["preparar"].named_transformers_["categoricas"].named_steps["codificar"]
        unknown = pd.DataFrame([{"variavel": field, "n_categoria_nao_vista_treino": int((~self.X_test[field].isin(categories)).sum()), "n_teste": len(self.test)} for field, categories in zip(CATEGORICAL, encoder.categories_)])
        tail = table[table.recorte.eq("Salario > p99 do treino") & table.modelo.eq(self.selected)].iloc[0]
        core = table[table.recorte.eq("Salario <= p99 do treino") & table.modelo.eq(self.selected)].iloc[0]
        note = (f"O limiar p99 foi fixado no treino ({money(cutoff)}). Na cauda acima dele ha {int(tail.n)} eventos, com MAE "
                f"{money(tail.mae)}, contra {money(core.mae)} abaixo/igual ao limiar. Esta e uma analise de sensibilidade por salario "
                "observado, nao um filtro de producao: o alvo futuro nao estaria disponivel para decidir a faixa. "
                "A avaliacao principal mantem todos os salarios validos e nao usa winsorizacao ou remocao de outliers baseada em marco. "
                "Categorias novas sao codificadas com zeros pelo encoder; a tabela informa sua cobertura. "
                "Os coeficientes sao descritivos: numericas estao padronizadas e categorias usam one-hot completo com Ridge, "
                "sem categoria-base omitida. Nao sao retornos causais da escolaridade, premios salariais individuais ou medidas de significancia.")
        return self.register("R8", {"sensibilidade_cauda": table, "categorias_novas_teste": unknown}, [], note)

    def run(self, key):
        return {"R0": self.scope, "R1": self.fit, "R2": self.trend, "R3": self.predicted_observed,
                "R4": self.residuals, "R5": self.performance, "R6": self.subgroups,
                "R7": self.calibration, "R8": self.sensitivity}[key]()

    def summary(self):
        parts = ["# Sintese da regressao salarial", "Etapa 04. Radar de Carreira em TI. Execucao com CAGED MOV de jan-mar/2025.",
                 "Somente fontes publicas; sem State of Data ou pesquisa G12. Valores mensais a precos de marco/2025."]
        for key, result in self.results.items():
            parts += [f"## {key}", result["interpretacao"]]
        parts += ["## Limites e proximo passo", "Estudo observacional de movimentacoes, nao pessoas ou vinculos. Apenas um mes reservado para teste; "
                  "nao permite previsao de longo prazo ou inferencia causal. Nao identifica senioridade, habilidades, tempo de vinculo ou "
                  "evolucao individual. A exposicao da fonte e real de mar/2025 (IPCA comum), nao informacao de salario atual de 2026. "
                  "Sexo e raca/cor nao entram; isso nao elimina vieses ou proxies. A etapa 05 continua pendente e usa outra fonte/alvo."]
        (self.area / "sintese_achados.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")

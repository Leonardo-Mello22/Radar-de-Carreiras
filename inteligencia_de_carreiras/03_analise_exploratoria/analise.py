"""Exploratory analysis with distinct sources, explicit universes and denominators."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler


MIN_N = 30
ACTIVE = {
    "Estou em busca de oportunidades dentro ou fora do Brasil": True,
    "Estou em busca de oportunidades, mas apenas fora do Brasil": True,
    "Não estou buscando, mas me considero aberto a outras oportunidades": False,
    "Não estou buscando e não pretendo mudar de emprego nos próximos 6 meses": False,
}


def money(value):
    return "R$ " + f"{value:,.0f}".replace(",", ".")


def percent(value):
    return f"{100 * value:.1f}%".replace(".", ",")


def format_count(value):
    return f"{int(value):,}".replace(",", ".")


def salary_summary(frame, keys, minimum=MIN_N):
    result = frame.groupby(keys, dropna=False, observed=True).salario_real.agg(
        n="size", p10=lambda x: x.quantile(.1), p50="median", p90=lambda x: x.quantile(.9)).reset_index()
    result["suficiente"] = result.n.ge(minimum)
    result.loc[~result.suficiente, ["p10", "p50", "p90"]] = np.nan
    return result


def frequencies(series):
    valid = series.dropna()
    counts = valid.astype(str).value_counts()
    return pd.DataFrame({"categoria": counts.index, "n": counts.values,
                         "denominador": len(valid), "proporcao": counts.values / len(valid) if len(valid) else np.nan,
                         "ausentes": int(series.isna().sum())})


def active_target(series):
    unknown = series.notna() & ~series.isin(ACTIVE)
    if unknown.any():
        raise ValueError("Unexpected job-search answer; review mapping before analysis.")
    return series.map(ACTIVE).astype("boolean")


def technology_rates(frame, groups=None):
    options = {"usa_sql": "SQL", "usa_python": "Python", "usa_r": "R", "usa_power_bi": "Power BI",
               "usa_aws": "AWS", "usa_gcp": "GCP", "usa_azure": "Azure"}
    records = []
    cohorts = [("Brasil", frame)] if groups is None else frame.groupby(groups, dropna=False, observed=True)
    for group, data in cohorts:
        for field, label in options.items():
            values = data[field]
            denominator, yes = int(values.notna().sum()), int(values.eq(True).sum())
            records.append({"grupo": str(group), "tecnologia": label, "n_elegiveis_no_recorte": len(data),
                            "n_respondidos": denominator, "n_usa": yes, "ausentes": int(values.isna().sum()),
                            "proporcao": yes / denominator if denominator >= MIN_N else np.nan})
    return pd.DataFrame(records)


def correlation_pair(frame, x, y, minimum=MIN_N):
    values = frame[[x, y]].dropna().astype(float)
    if len(values) < minimum or values[x].nunique() < 2 or values[y].nunique() < 2:
        return len(values), np.nan
    return len(values), float(spearmanr(values[x], values[y]).statistic)


class Exploracao:
    def __init__(self, area):
        self.area = Path(area).resolve()
        self.data = self.area.parent / "datasets"
        self.public = self.area / "resultados_fontes_publicas"
        self.local = self.area / "resultados_locais"
        spec = importlib.util.spec_from_file_location("radar_theme", self.area.parents[1] / "app/theme.py")
        self.theme = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.theme)
        plt.rcParams.update({"font.family": ["DejaVu Sans"], "font.size": 10,
                             "axes.spines.top": False, "axes.spines.right": False,
                             "axes.labelcolor": self.theme.TEXTO, "text.color": self.theme.TEXTO,
                             "axes.edgecolor": self.theme.BORDA_CLARA, "grid.color": self.theme.TRILHO_GRAFICO})
        self.sources = {}
        prepared = json.loads((self.data / "qualidade/execucao_preparacao.json").read_text(encoding="utf-8"))
        hashes = {item["arquivo"]: item["sha256"] for item in prepared["produtos"]}
        for name, stem in [("caged", "caged_ti"), ("sod", "state_of_data_brasil"),
                           ("g12", "pesquisa_grupo12_respostas"), ("priorities", "pesquisa_grupo12_prioridades")]:
            relative = f"tratados/{stem}.parquet"
            path = self.data / relative
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != hashes[relative]:
                raise ValueError(f"Prepared source changed: {stem}. Revalidate stage 02 first.")
            self.sources[stem] = {"sha256": digest, "linhas": len(pd.read_parquet(path))}
            setattr(self, name, pd.read_parquet(path))
        self.admissions = self.caged[self.caged.movimento.eq("admissão") & self.caged.salario_valido].copy()
        self.results = {}

    def region_frames(self, frame):
        northeast = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
        return {"Brasil": frame, "Nordeste": frame[frame.uf_sigla.isin(northeast)],
                "Pernambuco": frame[frame.uf_sigla.eq("PE")]}

    def figure(self, rows=1, cols=1, figsize=None):
        return plt.subplots(rows, cols, figsize=figsize or (10.5, 6), squeeze=False)

    def finish(self, fig, key, title, source="CAGED", private=False, note=""):
        fig.suptitle(textwrap.fill(title, 92), fontsize=14, fontweight="bold", x=.02, y=.98, ha="left")
        captions = {"CAGED": "Novo CAGED MOV; jan-mar/2025; salário real a preços de mar/2025.",
                    "SOD": "State of Data Brazil 2024-2025; residentes no Brasil; pesquisa autodeclarada.",
                    "G12": "Pesquisa G12; 31/08 a 04/09/2026; uso local restrito; n total=35."}
        fig.tight_layout(rect=(0, .10, 1, .90), pad=1.8)
        fig.text(.02, .025, textwrap.fill(captions[source] + " " + note, 145), fontsize=8, color=self.theme.TEXTO_SECUNDARIO)
        folder = (self.local / "pesquisa_grupo12" if private else self.public) / "graficos"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{key}.png"
        fig.savefig(path, dpi=145, facecolor=self.theme.BRANCO)
        plt.close(fig)
        return path

    def bars(self, frame, category, value, label=None, percent_axis=False):
        fig, axes = self.figure(figsize=(11, max(5, len(frame) * .40 + 2.4)))
        ax = axes[0, 0]
        ordered = frame.sort_values(value, ascending=True)
        ax.barh(range(len(ordered)), ordered[value], color=self.theme.LARANJA)
        ax.set_yticks(range(len(ordered)), [textwrap.fill(str(x), 39) for x in ordered[category]])
        ax.set_xlabel(label or value)
        ax.grid(axis="x", alpha=.65)
        ax.set_axisbelow(True)
        if percent_axis:
            ax.set_xlim(0, 1)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: percent(x)))
        for i, row in enumerate(ordered.itertuples(index=False, name=None)):
            v = ordered.iloc[i][value]
            ax.text(v, i, " " + (percent(v) if percent_axis else f"{v:,.0f}".replace(",", ".")), va="center", fontsize=9)
        if not percent_axis:
            ax.set_xlim(0, max(ordered[value]) * 1.17 if len(ordered) else 1)
        return fig

    def register(self, key, frames, figures, interpretation, private=False):
        root = self.local / "pesquisa_grupo12" if private else self.public
        tables = root / "tabelas"
        tables.mkdir(parents=True, exist_ok=True)
        for name, frame in frames.items():
            frame.to_csv(tables / f"{key}_{name}.csv", index=False, encoding="utf-8-sig")
        result = {"tabelas": frames, "graficos": figures, "interpretacao": interpretation, "restrito": private}
        self.results[key] = result
        return result

    def p1(self):
        summaries = []
        by_area = []
        for region, frame in self.region_frames(self.admissions).items():
            q = frame.salario_real.astype(float).quantile([.1, .5, .9])
            summaries.append({"regiao": region, "n": len(frame), "p10": q[.1], "p50": q[.5], "p90": q[.9]})
            grouped = salary_summary(frame, ["area_ti"])
            grouped["regiao"] = region
            by_area.append(grouped)
        overall = pd.DataFrame(summaries)
        areas = pd.concat(by_area, ignore_index=True)
        fig, axes = self.figure(figsize=(10.5, 5))
        ax = axes[0, 0]
        for i, row in overall.iterrows():
            ax.plot([row.p10, row.p90], [i, i], linewidth=7, color=self.theme.FAIXA_PREENCHIMENTO)
            ax.scatter(row.p50, i, color=self.theme.GRAFITE, s=65, zorder=3)
        ax.set_yticks(range(len(overall)), [f"{r.regiao} (n={r.n:,})".replace(",", ".") for r in overall.itertuples()])
        ax.set_xlabel("Salário de admissão mensal: p10-p90 e mediana (R$)")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        ax.set_xlim(0, overall.p90.max() * 1.12)
        ax.grid(axis="x", alpha=.6)
        pe = overall[overall.regiao.eq("Pernambuco")].iloc[0]
        br = overall[overall.regiao.eq("Brasil")].iloc[0]
        text = (f"Entre {format_count(len(self.admissions))} admissões com salário válido, a mediana de Pernambuco é {money(pe.p50)}, "
                f"contra {money(br.p50)} no Brasil; a faixa p10-p90 de PE vai de {money(pe.p10)} a {money(pe.p90)}. "
                "Esses recortes são aninhados, não amostras independentes. A diferença agregada também reflete composição de cargos; "
                "não estima salário júnior nem efeito causal da região. A tabela por área só divulga quantis com n>=30.")
        return self.register("P1", {"regioes": overall, "areas": areas},
                             [self.finish(fig, "P1_salarios_regioes", "P1 - Salários de admissão nos recortes disponíveis", note="Quantis não são extremos ou intervalo de confiança.")], text)

    def p2(self):
        records = []
        for region, frame in self.region_frames(self.caged).items():
            for month, data in frame.groupby("competencia", sort=True):
                admission, dismissal = int(data.saldo.eq(1).sum()), int(data.saldo.eq(-1).sum())
                records.append({"regiao": region, "competencia": month, "admissoes": admission,
                                "desligamentos": dismissal, "diferenca_mov": admission - dismissal})
        table = pd.DataFrame(records)
        fig, axes = self.figure(cols=3, figsize=(12, 5.6))
        for i, region in enumerate(["Brasil", "Nordeste", "Pernambuco"]):
            data = table[table.regiao.eq(region)]
            ax = axes[0, i]
            x = np.arange(len(data))
            ax.bar(x - .18, data.admissoes, .36, color=self.theme.LARANJA, label="Admissões")
            ax.bar(x + .18, data.desligamentos, .36, color=self.theme.NEUTRO_GRAFICO, label="Desligamentos")
            ax.set_xticks(x, ["Jan", "Fev", "Mar"])
            ax.set_title(region, fontsize=11)
            ax.set_ylabel("Movimentações")
            ax.grid(axis="y", alpha=.4)
            ax.set_axisbelow(True)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(.98, .94), ncol=2, fontsize=9, frameon=False)
        totals = table.groupby("regiao")[["admissoes", "desligamentos", "diferenca_mov"]].sum().reset_index()
        br = totals[totals.regiao.eq("Brasil")].iloc[0]
        pe = totals[totals.regiao.eq("Pernambuco")].iloc[0]
        text = (f"No Brasil, os arquivos MOV somam {format_count(br.admissoes)} admissões e {format_count(br.desligamentos)} desligamentos, "
                f"diferença de {format_count(br.diferenca_mov)}. Em PE, a diferença MOV é {format_count(pe.diferenca_mov)}. "
                "Salários sinalizados continuam nessas contagens. Não há ajustes FOR/EXC, portanto não chamar essa diferença de saldo oficial final. "
                "Três meses não permitem concluir sazonalidade ou tendência anual; os painéis usam escalas próprias.")
        return self.register("P2", {"mensal": table, "totais": totals},
                             [self.finish(fig, "P2_movimentacoes_mensais", "P2 - Admissões e desligamentos por mês", note="Escalas verticais distintas por região; recortes aninhados.")], text)

    def p3(self):
        valid = self.caged[self.caged.salario_valido]
        groups = salary_summary(valid, ["uf_sigla", "cbo_codigo", "cbo_nome", "competencia", "movimento"])
        admissions = groups[groups.movimento.eq("admissão")].drop(columns="movimento")
        dismissals = groups[groups.movimento.eq("desligamento")].drop(columns="movimento")
        matched = admissions.merge(dismissals, on=["uf_sigla", "cbo_codigo", "cbo_nome", "competencia"], suffixes=("_admissao", "_desligamento"), validate="one_to_one")
        matched = matched[matched.suficiente_admissao & matched.suficiente_desligamento].copy()
        matched["diferenca_mediana"] = matched.p50_admissao - matched.p50_desligamento
        pe = matched[matched.uf_sigla.eq("PE")].copy()
        chart = pe.assign(n_total=pe.n_admissao + pe.n_desligamento).nlargest(8, "n_total").sort_values("diferenca_mediana")
        fig, axes = self.figure(figsize=(12, 7))
        ax = axes[0, 0]
        for i, row in enumerate(chart.itertuples()):
            ax.plot([row.p10_admissao, row.p90_admissao], [i - .12] * 2, color=self.theme.LARANJA, alpha=.55, linewidth=3)
            ax.plot([row.p10_desligamento, row.p90_desligamento], [i + .12] * 2, color=self.theme.NEUTRO_GRAFICO, linewidth=3)
            ax.scatter(row.p50_admissao, i - .12, color=self.theme.LARANJA, label="Admissão" if i == 0 else None)
            ax.scatter(row.p50_desligamento, i + .12, color=self.theme.GRAFITE, marker="s", label="Desligamento" if i == 0 else None)
        ax.set_yticks(range(len(chart)), [textwrap.fill(r.cbo_nome, 39) + f"\n{r.competencia}" for r in chart.itertuples()])
        ax.set_xlabel("Salário mensal real (R$); p10-p90 e mediana")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        ax.set_xlim(left=0)
        ax.legend(fontsize=9)
        text = (f"Foram encontrados {len(matched)} pares UF/CBO/mês com pelo menos 30 salários válidos em cada movimento; "
                f"{len(pe)} estão em PE. Entre os pares de PE, {int(pe.diferenca_mediana.gt(0).sum())} apresentam mediana de admissão maior "
                f"e {int(pe.diferenca_mediana.lt(0).sum())} menor que a de desligamento. O gráfico mostra os oito pares de maior cobertura. "
                "Mesmo com cargo, UF e mês equivalentes, são pessoas diferentes: a diferença não mede aumento salarial, promoção ou trajetória individual.")
        return self.register("P3", {"pares_comparaveis": matched, "pernambuco": pe, "pares_exibidos": chart},
                             [self.finish(fig, "P3_pares_salariais_pe", "P3 - Grupos comparáveis em Pernambuco", note="Mesma UF, CBO e competência; n>=30 em ambos os movimentos.")], text)

    def p4(self):
        frame = self.admissions.copy()
        school_order = ["Sem instrucao", "Fundamental incompleto", "Fundamental completo", "Medio incompleto", "Medio completo", "Superior incompleto", "Superior completo", "Pos-graduacao", "Mestrado", "Doutorado"]
        school = salary_summary(frame, ["escolaridade_grupo"])
        categories = [x for x in school_order if x in set(school.loc[school.suficiente, "escolaridade_grupo"])]
        fig, axes = self.figure(figsize=(12, 6.5))
        ax = axes[0, 0]
        values = [frame.loc[frame.escolaridade_grupo.eq(x), "salario_real"].astype(float).to_numpy() for x in categories]
        ax.boxplot(values, orientation="horizontal", tick_labels=[textwrap.fill(x, 22) for x in categories],
                   showfliers=False, whis=(10, 90), medianprops={"color": self.theme.LARANJA, "linewidth": 2})
        ax.set_xlabel("Salário mensal real (R$); caixa Q1-Q3, mediana e hastes p10-p90")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        plots = [self.finish(fig, "P4_escolaridade", "P4 - Distribuição salarial por escolaridade", note="Apenas admissões válidas e grupos n>=30. Extremos não exibidos; não há ajuste por cargo neste gráfico.")]
        analytic = frame[["salario_real", "idade", "horas_contratuais"]].copy()
        analytic.loc[~frame.idade_valida, "idade"] = pd.NA
        analytic.loc[~frame.horas_validas, "horas_contratuais"] = pd.NA
        corr = []
        for x in ("idade", "horas_contratuais"):
            n, rho = correlation_pair(analytic, x, "salario_real")
            corr.append({"variavel": x, "n_pares": n, "rho_spearman": rho})
        correlation = pd.DataFrame(corr)
        conditional = []
        for keys, group in frame[frame.idade_valida].groupby(["cbo_codigo", "uf_sigla"], observed=True):
            n, rho = correlation_pair(group, "idade", "salario_real", minimum=100)
            if np.isfinite(rho):
                conditional.append({"cbo_codigo": keys[0], "uf_sigla": keys[1], "n_pares": n, "rho_idade_salario": rho})
        conditional = pd.DataFrame(conditional)
        fig, axes = self.figure(figsize=(9, 6))
        pair = analytic[["idade", "salario_real"]].dropna().astype(float)
        hexplot = axes[0, 0].hexbin(pair.idade, np.log10(pair.salario_real), gridsize=30, mincnt=30, bins="log", cmap="viridis")
        axes[0, 0].set_xlabel("Idade declarada (anos)")
        axes[0, 0].set_ylabel("Salário real mensal: log10(R$)")
        fig.colorbar(hexplot, ax=axes[0, 0], label="Movimentações por célula (escala log)")
        plots.append(self.finish(fig, "P4_densidade_idade_salario", "P4 - Densidade de idade e salário nas admissões", note="Células com menos de 30 registros omitidas apenas da visualização; todos os pares válidos entram na correlação."))
        age_rho = correlation.iloc[0].rho_spearman
        hours_rho = correlation.iloc[1].rho_spearman
        text = (f"A correlação de Spearman entre idade e salário é {age_rho:.3f}, com {format_count(correlation.iloc[0].n_pares)} pares; "
                f"para jornada é {hours_rho:.3f}. Em {len(conditional)} grupos CBO/UF com n>=100 e variação, a mediana do rho idade-salário "
                f"é {conditional.rho_idade_salario.median():.3f}. A análise dentro desses recortes reduz parte da mistura de cargos/regiões, "
                "mas não controla todos os fatores. Diferenças por escolaridade e idade não demonstram retorno causal da formação nem senioridade.")
        return self.register("P4", {"escolaridade": school, "correlacoes": correlation, "correlacoes_cbo_uf": conditional}, plots, text)

    def multivariate(self):
        frame = self.admissions.copy()
        higher = {"Superior completo", "Pos-graduacao", "Mestrado", "Doutorado"}
        profiles = []
        for keys, data in frame.groupby(["uf_sigla", "area_ti"], observed=True):
            hours = data.loc[data.horas_validas, "horas_contratuais"].dropna().astype(float)
            school = data.loc[data.escolaridade_grupo.ne("Nao informado"), "escolaridade_grupo"]
            if len(data) < 100 or len(hours) < 100 or len(school) < 100:
                continue
            profiles.append({"uf_sigla": keys[0], "area_ti": keys[1], "n_salarios": len(data),
                             "salario_p50": float(data.salario_real.median()), "proporcao_superior": float(school.isin(higher).mean()),
                             "media_horas": float(hours.mean()), "n_horas": len(hours), "n_escolaridade": len(school)})
        profiles = pd.DataFrame(profiles)
        features = profiles[["salario_p50", "proporcao_superior", "media_horas"]].copy()
        features["salario_p50"] = np.log(features.salario_p50)
        scaled = StandardScaler().fit_transform(features)
        candidates = []
        for k in range(2, min(5, len(profiles) - 1) + 1):
            labels = KMeans(n_clusters=k, random_state=12, n_init=20).fit_predict(scaled)
            candidates.append({"k": k, "silhouette": float(silhouette_score(scaled, labels))})
        scores = pd.DataFrame(candidates)
        k = int(scores.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0].k)
        model = KMeans(n_clusters=k, random_state=12, n_init=20).fit(scaled)
        labels2 = KMeans(n_clusters=k, random_state=13, n_init=20).fit_predict(scaled)
        stability = float(adjusted_rand_score(model.labels_, labels2))
        profiles["grupo"] = model.labels_ + 1
        centers = profiles.groupby("grupo").agg(perfis=("uf_sigla", "size"), movimentos=("n_salarios", "sum"),
                                                mediana_das_medianas_salariais=("salario_p50", "median"),
                                                media_proporcao_superior=("proporcao_superior", "mean"), media_horas=("media_horas", "mean")).reset_index()
        fig, axes = self.figure(figsize=(10, 6))
        ax = axes[0, 0]
        palette = plt.colormaps["tab10"]
        for group, data in profiles.groupby("grupo"):
            ax.scatter(data.salario_p50, data.proporcao_superior, color=palette(int(group) - 1), s=42, alpha=.75, label=f"Grupo {group} (perfis={len(data)})")
        ax.set_xscale("log")
        ax.set_xlabel("Mediana salarial de cada perfil UF/área (R$; eixo log)")
        ax.set_ylabel("Proporção com superior completo ou pós-graduação")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: percent(x)))
        ax.legend(fontsize=9)
        ax.grid(alpha=.3)
        covered = int(profiles.n_salarios.sum())
        text = (f"O agrupamento considera {len(profiles)} perfis UF/área, cobrindo {format_count(covered)} de {format_count(len(frame))} admissões válidas "
                f"({percent(covered / len(frame))}). Cada perfil tem ao menos 100 salários, 100 jornadas e 100 escolaridades informadas. "
                "As três dimensões são log da mediana salarial, proporção de formação superior e média de jornada, padronizadas por z-score. "
                f"Entre k=2 a 5, k={k} maximiza silhouette ({scores.silhouette.max():.3f}); a concordância entre sementes 12/13 é ARI={stability:.3f}. "
                "Cada perfil tem o mesmo peso no ajuste, não cada pessoa. Grupos são descritivos e seus números arbitrários; "
                "não são classes de trabalhadores, previsão, ranking de regiões ou evidência causal. A escolha está limitada à faixa de k explorada "
                "e não valida a existência de cinco grupos naturais. A projeção exibe apenas duas das três dimensões.")
        return self.register("M1", {"perfis": profiles, "silhouette": scores, "resumo_grupos": centers,
                                    "estabilidade": pd.DataFrame({"k": [k], "ari_sementes": [stability], "n_perfis": [len(profiles)]})},
                             [self.finish(fig, "M1_perfis_multivariados", "M1 - Agrupamento exploratório de perfis UF/área", note="KMeans sobre agregados; z-score das três dimensões; semente 12; não representa trajetória individual.")], text)

    def p5(self):
        masks = {"Junior declarado": self.sod.senioridade_declarada.eq("Junior").fillna(False),
                 "Estagio declarado": self.sod.vinculo_grupo.eq("Estagio").fillna(False),
                 "Ate 2 anos em dados": self.sod.inicio_carreira_dados_ate_2_anos.eq(True).fillna(False)}
        records, coverage = [], []
        for cohort, mask in masks.items():
            data = self.sod[mask]
            for field in ["escolaridade_grupo", "vinculo_grupo", "modelo_trabalho"]:
                valid = data[field].notna() & data[field].ne("Nao informado")
                for category, count in data.loc[valid, field].value_counts().items():
                    records.append({"coorte": cohort, "variavel": field, "categoria": category, "n": int(count),
                                    "denominador": int(valid.sum()), "proporcao": count / valid.sum()})
                coverage.append({"coorte": cohort, "variavel": field, "n_total": len(data), "respondidos": int(valid.sum()), "ausentes_ou_nao_informados": int((~valid).sum())})
        table, counts = pd.DataFrame(records), pd.DataFrame(coverage)
        education = table[table.variavel.eq("escolaridade_grupo")].pivot(index="coorte", columns="categoria", values="proporcao").fillna(0)
        fig, axes = self.figure(figsize=(12, 6))
        ax = axes[0, 0]
        left = np.zeros(len(education))
        for i, column in enumerate(education):
            ax.barh(education.index, education[column], left=left, label=column, color=plt.colormaps["tab10"](i))
            left += education[column].to_numpy()
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: percent(x)))
        ax.set_xlabel("Composição da formação entre respostas informadas")
        ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
        text = (f"Os recortes têm {int(masks['Junior declarado'].sum())} júniores declarados, {int(masks['Estagio declarado'].sum())} estagiários "
                f"e {int(masks['Ate 2 anos em dados'].sum())} participantes com até dois anos em dados. "
                "Há sobreposição: estágio, nível declarado e experiência em dados não são coortes mutuamente exclusivas nem equivalentes. "
                "As composições de formação, vínculo e trabalho usam denominador próprio de resposta informada, com cobertura registrada nas tabelas.")
        return self.register("P5", {"perfis": table, "cobertura": counts},
                             [self.finish(fig, "P5_coortes_formacao", "P5 - Formação em três recortes distintos de início em dados", source="SOD", note="Coortes se sobrepõem; não somar seus totais.")], text)

    def p6(self):
        answered = self.sod[self.sod.faixa_salarial_declarada.notna()]
        bounds = answered[["faixa_salarial_declarada", "faixa_salario_limite_inferior"]].drop_duplicates().sort_values("faixa_salario_limite_inferior")
        order = bounds.faixa_salarial_declarada.tolist()
        labels = ["< 1 mil", "1-2 mil", "2-3 mil", "3-4 mil", "4-6 mil", "6-8 mil", "8-12 mil", "12-16 mil", "16-20 mil", "20-25 mil", "25-30 mil", "30-40 mil", "> 40.001"]
        tables, plots = {}, []
        for field, name in [("senioridade_declarada", "senioridade"), ("modelo_trabalho", "trabalho"), ("cargo_atual", "cargo")]:
            valid = answered[field].notna() & answered[field].ne("Nao informado")
            universe = answered[valid]
            count = pd.crosstab(universe[field], universe.faixa_salarial_declarada).reindex(columns=order, fill_value=0)
            count = count[count.sum(axis=1).ge(MIN_N)]
            if field == "cargo_atual":
                count = count.loc[count.sum(axis=1).nlargest(6).index]
            proportions = count.div(count.sum(axis=1), axis=0)
            flat = proportions.rename_axis("grupo").reset_index().melt(id_vars="grupo", var_name="faixa_declarada", value_name="proporcao")
            flat["denominador"] = flat.grupo.map(count.sum(axis=1))
            tables[name] = flat
            fig, axes = self.figure(figsize=(13, max(5, len(count) * .7 + 3)))
            ax = axes[0, 0]
            image = ax.imshow(proportions.to_numpy(), aspect="auto", cmap="YlOrBr", vmin=0, vmax=.5)
            ax.set_xticks(range(len(order)), labels if len(order) == len(labels) else [str(x) for x in order], rotation=55, ha="right")
            ax.set_yticks(range(len(count)), [textwrap.fill(str(x), 35) + f" (n={count.loc[x].sum()})" for x in count.index])
            for i in range(len(count)):
                for j in range(len(order)):
                    value = proportions.iloc[i, j]
                    ax.text(j, i, f"{100*value:.0f}", ha="center", va="center", fontsize=8,
                            color=self.theme.BRANCO if value > .30 else self.theme.TEXTO)
            fig.colorbar(image, ax=ax, label="Proporção por linha", format=FuncFormatter(lambda x, _: percent(x)))
            plots.append(self.finish(fig, f"P6_faixas_{name}", f"P6 - Faixas de salário declarado por {name}", source="SOD", note="Valores nas células em %; cada linha soma 100%; grupos n>=30; faixas abreviadas, não salários exatos."))
        mode = answered.faixa_salarial_declarada.value_counts().index[0]
        text = (f"Há {format_count(len(answered))} respostas salariais entre {format_count(len(self.sod))} residentes no Brasil; a faixa mais frequente é '{mode}'. "
                "Os mapas mostram a composição dentro de cada nível, cargo ou modelo de trabalho, com n>=30 por linha. "
                "Cargo exibe os seis de maior cobertura, não todos. Distribuições entre grupos não estimam efeito causal do remoto ou retorno da senioridade; "
                "nenhuma faixa foi convertida em ponto médio, média salarial ou valor individual exato.")
        return self.register("P6", tables, plots, text)

    def p7(self):
        overall = technology_rates(self.sod)
        by_area = technology_rates(self.sod, "area_profissional")
        fig = self.bars(overall, "tecnologia", "proporcao", "Uso entre quem respondeu ao item", percent_axis=True)
        selected = ["Dados e BI", "Engenharia e arquitetura de dados", "Ciencia de dados e IA", "Desenvolvimento de software", "Gestao", "Suporte e operacoes"]
        labels = ["SQL", "Python", "R", "Power BI", "AWS", "GCP", "Azure"]
        chosen = by_area[by_area.grupo.isin(selected)]
        heat = chosen.pivot(index="grupo", columns="tecnologia", values="proporcao").reindex(index=selected, columns=labels)
        denominators = chosen.pivot(index="grupo", columns="tecnologia", values="n_respondidos").reindex(index=selected, columns=labels)
        fig2, axes = self.figure(figsize=(12.5, 7))
        ax = axes[0, 0]
        image = ax.imshow(heat.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=1)
        ax.set_xticks(range(len(labels)), labels)
        ax.set_yticks(range(len(selected)), [textwrap.fill(x, 30) for x in selected])
        for i in range(len(selected)):
            for j in range(len(labels)):
                value = heat.iloc[i, j]
                label = f"{100 * value:.0f}%\nn={int(denominators.iloc[i, j])}" if np.isfinite(value) else "n<30"
                ax.text(j, i, label, ha="center", va="center", fontsize=8,
                        color=self.theme.TEXTO if not np.isfinite(value) or value > .55 else self.theme.BRANCO)
        fig2.colorbar(image, ax=ax, format=FuncFormatter(lambda x, _: percent(x)), label="Uso declarado entre respostas válidas")
        top = overall.sort_values("proporcao", ascending=False).iloc[0]
        text = (f"Entre os itens selecionados, {top.tecnologia} tem a maior proporção declarada ({percent(top.proporcao)}, "
                f"{format_count(top.n_usa)}/{format_count(top.n_respondidos)} respostas válidas). Os denominadores variam entre SQL/linguagens, BI e nuvem "
                "pela ramificação do questionário. Ausente não foi convertido em Não. A tabela por área mantém apenas proporções com n>=30 no item. "
                "Selecionar tecnologia não mede vagas abertas nem demanda empresarial; percentuais de várias tecnologias podem somar mais de 100%.")
        return self.register("P7", {"geral": overall, "por_area": by_area},
                             [self.finish(fig, "P7_tecnologias", "P7 - Tecnologias declaradas e denominadores por item", source="SOD", note="Consultar n de cada item nas tabelas; múltipla escolha."),
                              self.finish(fig2, "P7_tecnologias_por_perfil", "P7 - Tecnologias em seis perfis profissionais", source="SOD", note="Cada célula usa denominador próprio; n<30 não recebe proporção. Perfis selecionados, não todos.")], text)

    def p8(self):
        target = active_target(self.sod.planos_mudar_emprego_6m)
        valid = target.notna()
        general = pd.DataFrame({"classe": ["Busca ativa", "Sem busca ativa"], "n": [int(target.eq(True).sum()), int(target.eq(False).sum())]})
        general["denominador"] = int(valid.sum())
        general["proporcao"] = general.n / general.denominador
        records = []
        data = self.sod.assign(busca_ativa=target)
        for field in ["senioridade_declarada", "modelo_trabalho", "vinculo_grupo", "escolaridade_grupo"]:
            for category, group in data.groupby(field, dropna=True, observed=True):
                values = group.busca_ativa.dropna()
                if len(values) >= MIN_N and category != "Nao informado":
                    records.append({"variavel": field, "categoria": category, "n_alvo_valido": len(values),
                                    "n_busca_ativa": int(values.eq(True).sum()), "proporcao": float(values.astype(float).mean()),
                                    "n_alvo_ausente": int(group.busca_ativa.isna().sum())})
        groups = pd.DataFrame(records)
        fig = self.bars(groups[groups.variavel.eq("senioridade_declarada")], "categoria", "proporcao", "Busca ativa entre respostas válidas", percent_axis=True)
        text = (f"O alvo tem {format_count(valid.sum())} respostas válidas: {format_count(target.eq(True).sum())} de busca ativa "
                f"({percent(target.eq(True).sum()/valid.sum())}) e {format_count(target.eq(False).sum())} sem busca ativa. "
                f"As {int((~valid).sum())} ausências não viram negativas. As tabelas mostram associações descritivas por perfil com denominador válido. "
                "Não foi treinado classificador nesta etapa: matriz de confusão, ROC e F1 pertencem à fase 05. Busca declarada não é desligamento futuro.")
        return self.register("P8", {"classes": general, "por_perfil": groups},
                             [self.finish(fig, "P8_busca_por_senioridade", "P8 - Busca ativa declarada por senioridade", source="SOD", note="Proporções internas à amostra; não são probabilidades de saída previstas.")], text)

    def p9(self):
        scale = frequencies(self.g12.facilidade_informacao_escala_1_5).sort_values("categoria")
        difficulty = frequencies(self.g12.dificuldade_principal)
        fig = self.bars(difficulty, "categoria", "n", "Respostas à dificuldade principal")
        fig2, axes = self.figure(figsize=(9, 5))
        axes[0, 0].bar(scale.categoria, scale.n, color=self.theme.LARANJA)
        axes[0, 0].set_xlabel("Nota declarada; âncoras não disponíveis")
        axes[0, 0].set_ylabel("Respostas")
        mode = difficulty.iloc[0]
        text = (f"Na amostra própria, a dificuldade mais frequente é '{mode.categoria}' ({int(mode.n)}/{int(mode.denominador)}; {percent(mode.proporcao)}). "
                "A distribuição de notas é apresentada sem inferir qual extremo significa maior facilidade, pois faltam as âncoras. "
                "Não representa todos os estudantes ou profissionais; resultados e células pequenas ficam locais, sujeitos à revisão antes de divulgação.")
        return self.register("P9", {"notas": scale, "dificuldades": difficulty},
                             [self.finish(fig, "P9_dificuldades", "P9 - Dificuldades de acesso à informação", "G12", True),
                              self.finish(fig2, "P9_notas", "P9 - Notas declaradas de acesso à informação", "G12", True)], text, True)

    def p10(self):
        valid = self.g12.prioridades_tratamento.eq("valido")
        denominator = int(valid.sum())
        counts = self.priorities.groupby(["opcao_id", "opcao"]).respondente_id.nunique().rename("n_selecionaram").reset_index()
        counts["denominador_participantes"] = denominator
        counts["proporcao"] = counts.n_selecionaram / denominator
        intent = frequencies(self.g12.usaria_ferramenta.map({True: "Sim", False: "Não"}))
        fig = self.bars(counts, "opcao", "proporcao", "Participantes que selecionaram a opção", percent_axis=True)
        fig2 = self.bars(intent, "categoria", "n", "Respostas Sim/Não válidas")
        yes = intent[intent.categoria.eq("Sim")].iloc[0]
        top = counts.sort_values("n_selecionaram", ascending=False).iloc[0]
        text = (f"Q08 tem {denominator} participantes com seleção reconhecida e {len(self.priorities)} escolhas; "
                f"'{top.opcao}' aparece em {int(top.n_selecionaram)} respostas ({percent(top.proporcao)}). "
                f"Q07 tem {int(yes.denominador)} Sim/Não válidos, com {int(yes.n)} Sim ({percent(yes.proporcao)}); três respostas fora do domínio foram excluídas "
                "somente desse denominador. Várias prioridades podem superar 100% somadas. Pergunta sobre a solução mede intenção autodeclarada, "
                "não uso observado; a intenção de uso foi analisada em tabela local, sem extrapolar adoção.")
        return self.register("P10", {"prioridades": counts, "intencao_valida": intent},
                             [self.finish(fig, "P10_prioridades", "P10 - Informações prioritárias para a amostra G12", "G12", True),
                              self.finish(fig2, "P10_intencao_restrita", "P10 - Intenção declarada de uso: análise interna", "G12", True,
                                          note="32 respostas válidas; três fora do domínio. Intenção não é adoção observada.")], text, True)

    def p11(self):
        valid = self.g12[~self.g12.expectativa_salarial_revisar].copy()
        salary = valid.expectativa_salarial_mensal.astype(float)
        raw = self.g12.expectativa_salarial_mensal.dropna().astype(float)
        n, rho = correlation_pair(valid, "experiencia_ti_meses_exatos", "expectativa_salarial_mensal")
        summary = pd.DataFrame({"recorte": ["Com revisão aplicada", "Todos os valores numéricos"], "n": [len(salary), len(raw)],
                                "q25": [salary.quantile(.25), raw.quantile(.25)], "mediana": [salary.median(), raw.median()],
                                "q75": [salary.quantile(.75), raw.quantile(.75)]})
        relation = pd.DataFrame({"n_pares_exatos": [n], "rho_spearman": [rho],
                                 "intervalos_nao_imputados": [int(self.g12.experiencia_ti_tratamento.eq("intervalo_declarado").sum())]})
        fig, axes = self.figure(figsize=(10, 5.5))
        axes[0, 0].hist(salary, bins=[0, 2000, 4000, 6000, 10000, 15000, 25000], color=self.theme.LARANJA, edgecolor=self.theme.BRANCO)
        axes[0, 0].set_xlabel("Expectativa mensal declarada (R$); após sinalização")
        axes[0, 0].set_ylabel("Respostas")
        axes[0, 0].xaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        pair = valid[["experiencia_ti_meses_exatos", "expectativa_salarial_mensal"]].dropna().astype(float)
        fig2, axes2 = self.figure(figsize=(9.5, 6))
        axes2[0, 0].scatter(pair.experiencia_ti_meses_exatos, pair.expectativa_salarial_mensal, alpha=.65, color=self.theme.LARANJA)
        axes2[0, 0].set_xlabel("Experiência exata declarada (meses)")
        axes2[0, 0].set_ylabel("Expectativa mensal (R$); não salário recebido")
        axes2[0, 0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: money(x)))
        text = (f"Após sinalizar uma expectativa, restam {len(salary)} valores: mediana {money(salary.median())}, "
                f"Q1={money(salary.quantile(.25))} e Q3={money(salary.quantile(.75))}. Incluindo o valor sinalizado, a mediana é {money(raw.median())}. "
                f"A associação com meses exatos tem n={n} e rho={rho:.3f}; o intervalo 7-8 meses não foi imputado. "
                "A amostra é pequena e valores altos influenciam a distribuição. Não há UF/cargo equivalentes nem período comum para comparar "
                "essa expectativa de 2026 ao salário CAGED de 2025. A dispersão é apenas para análise interna restrita.")
        return self.register("P11", {"expectativas_sensibilidade": summary, "relacao_experiencia": relation},
                             [self.finish(fig, "P11_expectativas", "P11 - Distribuição das expectativas salariais", "G12", True),
                              self.finish(fig2, "P11_relacao_restrita", "P11 - Experiência e expectativa: visualização interna", "G12", True)], text, True)

    def p12(self):
        tables = {field: frequencies(self.g12[field].map({True: "Sim", False: "Não"}))
                  for field in ["busca_mudanca", "cogitou_mudar_desistir"]}
        fig, axes = self.figure(cols=2, figsize=(10, 5))
        labels = ["Busca mudança atual", "Cogitou sair/mudar em 12 meses"]
        for i, (field, data) in enumerate(tables.items()):
            axes[0, i].bar(data.categoria, data.n, color=[self.theme.LARANJA if x == "Sim" else self.theme.NEUTRO_GRAFICO for x in data.categoria])
            axes[0, i].set_title(labels[i], fontsize=11)
            axes[0, i].set_ylabel("Respostas válidas")
            axes[0, i].set_ylim(0, len(self.g12))
        first = tables["busca_mudanca"].set_index("categoria").loc["Sim"]
        second = tables["cogitou_mudar_desistir"].set_index("categoria").loc["Sim"]
        text = (f"{int(first.n)}/{int(first.denominador)} respostas declaram busca atual de mudança ({percent(first.proporcao)}); "
                f"{int(second.n)}/{int(second.denominador)} relatam ter cogitado sair ou mudar de área em 12 meses ({percent(second.proporcao)}). "
                "São itens distintos: Q10 inclui emprego, área ou regime; Q11 relata cogitação, não saída efetiva. Não concluir causalidade "
                "da falta de informação nem juntar esses alvos ao State of Data. Nenhum classificador foi treinado com a amostra G12.")
        return self.register("P12", tables, [self.finish(fig, "P12_intencoes", "P12 - Intenções distintas de mudança", "G12", True)], text, True)

    def run(self, key):
        if key == "M1":
            return self.multivariate()
        return getattr(self, key.lower())()

    def write_summary(self):
        public = ["# Síntese da análise exploratória", "", "Resultados das fontes públicas, separados por unidade e período. Não inclui dados da pesquisa própria.", ""]
        local = ["# Pesquisa G12: resultados internos", "", "Uso local restrito. Consentimento de divulgação não confirmado; não publicar microdados, imagens ou resultados desta pasta sem revisão.", ""]
        for key, result in self.results.items():
            target = local if result["restrito"] else public
            target += [f"## {key}", "", result["interpretacao"], ""]
        public += ["## Limites gerais", "", "Associações não demonstram causalidade; movimentações não identificam pessoas. Recortes regionais se sobrepõem. A amostra State of Data é voluntária; carreira em dados não representa toda TI. A matriz de desk research não foi tratada como evidência verificada. Modelos de regressão e classificação serão desenvolvidos nas fases seguintes.", ""]
        (self.area / "sintese_achados.md").write_text("\n".join(public), encoding="utf-8")
        folder = self.local / "pesquisa_grupo12"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "interpretacao_interna.md").write_text("\n".join(local), encoding="utf-8")

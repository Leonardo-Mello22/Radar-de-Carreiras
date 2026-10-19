"""Consolidated Radar dashboard v1.1; public aggregates only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[1]
sys.path.insert(0, str(AREA))
sys.path.insert(1, str(ROOT))
from app import theme
from dados import MIN_N, PERIODS, PackageError, caged_groups, caged_query, export_csv, geography, load_package, occupation, profile_query

PUBLIC = AREA / "dados_publicos"
st.set_page_config(page_title="Radar de carreiras", page_icon=":material/radar:", layout="wide")
st.markdown(f"""<style>
 .stApp {{background:{theme.BRANCO}; color:{theme.TEXTO};}}
 header[data-testid="stHeader"] {{display:none;}}
 .block-container {{max-width:1240px; padding-top:1.4rem; padding-bottom:2rem;}}
 h1,h2,h3,p,label,button,div {{letter-spacing:0 !important;}}
 .brand {{display:flex; align-items:center; gap:12px; margin-bottom:6px;}}
 .brand h1 {{font-size:27px; line-height:1.2; padding:0; margin:0; font-weight:750;}}
 .edition {{font-size:12px; color:{theme.TEXTO_SECUNDARIO}; margin-bottom:20px;}}
 h2 {{font-size:21px !important; padding-top:1rem !important;}}
 h3 {{font-size:17px !important;}}
 [data-testid="stMetric"] {{border-top:2px solid {theme.BORDA_CLARA}; padding-top:12px; min-width:0;}}
 [data-testid="stMetricValue"] {{font-size:27px; overflow-wrap:anywhere; white-space:normal;}}
 [data-testid="stMetricLabel"] {{font-size:13px;}}
 [data-testid="stVerticalBlock"] {{gap:.8rem;}}
 [data-testid="stCaptionContainer"] {{color:{theme.TEXTO_SECUNDARIO}; font-size:12px;}}
 [data-testid="stButtonGroup"] {{margin-bottom:12px;}}
 button,[data-baseweb="select"]>div {{border-radius:5px !important;}}
 [data-testid="stDownloadButton"] button {{min-height:38px;}}
 @media(max-width:640px) {{
  .block-container {{padding:1rem .9rem 2rem;}}
  .brand h1 {{font-size:23px;}}
  [data-testid="stMetricValue"] {{font-size:25px;}}
 }}
 </style>""", unsafe_allow_html=True)
st.markdown(f'<div class="brand">{theme.aro_svg(34)}<h1>Radar de carreiras</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="edition">INTELIGÊNCIA DE CARREIRAS · V1.1</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_package(signature):
    return load_package(PUBLIC)


def money(value):
    return "R$ " + f"{value:,.0f}".replace(",", ".") if pd.notna(value) else "Indisponível"


def count(value):
    return f"{int(value):,}".replace(",", ".")


def money_text(value):
    return money(value).replace("$", "\\$")


def percent(value):
    return f"{100*value:.1f}%".replace(".", ",") if pd.notna(value) else "Indisponível"


def chart(value):
    value = value.configure_axis(labelFontSize=11, titleFontSize=11, gridColor=theme.TRILHO_GRAFICO, labelLimit=190).configure_view(stroke=None)
    st.altair_chart(value, width="stretch")


def reset(prefix):
    defaults = {"c_regiao": "Pernambuco", "c_uf": "PE", "c_periodo": "2025T1", "c_area": "Todas", "c_cargo": "Todos",
                "p_regiao": "Brasil", "p_uf": "Todas", "p_senior": "Todos", "p_modelo": "Todos"}
    for key, value in defaults.items():
        if key.startswith(prefix):
            st.session_state[key] = value


def clear_uf(prefix):
    st.session_state[prefix+"uf"] = "PE" if st.session_state[prefix+"regiao"] == "Pernambuco" else "Todas"


def location_filters(package, prefix, default_region):
    c1, c2 = st.columns(2)
    regions = ["Pernambuco", "Nordeste", "Brasil"]
    region = c1.selectbox("Região", regions, index=regions.index(default_region), key=prefix+"regiao", on_change=clear_uf, args=(prefix,), persist_state="session")
    ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
    options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
    if st.session_state.get(prefix+"uf") not in options:
        st.session_state[prefix+"uf"] = options[0]
    uf = c2.selectbox("UF", options, key=prefix+"uf", disabled=region == "Pernambuco", persist_state="session")
    return geography(region, uf), "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)


def download(label, table, filename):
    payload = export_csv(table)
    key = "export_" + hashlib.sha256(payload).hexdigest()[:16]
    st.download_button(label, payload, file_name=filename, mime="text/csv", icon=":material/download:", key=key, on_click="ignore")


def employment(package):
    st.header("Emprego formal em TI")
    st.caption("Novo CAGED MOV · janeiro a março de 2025 · salários mensais a preços de março/2025")
    with st.expander("Filtros do recorte", expanded=False, icon=":material/tune:"):
        geo, location = location_filters(package, "c_", "Pernambuco")
        a, b, c = st.columns([1, 1.2, 1.8])
        period = a.selectbox("Período", list(PERIODS), format_func=PERIODS.get, key="c_periodo", persist_state="session")
        catalog = package["metadata"]["catalogo"]
        areas = ["Todas", *[v["categoria"] for v in catalog if v["tipo"] == "area"]]
        area = b.selectbox("Área de TI", areas, key="c_area", persist_state="session")
        occupations = {v["categoria"]: v["rotulo"] for v in catalog if v["tipo"] == "cargo" and (area == "Todas" or v["area"] == area)}
        options = ["Todos", *occupations]
        if st.session_state.get("c_cargo") not in options:
            st.session_state.c_cargo = "Todos"
        cargo = c.selectbox("Ocupação", options, format_func=lambda v: occupations.get(v, "Todas as ocupações"), key="c_cargo", persist_state="session")
        st.button("Restaurar filtros", icon=":material/restart_alt:", on_click=reset, args=("c_",), key="reset_caged")
    kind, category = occupation(area, cargo)
    rows = caged_query(package, geo, period, kind, category)
    st.subheader(f"{location} · {PERIODS[period]}")
    st.caption(f"Área: {area if area != 'Todas' else 'Todas as áreas'} · Ocupação: {occupations[cargo] + ' (CBO ' + cargo + ')' if cargo != 'Todos' else 'Todas as ocupações'}")
    if rows.empty or rows.iloc[0].n_eventos == 0:
        st.info("Nenhuma movimentação encontrada neste recorte.")
        return
    row = rows.iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Mediana de admissão", money(row.admissoes_p50), help="Salário mensal corrigido pelo IPCA para março/2025; somente admissões com salário válido. Não é salário atual nem previsão individual.")
    k2.metric("Admissões", count(row.admissoes))
    k3.metric("Desligamentos", count(row.desligamentos))
    k4.metric("Diferença MOV", count(row.diferenca_mov), help="Admissões menos desligamentos dos arquivos MOV. Não inclui ajustes FOR/EXC e não é o saldo oficial ajustado.")
    st.caption(f"{count(row.admissoes_validos)} salários válidos de admissão · {count(row.admissoes-row.admissoes_validos)} sinalizados fora das estatísticas salariais. Diferença MOV não é o saldo oficial ajustado.")
    if row.admissoes_validos < MIN_N:
        st.warning(f"Dados salariais insuficientes: n={int(row.admissoes_validos)}; mínimo de {MIN_N}. As contagens de eventos permanecem disponíveis.")
    else:
        st.write(f"Nas admissões deste recorte, p10 é {money_text(row.admissoes_p10)} e p90 é {money_text(row.admissoes_p90)}. São percentis da distribuição, não mínimo/máximo ou salário júnior.")
    table = package["emprego"]
    monthly = table[table.geo.eq(geo) & table.tipo.eq(kind) & table.categoria.eq(category) & table.periodo.ne("2025T1")].copy()
    if period != "2025T1":
        monthly = monthly[monthly.periodo.eq(period)]
    monthly["mes"] = monthly.periodo.map(PERIODS)
    left, right = st.columns(2)
    with left:
        st.subheader("Faixas salariais de admissão")
        groups = caged_groups(package, geo, period, area, cargo)
        eligible = groups[groups.admissoes_validos.ge(MIN_N)].copy()
        if eligible.empty:
            st.info("Nenhum grupo com pelo menos 30 salários válidos.")
        else:
            base = alt.Chart(eligible).encode(y=alt.Y("rotulo:N", title=None, sort=alt.SortField("admissoes_p50", order="descending")), tooltip=[alt.Tooltip("rotulo:N", title="Grupo"), alt.Tooltip("admissoes_validos:Q", title="n válido"), alt.Tooltip("admissoes_p10:Q", title="p10 (R$)", format=",.0f"), alt.Tooltip("admissoes_p50:Q", title="Mediana (R$)", format=",.0f"), alt.Tooltip("admissoes_p90:Q", title="p90 (R$)", format=",.0f")])
            rule = base.mark_rule(strokeWidth=7, color=theme.FAIXA_PREENCHIMENTO).encode(x=alt.X("admissoes_p10:Q", title="Salário mensal real (R$)", scale=alt.Scale(zero=True)), x2="admissoes_p90:Q")
            points = base.mark_point(filled=True, color=theme.LARANJA, size=65).encode(x="admissoes_p50:Q")
            chart((rule+points).properties(height=max(250, len(eligible)*27)))
        st.caption("Faixa p10-p90 e mediana · cada quantil é calculado diretamente no recorte, sem média de percentis.")
    with right:
        st.subheader("Movimentações por mês")
        movement = monthly.melt(id_vars=["mes", "periodo"], value_vars=["admissoes", "desligamentos"], var_name="movimento", value_name="n")
        movement["movimento"] = movement.movimento.map({"admissoes": "Admissões", "desligamentos": "Desligamentos"})
        chart(alt.Chart(movement).mark_bar().encode(x=alt.X("mes:N", title=None, sort=list(PERIODS.values())[1:]), xOffset="movimento:N", y=alt.Y("n:Q", title="Movimentações", scale=alt.Scale(zero=True)), color=alt.Color("movimento:N", title=None, scale=alt.Scale(domain=["Admissões", "Desligamentos"], range=[theme.LARANJA, theme.NEUTRO_GRAFICO]), legend=alt.Legend(orient="top")), tooltip=["mes:N", "movimento:N", alt.Tooltip("n:Q", title="Eventos")]).properties(height=280))
        st.caption("Todos os eventos, inclusive salários sinalizados · três meses não permitem inferir sazonalidade.")
    st.subheader("Mediana mensal de admissão")
    chart(alt.Chart(monthly).mark_line(point=True, color=theme.LARANJA).encode(x=alt.X("mes:N", sort=list(PERIODS.values())[1:], title=None), y=alt.Y("admissoes_p50:Q", title="R$ a preços de março/2025", scale=alt.Scale(zero=True)), tooltip=["mes:N", alt.Tooltip("admissoes_p50:Q", title="Mediana", format=",.0f"), alt.Tooltip("admissoes_validos:Q", title="n válido")]).properties(height=200))
    st.caption("Meses com n<30 não exibem mediana. Mudanças entre meses não acompanham as mesmas pessoas.")
    with st.expander("Comparativo de admissão e desligamento"):
        if row.admissoes_validos >= MIN_N and row.desligamentos_validos >= MIN_N:
            st.write(f"Mediana de admissão: {money_text(row.admissoes_p50)}. Mediana de desligamento: {money_text(row.desligamentos_p50)}. São grupos distintos; a diferença não mede promoção ou aumento salarial individual.")
        else:
            st.info("Pelo menos um movimento tem menos de 30 salários válidos; comparação salarial indisponível.")
        st.dataframe(rows.drop(columns=["geo", "tipo"]), hide_index=True, width="stretch")
    download("Baixar recorte agregado", rows, "emprego_recorte.csv")


def distribution_chart(frame, field, title):
    selected = frame[frame.variavel.eq(field)].copy()
    st.subheader(title)
    if selected.empty:
        st.info("Base respondida insuficiente para esta distribuição.")
        return
    selected["rotulo"] = selected.categoria.str.replace("de R$ ", "", regex=False).str.replace("/mês", "", regex=False)
    order = list(selected.sort_values("ordem").rotulo) if field == "salario" else alt.SortField("n", order="descending")
    chart(alt.Chart(selected).mark_bar(color=theme.NEUTRO_GRAFICO).encode(y=alt.Y("rotulo:N", sort=order, title=None), x=alt.X("proporcao:Q", title="Proporção das respostas válidas", axis=alt.Axis(format="%"), scale=alt.Scale(zero=True)), tooltip=[alt.Tooltip("categoria:N", title="Resposta"), "n:Q", alt.Tooltip("denominador:Q", title="Base válida"), alt.Tooltip("proporcao:Q", format=".1%", title="Proporção")]).properties(height=max(260, len(selected)*25)))
    st.caption(f"Base respondida: {count(selected.denominador.iloc[0])}. Categorias com menos de 5 respostas estão reunidas em Outras respostas.")


def profiles(package):
    st.header("Perfis na área de dados")
    st.caption("State of Data Brazil 2024-2025 · pesquisa voluntária e autodeclarada · residentes no Brasil")
    with st.expander("Filtros do recorte", expanded=False, icon=":material/tune:"):
        geo, location = location_filters(package, "p_", "Brasil")
        c1, c2 = st.columns(2)
        senior = c1.selectbox("Senioridade declarada", ["Todos", "Junior", "Pleno", "Senior", "Nao informado"], format_func=lambda v: {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(v, v), key="p_senior", persist_state="session")
        work = c2.selectbox("Modelo de trabalho", ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"], format_func=lambda v: {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(v, v), key="p_modelo", persist_state="session")
        st.button("Restaurar filtros", icon=":material/restart_alt:", on_click=reset, args=("p_",), key="reset_profiles")
    result = profile_query(package, geo, senior, work)
    st.subheader(location)
    senior_label = {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(senior, senior)
    work_label = {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(work, work)
    st.caption(f"Senioridade: {senior_label} · Trabalho: {work_label}")
    if result["perfis"].empty:
        st.info("Nenhuma resposta neste recorte.")
        return
    row = result["perfis"].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Respostas no recorte", count(row.n_respostas))
    c2.metric("Faixa salarial respondida", count(row.n_salarios))
    c3.metric("Busca ativa declarada", percent(row.proporcao_ativa), help="Proporção somente entre respostas válidas à pergunta. Ausentes não contam como Não; mínimo de 30 respostas válidas.")
    st.caption(f"Busca ativa: base válida de {count(row.n_alvo)} respostas; {count(row.n_respostas-row.n_alvo)} ausentes, não tratados como Não.")
    if row.n_respostas < MIN_N:
        st.warning(f"Dados insuficientes para comparar perfis: n={int(row.n_respostas)}; mínimo de {MIN_N}. Nenhuma distribuição é exibida.")
        return
    if row.n_alvo < MIN_N:
        st.warning(f"Busca ativa indisponível: somente {int(row.n_alvo)} respostas válidas ao item; mínimo de {MIN_N}. As outras distribuições usam suas próprias bases válidas.")
    left, right = st.columns(2)
    with left:
        distribution_chart(result["distribuicoes"], "salario", "Faixas salariais declaradas")
        st.caption("Faixas não viram salários exatos ou médias; a faixa superior é aberta.")
    with right:
        st.subheader("Tecnologias declaradas")
        tech = result["tecnologias"].dropna(subset=["proporcao"])
        if tech.empty:
            st.info("Nenhuma tecnologia com pelo menos 30 respostas válidas ao item.")
        else:
            chart(alt.Chart(tech).mark_bar(color=theme.LARANJA).encode(y=alt.Y("tecnologia:N", sort="-x", title=None), x=alt.X("proporcao:Q", title="Usuários entre respondentes do item", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")), tooltip=["tecnologia:N", alt.Tooltip("n:Q", title="Selecionaram"), alt.Tooltip("denominador:Q", title="Base válida do item"), alt.Tooltip("proporcao:Q", title="Proporção", format=".1%")]).properties(height=300))
        st.caption("Cada item tem seu denominador. Ausente não é Não; múltiplas escolhas podem somar mais de 100%.")
    left, right = st.columns(2)
    with left:
        distribution_chart(result["distribuicoes"], "formacao", "Formação declarada")
    with right:
        distribution_chart(result["distribuicoes"], "vinculo", "Vínculo de trabalho")
    st.caption("Senioridade ausente pode refletir ramificações do formulário. Experiência em dados não equivale à carreira profissional inteira.")
    download("Baixar distribuições agregadas", result["distribuicoes"], "perfis_distribuicoes.csv")


def models(package):
    st.header("Avaliação dos modelos")
    view = st.segmented_control("Análise", ["Salários", "Busca ativa"], default="Salários", required=True, key="modelo_visao", persist_state="session")
    if view == "Salários":
        table = package["R1_teste_marco"]
        meta = package["metadata"]["modelos"]["regressao"]
        chosen = table[table.modelo.eq(meta["modelo_selecionado"])].iloc[0]
        st.caption(f"CAGED · treino: jan-fev/2025 · teste reservado: mar/2025 · n={count(meta['n_teste'])} · métricas fixas da etapa 04")
        a, b, c = st.columns(3)
        a.metric("MAE do modelo selecionado", money(chosen.mae))
        b.metric("RMSE", money(chosen.rmse))
        c.metric("R²", f"{chosen.r2:.3f}")
        st.warning(f"{int(chosen.previsoes_negativas)} previsões negativas foram mantidas na avaliação. O modelo não é uma calculadora salarial individual.")
        st.dataframe(table[["modelo", "n", "mae", "rmse", "r2", "previsoes_negativas"]], hide_index=True, width="stretch")
        st.image(str(PUBLIC / "R3_observado_previsto.png"), width="stretch")
        st.image(str(PUBLIC / "R4_residuos.png"), width="stretch")
        st.caption("Relações observacionais; idade não é experiência. Uma linha é um evento, não uma pessoa ou vínculo acompanhado.")
        download("Baixar métricas de regressão", table, "regressao_metricas.csv")
        return
    meta = package["metadata"]["modelos"]["classificacao"]
    st.caption(f"State of Data · treino: {count(meta['n_treino'])} · teste estratificado: {count(meta['n_teste'])} · classe 1 = busca ativa · limiar fixo 0,5")
    names = {"logistica": "Regressão logística", "arvore": "Árvore simples", "majoritaria": "Classe majoritária"}
    key = st.selectbox("Classificador", list(names), format_func=names.get, key="classificador", persist_state="session")
    row = package["C1_metricas_teste"].set_index("modelo").loc[key]
    a, b, c, d = st.columns(4)
    a.metric("Acurácia", percent(row.acuracia))
    b.metric("Precisão da classe 1", percent(row.precisao))
    c.metric("Recall da classe 1", percent(row.recall))
    d.metric("F1 da classe 1", f"{row.f1:.3f}")
    st.warning(f"{int(row.fn)} de {int(row.n_ativos)} buscas ativas não foram identificadas. Acurácia isolada não valida detecção individual.")
    matrix = pd.DataFrame([{"Observado": str(obs), "Previsto": str(pred), "n": int(row[field]), "taxa": row[field]/total} for obs, total, pair in [(0, row.tn+row.fp, [(0, "tn"), (1, "fp")]), (1, row.fn+row.tp, [(0, "fn"), (1, "tp")])] for pred, field in pair])
    st.subheader("Matriz de confusão")
    base = alt.Chart(matrix).encode(x=alt.X("Previsto:N", title="Classe prevista", axis=alt.Axis(labelAngle=0)), y=alt.Y("Observado:N", title="Classe observada"), tooltip=["Observado:N", "Previsto:N", "n:Q", alt.Tooltip("taxa:Q", format=".1%", title="Proporção na linha")])
    chart((base.mark_rect().encode(color=alt.Color("taxa:Q", scale=alt.Scale(domain=[0, 1], range=[theme.CINZA_CLARO, theme.GRAFITE]), legend=None)) + base.mark_text(fontSize=21).encode(text="n:Q", color=alt.condition(alt.datum.taxa > .5, alt.value(theme.BRANCO), alt.value(theme.TEXTO)))).properties(height=240))
    st.caption("0: sem busca ativa · 1: busca ativa declarada · cores normalizadas por classe observada")
    left, right = st.columns(2)
    for column, dataset, x, y, title, x_title, y_title in [(left, "C4_curvas_roc", "taxa_falso_positivo", "taxa_verdadeiro_positivo", "Curvas ROC", "Taxa de falsos positivos", "Recall"), (right, "C5_curvas_precision_recall", "recall", "precisao", "Precision-recall", "Recall", "Precisão")]:
        with column:
            st.subheader(title)
            curves = package[dataset].copy()
            curves["classificador"] = curves.modelo.map(names)
            curves["ordem"] = curves.groupby("modelo").cumcount()
            chart(alt.Chart(curves).mark_line(interpolate="step-after" if dataset == "C5_curvas_precision_recall" else "linear").encode(x=alt.X(x+":Q", title=x_title, scale=alt.Scale(domain=[0, 1])), y=alt.Y(y+":Q", title=y_title, scale=alt.Scale(domain=[0, 1])), color=alt.Color("classificador:N", title=None, scale=alt.Scale(domain=list(names.values()), range=[theme.LARANJA, theme.GRAFITE, theme.NEUTRO_GRAFICO]), legend=alt.Legend(orient="bottom")), order="ordem:Q", tooltip=["classificador:N", alt.Tooltip(x+":Q", format=".3f"), alt.Tooltip(y+":Q", format=".3f")]).properties(height=270))
    st.write(f"ROC-AUC do classificador selecionado: **{row.roc_auc:.3f}**. Average Precision: **{row.average_precision:.3f}**; prevalência no teste: **{row.n_ativos/row.n:.3f}**.")
    st.caption("A logística foi escolhida por validação somente no treino; o seletor compara resultados já calculados, sem retreinar. AP não é área trapezoidal genérica. Intenção contemporânea, não saída futura; amostra voluntária com viés de elegibilidade.")
    download("Baixar métricas de classificação", package["C1_metricas_teste"], "classificacao_metricas.csv")


def sources(package):
    st.header("Fontes e limites")
    meta = package["metadata"]
    st.dataframe(pd.DataFrame([
        {"Fonte": "Novo CAGED MOV", "Período": "Jan-mar/2025", "Unidade": "Movimentação formal", "Registros preparados": meta["fontes"]["caged_ti"]["n"]},
        {"Fonte": "State of Data Brazil", "Período": "2024-2025", "Unidade": "Resposta de participante residente no Brasil", "Registros preparados": meta["fontes"]["state_of_data_brasil"]["n"]},
    ]), hide_index=True, width="stretch")
    st.subheader("Emprego formal")
    st.write("O CAGED não cobre PJ ou informalidade, não identifica senioridade e não acompanha a trajetória de uma pessoa. A diferença de admissões e desligamentos dos arquivos MOV não inclui os ajustes FOR/EXC. Os salários são mensais, corrigidos pelo IPCA para março de 2025, não salários atuais de 2026.")
    st.subheader("Pesquisa em dados")
    st.write("Pesquisa voluntária, autodeclarada e específica da área de dados. Ausente não é uma resposta negativa. Faixas salariais não são convertidas em salário exato. As bases válidas variam por item; recortes pequenos não sustentam comparação.")
    st.subheader("Privacidade")
    st.write("O pacote contém agregados de fontes públicas. Não contém IDs, respostas individuais ou escores por pessoa. A pesquisa G12 não está publicada: a autorização de divulgação permanece pendente. As fontes não foram concatenadas como uma única população.")
    st.caption("Mínimo operacional: 30 observações válidas por comparação. A regra não garante representatividade ou independência. Versão dos agregados: " + meta["preparado_em"][:10])
    st.link_button("Microdados MTE", "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged", icon=":material/open_in_new:")
    st.link_button("State of Data Brazil", "https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025", icon=":material/open_in_new:")
    st.download_button("Baixar manifesto público", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"), file_name="manifesto_publico.json", mime="application/json", icon=":material/download:")


try:
    signature = (PUBLIC / "manifesto.json").stat().st_mtime_ns
    package = cached_package(signature)
except (PackageError, OSError):
    st.error("Pacote público indisponível ou com integridade inválida. Nenhuma análise foi carregada.")
    st.stop()

view = st.segmented_control("Visão", ["Emprego formal", "Perfis em dados", "Modelos", "Fontes"], default="Emprego formal", required=True, key="visao", label_visibility="collapsed")
{"Emprego formal": employment, "Perfis em dados": profiles, "Modelos": models, "Fontes": sources}[view](package)
st.divider()
st.caption("Radar de carreiras · Novo CAGED / State of Data · populações e períodos analisados separadamente")

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
 .edition {{font-size:12.5px; color:{theme.LARANJA}; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;}}
 .lead {{font-size:16px; line-height:1.55; color:{theme.TEXTO_SECUNDARIO}; max-width:760px; margin:0 0 18px;}}
 [data-testid="stButtonGroup"] button p {{font-size:15px !important; font-weight:600 !important;}}
 .ajuda {{font-size:13.5px; color:{theme.TEXTO_SECUNDARIO}; margin:2px 0 18px;}}
 .resp-rotulo {{font-size:13px; text-transform:uppercase; letter-spacing:1px; color:{theme.TEXTO_SECUNDARIO}; margin:22px 0 2px;}}
 .resp-numero {{font-size:54px; font-weight:800; color:{theme.LARANJA}; line-height:1; margin:0;}}
 .resp-numero span {{font-size:20px; color:{theme.TEXTO_SECUNDARIO}; font-weight:600;}}
 .resp-faixa {{font-size:17px; color:{theme.TEXTO}; margin:8px 0 10px;}}
 div[data-testid="stExpander"] summary p {{font-weight:600;}}
 .stSelectbox label {{font-size:15px !important; font-weight:600 !important; color:{theme.TEXTO} !important;}}
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
st.markdown('<div class="edition">Salários e vagas de TI explicados de forma simples, com dados oficiais</div>', unsafe_allow_html=True)
st.markdown('<p class="lead">Descubra quanto pagam os cargos de tecnologia, onde estão surgindo vagas e o que esperar no começo da carreira. É só escolher uma seção abaixo e, dentro dela, a sua cidade e o cargo.</p>', unsafe_allow_html=True)


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
    st.header("Salários e vagas em TI")
    st.caption("A partir de registros oficiais de contratações com carteira assinada (Novo CAGED), de janeiro a março de 2025. Os valores já estão corrigidos pela inflação.")

    catalog = package["metadata"]["catalogo"]
    area_atual = st.session_state.get("c_area", "Todas")
    occupations = {v["categoria"]: v["rotulo"] for v in catalog if v["tipo"] == "cargo" and (area_atual == "Todas" or v["area"] == area_atual)}

    f1, f2 = st.columns(2)
    with f1:
        options = ["Todos", *occupations]
        if st.session_state.get("c_cargo") not in options:
            st.session_state["c_cargo"] = "Todos"
        cargo = st.selectbox("Qual cargo?", options, format_func=lambda v: occupations.get(v, "Todos os cargos"), key="c_cargo", persist_state="session")
    with f2:
        regions = ["Pernambuco", "Nordeste", "Brasil"]
        region = st.selectbox("Onde?", regions, key="c_regiao", on_change=clear_uf, args=("c_",), persist_state="session")

    with st.expander("Mais opções (estado, área, período)"):
        m1, m2, m3 = st.columns(3)
        areas = ["Todas", *[v["categoria"] for v in catalog if v["tipo"] == "area"]]
        area = m1.selectbox("Área de TI", areas, key="c_area", persist_state="session")
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("c_uf") not in uf_options:
            st.session_state["c_uf"] = uf_options[0]
        uf = m2.selectbox("Estado", uf_options, key="c_uf", disabled=region == "Pernambuco", persist_state="session")
        period = m3.selectbox("Período", list(PERIODS), format_func=PERIODS.get, key="c_periodo", persist_state="session")
        st.button("Restaurar filtros", icon=":material/restart_alt:", on_click=reset, args=("c_",), key="reset_caged")

    geo = geography(region, uf)
    location = "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)
    kind, category = occupation(area, cargo)
    rows = caged_query(package, geo, period, kind, category)
    if rows.empty or rows.iloc[0].n_eventos == 0:
        st.info("Não encontramos contratações para essa combinação. Experimente 'Todos os cargos' ou uma região maior, como o Brasil.")
        return
    row = rows.iloc[0]
    cargo_label = occupations[cargo] if cargo != "Todos" else "TI em geral"

    st.markdown(f'<p class="resp-rotulo">Salário típico de entrada · {cargo_label} · {location}</p>', unsafe_allow_html=True)
    if row.admissoes_validos < MIN_N:
        st.warning(f"Há poucos dados de salário aqui (menos de {MIN_N} contratações), então não mostramos o valor para não enganar. Experimente 'Todos os cargos' ou uma região maior.")
    else:
        st.markdown(f'<p class="resp-numero">{money(row.admissoes_p50)}<span> /mês</span></p>', unsafe_allow_html=True)
        st.markdown(f'<p class="resp-faixa">A maioria entra ganhando entre <b>{money(row.admissoes_p10)}</b> e <b>{money(row.admissoes_p90)}</b> por mês.</p>', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    k1.metric("Contratações", count(row.admissoes), help="Pessoas contratadas no período.")
    k2.metric("Saídas", count(row.desligamentos), help="Pessoas que saíram (demissão, fim de contrato, etc.) no período.")
    k3.metric("Saldo de vagas", count(row.diferenca_mov), help="Contratações menos saídas. Positivo = o mercado abriu mais vagas do que fechou.")

    st.subheader("Quanto pagam, por cargo")
    groups = caged_groups(package, geo, period, area, cargo)
    eligible = groups[groups.admissoes_validos.ge(MIN_N)].copy()
    if eligible.empty:
        st.info("Ainda não há dados suficientes para mostrar o salário por cargo aqui.")
    else:
        base = alt.Chart(eligible).encode(y=alt.Y("rotulo:N", title=None, sort=alt.SortField("admissoes_p50", order="descending")), tooltip=[alt.Tooltip("rotulo:N", title="Cargo"), alt.Tooltip("admissoes_validos:Q", title="Contratações"), alt.Tooltip("admissoes_p10:Q", title="Mais baixo (R$)", format=",.0f"), alt.Tooltip("admissoes_p50:Q", title="Típico (R$)", format=",.0f"), alt.Tooltip("admissoes_p90:Q", title="Mais alto (R$)", format=",.0f")])
        rule = base.mark_rule(strokeWidth=7, color=theme.FAIXA_PREENCHIMENTO).encode(x=alt.X("admissoes_p10:Q", title="Salário mensal (R$)", scale=alt.Scale(zero=True)), x2="admissoes_p90:Q")
        points = base.mark_point(filled=True, color=theme.LARANJA, size=65).encode(x="admissoes_p50:Q")
        chart((rule + points).properties(height=max(230, len(eligible) * 27)))
    st.caption("Cada barra vai do salário de entrada mais baixo ao mais alto que a maioria recebe. O ponto laranja é o valor típico.")

    table = package["emprego"]
    monthly = table[table.geo.eq(geo) & table.tipo.eq(kind) & table.categoria.eq(category) & table.periodo.ne("2025T1")].copy()
    if period != "2025T1":
        monthly = monthly[monthly.periodo.eq(period)]
    monthly["mes"] = monthly.periodo.map(PERIODS)
    left, right = st.columns(2)
    with left:
        st.subheader("Contratações e saídas, mês a mês")
        movement = monthly.melt(id_vars=["mes", "periodo"], value_vars=["admissoes", "desligamentos"], var_name="movimento", value_name="n")
        movement["movimento"] = movement.movimento.map({"admissoes": "Contratações", "desligamentos": "Saídas"})
        chart(alt.Chart(movement).mark_bar().encode(x=alt.X("mes:N", title=None, sort=list(PERIODS.values())[1:]), xOffset="movimento:N", y=alt.Y("n:Q", title="Pessoas", scale=alt.Scale(zero=True)), color=alt.Color("movimento:N", title=None, scale=alt.Scale(domain=["Contratações", "Saídas"], range=[theme.LARANJA, theme.NEUTRO_GRAFICO]), legend=alt.Legend(orient="top")), tooltip=["mes:N", "movimento:N", alt.Tooltip("n:Q", title="Pessoas")]).properties(height=260))
    with right:
        st.subheader("Salário de entrada ao longo dos meses")
        chart(alt.Chart(monthly).mark_line(point=True, color=theme.LARANJA).encode(x=alt.X("mes:N", sort=list(PERIODS.values())[1:], title=None), y=alt.Y("admissoes_p50:Q", title="Salário mensal (R$)", scale=alt.Scale(zero=True)), tooltip=["mes:N", alt.Tooltip("admissoes_p50:Q", title="Salário típico", format=",.0f")]).properties(height=260))
    if row.admissoes_validos >= MIN_N and row.desligamentos_validos >= MIN_N:
        st.subheader("Quem entra e quem sai")
        st.write(f"Quem é contratado entra ganhando por volta de {money_text(row.admissoes_p50)}. Quem sai recebia por volta de {money_text(row.desligamentos_p50)}. São pessoas diferentes — essa diferença **não** significa aumento de salário de quem fica.")
    with st.expander("Ver tabela com todos os números"):
        st.dataframe(rows.drop(columns=["geo", "tipo"]), hide_index=True, width="stretch")
    download("Baixar dados desta tela (CSV)", rows, "salarios_e_vagas.csv")


def distribution_chart(frame, field, title):
    selected = frame[frame.variavel.eq(field)].copy()
    st.subheader(title)
    if selected.empty:
        st.info("Base respondida insuficiente para esta distribuição.")
        return
    selected["rotulo"] = selected.categoria.str.replace("de R$ ", "", regex=False).str.replace("/mês", "", regex=False)
    order = list(selected.sort_values("ordem").rotulo) if field == "salario" else alt.SortField("n", order="descending")
    chart(alt.Chart(selected).mark_bar(color=theme.LARANJA).encode(y=alt.Y("rotulo:N", sort=order, title=None), x=alt.X("proporcao:Q", title="% das pessoas", axis=alt.Axis(format="%"), scale=alt.Scale(zero=True)), tooltip=[alt.Tooltip("categoria:N", title="Resposta"), alt.Tooltip("n:Q", title="Pessoas"), alt.Tooltip("proporcao:Q", format=".1%", title="% das pessoas")]).properties(height=max(260, len(selected)*25)))
    st.caption(f"Com base em {count(selected.denominador.iloc[0])} respostas.")


def profiles(package):
    st.header("Quem trabalha na área de dados")
    st.caption("A partir da pesquisa State of Data Brazil (2024-2025), respondida voluntariamente por profissionais no Brasil. As pessoas informam seus próprios dados.")
    pf1, pf2 = st.columns(2)
    with pf1:
        regions = ["Brasil", "Nordeste", "Pernambuco"]
        region = st.selectbox("Onde?", regions, key="p_regiao", on_change=clear_uf, args=("p_",), persist_state="session")
    with pf2:
        senior = st.selectbox("Nível de experiência", ["Todos", "Junior", "Pleno", "Senior", "Nao informado"], format_func=lambda v: {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(v, v), key="p_senior", persist_state="session")
    with st.expander("Mais opções (estado, modelo de trabalho)"):
        mm1, mm2 = st.columns(2)
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("p_uf") not in uf_options:
            st.session_state["p_uf"] = uf_options[0]
        uf = mm1.selectbox("Estado", uf_options, key="p_uf", disabled=region == "Pernambuco", persist_state="session")
        work = mm2.selectbox("Modelo de trabalho", ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"], format_func=lambda v: {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(v, v), key="p_modelo", persist_state="session")
        st.button("Restaurar filtros", icon=":material/restart_alt:", on_click=reset, args=("p_",), key="reset_profiles")
    geo = geography(region, uf)
    location = "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)
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
    c1.metric("Pessoas que responderam", count(row.n_respostas))
    c2.metric("Informaram o salário", count(row.n_salarios))
    c3.metric("Procurando emprego", percent(row.proporcao_ativa), help="Entre quem respondeu a essa pergunta, a parte que disse estar buscando uma nova vaga.")
    if row.n_respostas < MIN_N:
        st.warning(f"Há poucas respostas neste recorte (menos de {MIN_N}), então não mostramos os gráficos para não enganar. Tente um recorte mais amplo.")
        return
    left, right = st.columns(2)
    with left:
        distribution_chart(result["distribuicoes"], "salario", "Faixas de salário")
        st.caption("São faixas informadas pelas pessoas, não um salário exato.")
    with right:
        st.subheader("Tecnologias mais usadas")
        tech = result["tecnologias"].dropna(subset=["proporcao"])
        if tech.empty:
            st.info("Ainda não há respostas suficientes sobre tecnologias neste recorte.")
        else:
            chart(alt.Chart(tech).mark_bar(color=theme.LARANJA).encode(y=alt.Y("tecnologia:N", sort="-x", title=None), x=alt.X("proporcao:Q", title="% das pessoas", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")), tooltip=["tecnologia:N", alt.Tooltip("n:Q", title="Pessoas"), alt.Tooltip("proporcao:Q", title="% das pessoas", format=".1%")]).properties(height=300))
        st.caption("Cada pessoa pode usar várias tecnologias, então a soma passa de 100%.")
    left, right = st.columns(2)
    with left:
        distribution_chart(result["distribuicoes"], "formacao", "Formação")
    with right:
        distribution_chart(result["distribuicoes"], "vinculo", "Tipo de vínculo")
    download("Baixar distribuições agregadas", result["distribuicoes"], "perfis_distribuicoes.csv")


def models(package):
    st.header("Previsões")
    st.info("Aqui testamos, a título experimental, o quanto dá para **estimar** salário e intenção de troca de emprego a partir dos dados. Servem para dar uma ideia geral — **não** são uma calculadora para o seu caso.", icon=":material/science:")
    view = st.segmented_control("Análise", ["Estimar salário", "Quem procura emprego"], default="Estimar salário", required=True, key="modelo_visao", persist_state="session")
    if view == "Estimar salário":
        table = package["R1_teste_marco"]
        meta = package["metadata"]["modelos"]["regressao"]
        chosen = table[table.modelo.eq(meta["modelo_selecionado"])].iloc[0]
        st.caption("Testamos estimar o salário de entrada a partir de cargo, idade e região.")
        a, b = st.columns(2)
        a.metric("Erro médio da estimativa", money(chosen.mae), help="Em média, a estimativa fica distante do valor real por volta disso, para mais ou para menos.")
        b.metric("Quanto o modelo explica", f"{max(chosen.r2, 0)*100:.0f}%", help="De 0% a 100%: o quanto da variação de salário o modelo consegue captar. Quanto maior, melhor. Valores baixos mostram que salário depende de muita coisa além de cargo, idade e região.")
        st.write(f"**Na prática:** a estimativa erra, em média, cerca de {money_text(chosen.mae)} por mês. Por isso o Radar mostra **faixas** de salário, e não um número exato.")
        with st.expander("Detalhes técnicos (para quem é da área)"):
            st.caption(f"CAGED · treino jan-fev/2025 · teste reservado mar/2025 · n={count(meta['n_teste'])}. {int(chosen.previsoes_negativas)} previsões negativas mantidas na avaliação. Relações observacionais; idade não é experiência; uma linha é um evento, não uma pessoa acompanhada.")
            st.dataframe(table[["modelo", "n", "mae", "rmse", "r2", "previsoes_negativas"]], hide_index=True, width="stretch")
            st.image(str(PUBLIC / "R3_observado_previsto.png"), width="stretch")
            st.image(str(PUBLIC / "R4_residuos.png"), width="stretch")
        download("Baixar dados desta tela (CSV)", table, "estimativa_salario.csv")
        return
    meta = package["metadata"]["modelos"]["classificacao"]
    st.caption("Testamos adivinhar quem está querendo trocar de emprego a partir do perfil da pessoa.")
    names = {"logistica": "Regressão logística", "arvore": "Árvore simples", "majoritaria": "Modelo base"}
    key = st.selectbox("Modelo", list(names), format_func=names.get, key="classificador", persist_state="session", help="Comparação técnica entre modelos. Pode deixar no primeiro.")
    row = package["C1_metricas_teste"].set_index("modelo").loc[key]
    a, b, c, d = st.columns(4)
    a.metric("Acerto geral", percent(row.acuracia), help="De todas as pessoas, a parte que o modelo classificou corretamente.")
    b.metric("Precisão", percent(row.precisao), help="Quando o modelo diz 'está procurando', a parte das vezes em que acerta.")
    c.metric("Cobertura", percent(row.recall), help="De quem realmente estava procurando, quantos o modelo conseguiu encontrar.")
    d.metric("Nota combinada (F1)", f"{row.f1:.2f}", help="Equilíbrio entre precisão e cobertura, de 0 a 1.")
    st.warning(f"Na prática, o modelo deixa passar {int(row.fn)} de {int(row.n_ativos)} pessoas que estavam realmente procurando. Serve para enxergar grupos, não para prever uma pessoa.")
    matrix = pd.DataFrame([{"Observado": str(obs), "Previsto": str(pred), "n": int(row[field]), "taxa": row[field]/total} for obs, total, pair in [(0, row.tn+row.fp, [(0, "tn"), (1, "fp")]), (1, row.fn+row.tp, [(0, "fn"), (1, "tp")])] for pred, field in pair])
    with st.expander("Detalhes técnicos (para quem é da área)"):
        st.caption(f"State of Data · treino {count(meta['n_treino'])} · teste estratificado {count(meta['n_teste'])} · classe 1 = busca ativa · limiar 0,5. A logística foi escolhida por validação no treino; o seletor apenas compara resultados já calculados.")
        st.markdown(f"**ROC-AUC:** {row.roc_auc:.3f} · **Average Precision:** {row.average_precision:.3f} · **prevalência no teste:** {row.n_ativos/row.n:.3f}")
    st.subheader("Onde o modelo acerta e erra")
    base = alt.Chart(matrix).encode(x=alt.X("Previsto:N", title="O que o modelo achou", axis=alt.Axis(labelAngle=0)), y=alt.Y("Observado:N", title="O que era verdade"), tooltip=["Observado:N", "Previsto:N", "n:Q", alt.Tooltip("taxa:Q", format=".1%", title="Proporção na linha")])
    chart((base.mark_rect().encode(color=alt.Color("taxa:Q", scale=alt.Scale(domain=[0, 1], range=[theme.CINZA_CLARO, theme.GRAFITE]), legend=None)) + base.mark_text(fontSize=21).encode(text="n:Q", color=alt.condition(alt.datum.taxa > .5, alt.value(theme.BRANCO), alt.value(theme.TEXTO)))).properties(height=240))
    st.caption("Linhas = o que era verdade; colunas = o que o modelo achou. 0 = não procurava, 1 = procurava. Os maiores números deveriam ficar na diagonal (acertos).")
    left, right = st.columns(2)
    for column, dataset, x, y, title, x_title, y_title in [(left, "C4_curvas_roc", "taxa_falso_positivo", "taxa_verdadeiro_positivo", "Curva ROC (técnico)", "Taxa de falsos positivos", "Recall"), (right, "C5_curvas_precision_recall", "recall", "precisao", "Precisão × cobertura (técnico)", "Recall", "Precisão")]:
        with column:
            st.subheader(title)
            curves = package[dataset].copy()
            curves["classificador"] = curves.modelo.map(names)
            curves["ordem"] = curves.groupby("modelo").cumcount()
            chart(alt.Chart(curves).mark_line(interpolate="step-after" if dataset == "C5_curvas_precision_recall" else "linear").encode(x=alt.X(x+":Q", title=x_title, scale=alt.Scale(domain=[0, 1])), y=alt.Y(y+":Q", title=y_title, scale=alt.Scale(domain=[0, 1])), color=alt.Color("classificador:N", title=None, scale=alt.Scale(domain=list(names.values()), range=[theme.LARANJA, theme.GRAFITE, theme.NEUTRO_GRAFICO]), legend=alt.Legend(orient="bottom")), order="ordem:Q", tooltip=["classificador:N", alt.Tooltip(x+":Q", format=".3f"), alt.Tooltip(y+":Q", format=".3f")]).properties(height=270))
    st.caption("Mede intenção de troca hoje, não o que a pessoa fará no futuro. A pesquisa é voluntária, então pode não representar todo mundo.")
    download("Baixar dados desta tela (CSV)", package["C1_metricas_teste"], "quem_procura_emprego.csv")


def sources(package):
    st.header("De onde vêm os dados")
    st.caption("Transparência total: as fontes, o que cada uma cobre e o que elas não conseguem dizer.")
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
    st.caption("Regra do painel: só mostramos um número quando há pelo menos 30 respostas — abaixo disso, o dado fica instável e pode enganar. Versão dos dados: " + meta["preparado_em"][:10])
    st.link_button("Microdados MTE", "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged", icon=":material/open_in_new:")
    st.link_button("State of Data Brazil", "https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025", icon=":material/open_in_new:")
    st.download_button("Baixar manifesto público", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"), file_name="manifesto_publico.json", mime="application/json", icon=":material/download:")


SURVEY = AREA / "cesar_pesquisa_agregada.json"


def cesar_school(package):
    data = json.loads(SURVEY.read_text(encoding="utf-8"))
    st.header("Cesar School")
    st.write("O que a própria turma da CESAR School pensa sobre carreira em TI: onde as pessoas estão, quanto esperam ganhar e o que mais querem saber.")
    st.caption(f'{data["fonte"]} · n = {data["n"]}')
    k = data["kpis"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Respostas", count(data["n"]))
    c2.metric("Usariam a ferramenta", f'{k["usariam_n"]} de {data["n"]}', help="Responderam que usariam uma ferramenta de dados para ver vagas e tendências de TI.")
    c3.metric("Cogitaram desistir ou mudar", f'{k["cogitaram_n"]} de {data["n"]}', help="Nos últimos 12 meses, por falta de informação clara sobre salário e carreira.")
    c4, c5, c6 = st.columns(3)
    c4.metric("Expectativa salarial (mediana)", money(k["sal_mediana"]))
    c5.metric("Experiência (mediana)", f'{k["exp_mediana"]} meses')
    c6.metric("Buscando mudança agora", f'{k["buscando_n"]} de {data["n"]}')
    st.divider()
    blocos = data["blocos"]
    for i in range(0, len(blocos), 2):
        for col, bloco in zip(st.columns(2), blocos[i:i + 2]):
            with col:
                st.subheader(bloco["titulo"])
                frame = pd.DataFrame(bloco["itens"])
                order = list(frame["rotulo"]) if bloco.get("ordinal") else "-x"
                bars = alt.Chart(frame).mark_bar(color=theme.LARANJA).encode(
                    y=alt.Y("rotulo:N", sort=order, title=None),
                    x=alt.X("n:Q", title="Respostas", axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip("rotulo:N", title="Resposta"), alt.Tooltip("n:Q", title="Respostas")],
                ).properties(height=max(170, len(frame) * 30))
                chart(bars)
                if bloco.get("nota"):
                    st.caption(bloco["nota"].replace("$", "\\$"))
    st.divider()
    st.caption("Apenas dados agregados; nenhuma resposta individual é exibida. Amostra pequena de conveniência (uma turma da CESAR School), não representa o mercado de TI nem a escola como um todo.")


try:
    signature = (PUBLIC / "manifesto.json").stat().st_mtime_ns
    package = cached_package(signature)
except (PackageError, OSError):
    st.error("Pacote público indisponível ou com integridade inválida. Nenhuma análise foi carregada.")
    st.stop()

LABELS = {
    "Salários e vagas": employment,
    "Quem trabalha na área": profiles,
    "Previsões": models,
    "Cesar School": cesar_school,
    "Sobre os dados": sources,
}
st.markdown('<p class="ajuda">👇 Escolha o que você quer ver:</p>', unsafe_allow_html=True)
view = st.segmented_control("Seções", list(LABELS), default="Salários e vagas", required=True, key="visao", label_visibility="collapsed")
LABELS[view](package)
st.divider()
st.caption("Radar de carreiras · dados oficiais do mercado de TI (Novo CAGED e State of Data) · cada fonte é analisada separadamente")

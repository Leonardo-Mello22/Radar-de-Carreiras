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
from dados import MIN_N, PackageError, caged_groups, caged_query, export_csv, geography, load_expansion, occupation, profile_query

PUBLIC = AREA / "dados_ampliados"
st.set_page_config(page_title="Radar de carreiras", page_icon=":material/radar:", layout="wide")
st.markdown(f"""<style>
 .stApp {{background:{theme.BRANCO}; color:{theme.TEXTO};}}
 header[data-testid="stHeader"], #MainMenu, footer {{display:none; visibility:hidden;}}
 .block-container {{max-width:1200px; padding-top:.6rem; padding-bottom:3rem;}}
 h1,h2,h3,p,label,button,div {{letter-spacing:0 !important;}}

 /* ---------- HERO ---------- */
 .hero-fig {{position:relative; overflow:hidden; border-radius:22px; margin:6px 0 14px;
   background:linear-gradient(100deg,#16181D 0%,#1E1A16 55%,#33210F 100%); color:#fff; padding:32px 38px 38px;}}
 .hero-fig .brandrow {{display:flex; align-items:center; gap:13px; font-weight:800; font-size:20px; color:#fff; position:relative; z-index:1;}}
 .hero-fig .pill {{margin-left:auto; padding:7px 13px; border:1px solid #5A5E66; border-radius:20px;
   color:{theme.TEXTO_SOBRE_ESCURO}; font-size:12px; font-weight:600; letter-spacing:.5px;}}
 .hero-fig .kicker {{color:{theme.LARANJA}; font-size:13px; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-top:40px; position:relative; z-index:1;}}
 .hero-fig h1 {{color:#fff !important; font-size:clamp(29px,4vw,46px); font-weight:800; line-height:1.08; letter-spacing:-.02em; margin:12px 0 12px; max-width:720px; position:relative; z-index:1;}}
 .hero-fig .sub {{color:{theme.TEXTO_SOBRE_ESCURO}; font-size:17px; line-height:1.5; max-width:650px; position:relative; z-index:1;}}

 /* ---------- NAV (abas) ---------- */
 .ajuda {{font-size:13px; color:{theme.TEXTO_SECUNDARIO}; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin:4px 0 8px;}}
 /* seletor interno (ex.: Previsões) — pílulas simples */
 [data-testid="stButtonGroup"] {{gap:7px; margin-bottom:12px;}}
 [data-testid="stButtonGroup"] button {{min-height:44px; border-radius:10px !important;}}
 [data-testid="stButtonGroup"] button p {{font-weight:700 !important;}}
 [data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind="primary"] {{background:{theme.LARANJA_CLARO} !important; border-color:{theme.LARANJA} !important;}}
 [data-testid="stButtonGroup"] button[aria-checked="true"] p, [data-testid="stButtonGroup"] button[kind="primary"] p {{color:{theme.LARANJA_ESCURO_TEXTO} !important;}}

 /* ---------- NAVEGAÇÃO PRINCIPAL (abas numeradas) ---------- */
 div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-navtab_"]) {{gap:0 !important; border-bottom:1px solid {theme.BORDA_CLARA}; margin-bottom:20px;}}
 div[class*="st-key-navtab_"] button {{width:100% !important; min-height:66px; border:0 !important; border-radius:0 !important; border-bottom:3px solid transparent !important; background:transparent !important; justify-content:flex-start !important; padding:10px 16px !important; box-shadow:none !important;}}
 div[class*="st-key-navtab_"] button p {{font-size:16px !important; font-weight:700 !important; color:{theme.TEXTO_SECUNDARIO} !important; text-align:left;}}
 div[class*="st-key-navtab_"] button p::before {{display:block; font-size:11px; font-weight:700; letter-spacing:.04em; color:{theme.TEXTO_TERCIARIO}; margin-bottom:5px;}}
 div.st-key-navtab_0 button p::before {{content:"01";}}
 div.st-key-navtab_1 button p::before {{content:"02";}}
 div.st-key-navtab_2 button p::before {{content:"03";}}
 div.st-key-navtab_3 button p::before {{content:"04";}}
 div.st-key-navtab_4 button p::before {{content:"05";}}
 div[class*="st-key-navtab_"] button:hover {{background:{theme.CINZA_CLARO} !important;}}
 div[class*="st-key-navtab_"] button[kind="primary"] {{background:{theme.LARANJA_CLARO} !important; border-bottom:3px solid {theme.LARANJA} !important;}}
 div[class*="st-key-navtab_"] button[kind="primary"] p {{color:{theme.GRAFITE} !important;}}
 div[class*="st-key-navtab_"] button[kind="primary"] p::before {{color:{theme.LARANJA};}}

 /* ---------- Títulos de seção ---------- */
 h2 {{font-size:clamp(25px,3vw,33px) !important; font-weight:800 !important; color:{theme.GRAFITE}; padding-top:.4rem !important;}}
 h3 {{font-size:19px !important; font-weight:800 !important; color:{theme.GRAFITE};}}

 /* ---------- Resposta em destaque ---------- */
 .answer-fig {{display:grid; grid-template-columns:1.15fr .85fr; gap:40px; align-items:center;
   background:{theme.LARANJA_CLARO}; border:1px solid {theme.FAIXA_PREENCHIMENTO}; border-left:6px solid {theme.LARANJA};
   border-radius:18px; padding:26px 30px; margin:6px 0 22px;}}
 .answer-fig .lbl {{color:{theme.LARANJA_ESCURO_TEXTO}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;}}
 .answer-fig .big {{color:{theme.LARANJA}; font-size:clamp(42px,5vw,58px); font-weight:800; line-height:1; margin:6px 0 6px;}}
 .answer-fig .big small {{font-size:20px; color:{theme.TEXTO_SECUNDARIO}; font-weight:600;}}
 .answer-fig .faixa {{font-size:16px; color:{theme.TEXTO}; line-height:1.5;}}
 .answer-fig .faixa b {{color:{theme.GRAFITE};}}
 .answer-fig .track-wrap {{border-left:1px solid {theme.FAIXA_PREENCHIMENTO}; padding-left:30px;}}
 .answer-fig .tlabels {{display:flex; justify-content:space-between; font-size:11px; color:{theme.TEXTO_SECUNDARIO};}}
 .answer-fig .tlabels span:nth-child(2) {{text-align:center;}} .answer-fig .tlabels span:last-child {{text-align:right;}}
 .answer-fig .tlabels b {{color:{theme.TEXTO}; font-size:13px; display:block;}}
 .answer-fig .track {{position:relative; height:13px; border-radius:10px; background:{theme.FAIXA_PREENCHIMENTO}; margin:10px 0 8px;}}
 .answer-fig .track i {{position:absolute; top:50%; width:20px; height:20px; border:4px solid #fff; border-radius:50%;
   background:{theme.LARANJA}; box-shadow:0 2px 5px rgba(0,0,0,.14); transform:translate(-50%,-50%);}}
 .answer-fig .src {{color:{theme.TEXTO_TERCIARIO}; font-size:12px; margin-top:8px;}}

 /* ---------- KPI (metric) como card ---------- */
 [data-testid="stMetric"] {{background:#fff; border:1px solid {theme.BORDA_CLARA}; border-radius:14px; padding:16px 18px; min-width:0;}}
 [data-testid="stMetricValue"] {{font-size:30px !important; font-weight:800 !important; color:{theme.GRAFITE}; overflow-wrap:anywhere; white-space:normal;}}
 [data-testid="stMetricLabel"] p {{font-size:14px !important; font-weight:600 !important; color:{theme.TEXTO_SECUNDARIO} !important;}}

 /* ---------- selects e expanders ---------- */
 .stSelectbox label {{font-size:14px !important; font-weight:700 !important; color:{theme.TEXTO_SECUNDARIO} !important; text-transform:lowercase;}}
 .stSelectbox .react-aria-ComboBox [role="group"] {{border-radius:12px !important; min-height:56px !important; border:1px solid {theme.BORDA_CLARA} !important; background:#fff !important;}}
 .stSelectbox input[role="combobox"] {{font-size:16px !important; font-weight:700 !important; color:{theme.GRAFITE} !important; padding-left:14px !important;}}
 .stSelectbox input[role="combobox"]::placeholder {{color:{theme.TEXTO_TERCIARIO}; font-weight:600;}}
 .stSelectbox button[aria-haspopup="listbox"] svg {{color:{theme.TEXTO_SECUNDARIO};}}
 div.st-key-filtros .stSelectbox .react-aria-ComboBox [role="group"], div.st-key-filtros_perfil .stSelectbox .react-aria-ComboBox [role="group"] {{box-shadow:0 1px 2px rgba(0,0,0,.04);}}
 div.st-key-filtros, div.st-key-filtros_perfil {{background:{theme.CINZA_CLARO}; border:1px solid {theme.BORDA_CLARA}; border-radius:18px; padding:20px 22px 22px; margin-bottom:24px;}}
 div.st-key-filtros hr, div.st-key-filtros_perfil hr {{margin:14px 0; border-color:{theme.BORDA_CLARA};}}
 div[data-testid="stExpander"] {{border:1px solid {theme.BORDA_CLARA} !important; border-radius:14px !important;}}
 div[data-testid="stExpander"] summary p {{font-weight:700;}}
 [data-testid="stVerticalBlock"] {{gap:.8rem;}}
 [data-testid="stCaptionContainer"] {{color:{theme.TEXTO_TERCIARIO}; font-size:12px;}}
 [data-testid="stDownloadButton"] button {{min-height:46px; border-radius:12px !important; border:1px solid {theme.GRAFITE} !important; font-weight:700;}}

 /* ---------- rodapé ---------- */
 .footer-fig {{background:{theme.GRAFITE}; color:{theme.TEXTO_SOBRE_ESCURO}; border-radius:16px; padding:22px 26px;
   margin-top:28px; display:flex; justify-content:space-between; align-items:center; gap:22px; flex-wrap:wrap; font-size:12.5px;}}
 .footer-fig .fb {{display:flex; align-items:center; gap:12px;}}
 .footer-fig strong {{color:#fff; display:block;}}

 /* ---------- page intro ---------- */
 .pintro {{margin:2px 0 20px;}}
 .pintro .eyebrow {{color:{theme.LARANJA}; font-size:13px; font-weight:700; letter-spacing:.11em; text-transform:uppercase;}}
 .pintro h2 {{margin:8px 0 9px; font-size:clamp(25px,3vw,35px) !important; font-weight:800 !important; letter-spacing:-.02em; color:{theme.GRAFITE};}}
 .pintro p {{color:{theme.TEXTO_SECUNDARIO}; font-size:16px; line-height:1.5; max-width:720px;}}

 /* ---------- survey hero (Cesar) ---------- */
 .survey-hero {{display:grid; grid-template-columns:1fr 1fr 1.15fr; gap:14px; margin:6px 0 18px;}}
 .survey-hero article {{min-height:195px; padding:23px; border:1px solid {theme.BORDA_CLARA}; border-radius:14px; background:{theme.CINZA_CLARO}; display:flex; flex-direction:column;}}
 .survey-hero article > span {{color:{theme.TEXTO_SECUNDARIO}; font-size:13px; font-weight:600;}}
 .survey-hero article > strong {{display:block; margin:22px 0 10px; color:{theme.LARANJA}; font-size:48px; font-weight:800; line-height:1;}}
 .survey-hero article > p {{color:{theme.TEXTO_SECUNDARIO}; line-height:1.45; font-size:15px;}}
 .survey-hero .salary {{background:linear-gradient(90deg,#FF7200 0%,#E05F00 100%); border-color:transparent;}}
 .survey-hero .salary > span, .survey-hero .salary > p {{color:#fff;}}
 .survey-hero .salary > strong {{color:#fff; font-size:43px;}}

 /* ---------- simple bars ---------- */
 .simple-bars {{display:flex; flex-direction:column; gap:14px;}}
 .sbar {{display:grid; grid-template-columns:155px 1fr 52px; align-items:center; gap:12px; font-size:13px;}}
 .sbar > span {{color:{theme.TEXTO_SECUNDARIO};}}
 .sbar .trk {{height:11px; border-radius:10px; background:{theme.TRILHO_GRAFICO};}}
 .sbar .trk i {{display:block; height:11px; border-radius:10px; background:{theme.NEUTRO_GRAFICO};}}
 .sbar .trk i.hl {{background:{theme.LARANJA};}}
 .sbar strong {{text-align:right; color:{theme.GRAFITE};}}

 /* ---------- panel (figma) ---------- */
 .panel-fig {{padding:24px; border:1px solid {theme.BORDA_CLARA}; border-radius:18px; background:#fff; margin-bottom:16px;}}
 .panel-fig .ph .eyebrow {{color:{theme.LARANJA}; font-size:12px; font-weight:700; letter-spacing:.09em; text-transform:uppercase;}}
 .panel-fig .ph h3 {{margin:4px 0 18px; font-size:21px !important; font-weight:800 !important;}}

 .transp {{margin:16px 0 4px; padding:14px 17px; border-radius:12px; background:{theme.CINZA_CLARO}; color:{theme.TEXTO_SECUNDARIO}; font-size:13px; text-align:center;}}

 /* ---------- previsões ---------- */
 .experiment {{margin:4px 0 18px; padding:16px 19px; border-left:4px solid {theme.LARANJA}; border-radius:10px; background:{theme.LARANJA_CLARO}; color:{theme.LARANJA_ESCURO_TEXTO};}}
 .experiment strong {{font-size:16px;}} .experiment p {{margin-top:3px; line-height:1.5;}}
 .prediction {{padding:40px; border:1px solid {theme.FAIXA_PREENCHIMENTO}; border-radius:18px; background:{theme.LARANJA_CLARO}; text-align:center; margin-bottom:16px;}}
 .prediction .eyebrow {{color:{theme.LARANJA}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.09em;}}
 .prediction .val {{margin:10px 0 0; color:{theme.LARANJA}; font-size:clamp(46px,6vw,64px); font-weight:800; line-height:1;}}
 .prediction h3 {{margin:6px 0 10px; font-size:22px !important;}}
 .prediction p {{color:{theme.TEXTO_SECUNDARIO}; font-size:16px; max-width:560px; margin:0 auto;}}
 .outlook-fig {{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:22px 24px; border:1px solid {theme.BORDA_CLARA}; border-radius:18px; background:#fff;}}
 .outlook-fig .eyebrow {{color:{theme.LARANJA}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.09em;}}
 .outlook-fig h3 {{margin:4px 0 0; font-size:20px !important;}}
 .outlook-fig p {{color:{theme.TEXTO_SECUNDARIO}; margin-top:6px;}}
 .outlook-pill {{display:flex; align-items:center; gap:8px; padding:10px 15px; border-radius:20px; background:{theme.CINZA_CLARO}; color:{theme.TEXTO_SECUNDARIO}; font-size:13px; font-weight:700; white-space:nowrap;}}
 .outlook-pill i {{width:9px; height:9px; border-radius:50%; background:{theme.LARANJA};}}

 /* ---------- source cards (Sobre os dados) ---------- */
 .sources-list {{display:flex; flex-direction:column; gap:14px;}}
 .source-card {{display:grid; grid-template-columns:60px 1fr; gap:20px; padding:24px; border:1px solid {theme.BORDA_CLARA}; border-radius:18px; background:#fff;}}
 .source-card .num {{color:{theme.BORDA_CLARA}; font-size:38px; font-weight:800; line-height:1;}}
 .source-tag {{display:inline-block; padding:5px 9px; border-radius:20px; background:{theme.LARANJA_CLARO}; color:{theme.LARANJA_ESCURO_TEXTO}; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;}}
 .source-card h3 {{margin:9px 0 7px; font-size:22px !important;}}
 .source-card p {{color:{theme.TEXTO_SECUNDARIO}; line-height:1.5;}}
 .doesnt-cover {{margin:14px 0; padding:11px 14px; border-radius:10px; background:{theme.CINZA_CLARO}; color:{theme.TEXTO_SECUNDARIO}; font-size:13px;}}
 .doesnt-cover strong {{margin-right:10px; color:{theme.GRAFITE};}}
 .source-card a {{color:{theme.LARANJA_ESCURO_TEXTO}; font-size:13px; font-weight:700; text-decoration:none;}}
 .source-local {{color:{theme.TEXTO_TERCIARIO}; font-size:12px;}}
 .privacy-panel {{display:flex; align-items:center; gap:22px; margin-top:18px; padding:26px; border-radius:18px; background:{theme.GRAFITE};}}
 .privacy-panel .eyebrow {{color:{theme.LARANJA}; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.09em;}}
 .privacy-panel h3 {{margin:5px 0 7px; color:#fff !important; font-size:21px !important;}}
 .privacy-panel p {{color:{theme.TEXTO_SOBRE_ESCURO}; line-height:1.5;}}

 /* ---------- compact answer (profiles) ---------- */
 .answer-compact {{display:flex; justify-content:space-between; align-items:flex-end; gap:30px; flex-wrap:wrap; background:{theme.LARANJA_CLARO}; border:1px solid {theme.FAIXA_PREENCHIMENTO}; border-left:6px solid {theme.LARANJA}; border-radius:18px; padding:24px 30px; margin:6px 0 18px;}}
 .answer-compact .lbl {{color:{theme.LARANJA_ESCURO_TEXTO}; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;}}
 .answer-compact .big {{color:{theme.LARANJA}; font-size:44px; font-weight:800; line-height:1; margin:6px 0 6px;}}
 .answer-compact .big small {{font-size:18px; color:{theme.TEXTO_SECUNDARIO}; font-weight:600;}}
 .answer-compact .faixa {{font-size:15px; color:{theme.TEXTO};}}
 .answer-compact .src {{color:{theme.TEXTO_TERCIARIO}; font-size:12px;}}
 @media(max-width:760px) {{ .survey-hero {{grid-template-columns:1fr;}} }}

 @media(max-width:760px) {{
  .block-container {{padding:.6rem .9rem 2rem;}}
  .answer-fig {{grid-template-columns:1fr; gap:20px;}}
  .answer-fig .track-wrap {{border-left:0; padding-left:0; border-top:1px solid {theme.FAIXA_PREENCHIMENTO}; padding-top:16px;}}
 }}
 </style>""", unsafe_allow_html=True)

st.markdown(f'''<div class="hero-fig">
  {theme.aro_marca_dagua(430, 0.13)}
  <div class="brandrow">{theme.aro_svg(30)}<span>Radar de Carreiras</span><span class="pill">CESAR School</span></div>
  <div class="kicker">Projeto 5 · Ciência da Computação</div>
  <h1>Decisões de carreira começam com referências mais claras.</h1>
  <div class="sub">Salários e vagas de TI explicados de forma simples, com dados oficiais.</div>
</div>''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_package(signature):
    return load_expansion(PUBLIC)


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


def category_axis(field, order):
    return alt.Y(f"{field}:N", title=None, sort=order, axis=alt.Axis(labelOverlap=False))


def reset(prefix):
    defaults = {"c_regiao": "Pernambuco", "c_uf": "PE", "c_periodo": "todos", "c_area": "Todas", "c_cargo": "Todos",
                "p_regiao": "Brasil", "p_uf": "Todas", "p_senior": "Todos", "p_modelo": "Todos", "p_edicao": "2025/2026"}
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
    st.markdown('<div class="pintro"><span class="eyebrow">salários e oportunidades</span>'
                '<h2>Quanto pagam, e onde tem vaga?</h2>'
                '<p>Admissões e desligamentos formais em TI de janeiro de 2025 a setembro de 2026. Salários em valores de março de 2025, corrigidos pelo IPCA.</p></div>',
                unsafe_allow_html=True)

    catalog = package["metadata"]["catalogo"]
    periods = package["metadata"]["periodos"]
    labels = {key: value["rotulo"] for key, value in periods.items()}
    area_atual = st.session_state.get("c_area", "Todas")
    occupations = {v["categoria"]: v["rotulo"] for v in catalog if v["tipo"] == "cargo" and (area_atual == "Todas" or v["area"] == area_atual)}

    with st.container(key="filtros"):
        f1, f2 = st.columns([1.5, 1])
        with f1:
            options = ["Todos", *occupations]
            if st.session_state.get("c_cargo") not in options:
                st.session_state["c_cargo"] = "Todos"
            cargo = st.selectbox("qual cargo?", options, format_func=lambda v: occupations.get(v, "Todos os cargos"), key="c_cargo", persist_state="session")
        with f2:
            regions = ["Pernambuco", "Nordeste", "Brasil"]
            region = st.selectbox("onde?", regions, key="c_regiao", on_change=clear_uf, args=("c_",), persist_state="session")
        st.divider()
        m1, m2, m3 = st.columns(3)
        period = m1.selectbox("período", list(periods), format_func=labels.get, key="c_periodo", persist_state="session")
        areas = ["Todas", *[v["categoria"] for v in catalog if v["tipo"] == "area"]]
        area = m2.selectbox("área", areas, key="c_area", persist_state="session")
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("c_uf") not in uf_options:
            st.session_state["c_uf"] = uf_options[0]
        uf = m3.selectbox("estado", uf_options, key="c_uf", disabled=region == "Pernambuco", persist_state="session")
        st.button("Limpar filtros", icon=":material/restart_alt:", key="reset_caged", on_click=reset, args=("c_",))

    geo = geography(region, uf)
    location = "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)
    kind, category = occupation(area, cargo)
    rows = caged_query(package, geo, period, kind, category)
    if rows.empty or rows.iloc[0].n_eventos == 0:
        st.info("Não encontramos movimentações para essa combinação de filtros.")
        return
    row = rows.iloc[0]
    cargo_label = occupations[cargo] if cargo != "Todos" else "TI em geral"
    st.caption(f"{labels[period]} · {location} · {cargo_label}")

    if row.admissoes_validos < MIN_N:
        st.markdown(f"**Salário típico de entrada · {cargo_label} · {location}**")
        st.warning(f"Há poucos dados de salário aqui (menos de {MIN_N} contratações), então não mostramos o valor para não enganar. Experimente 'Todos os cargos' ou uma região maior.")
    else:
        pct = max(6, min(94, (row.admissoes_p50 - row.admissoes_p10) / max(row.admissoes_p90 - row.admissoes_p10, 1) * 100))
        st.markdown(f'''<div class="answer-fig">
  <div>
    <div class="lbl">Salário típico de entrada · {cargo_label} · {location}</div>
    <div class="big">{money(row.admissoes_p50)}<small> /mês</small></div>
    <div class="faixa">Os 80% centrais dos salários válidos vão de <b>{money(row.admissoes_p10)}</b> a <b>{money(row.admissoes_p90)}</b> por mês.</div>
  </div>
  <div class="track-wrap">
    <div class="tlabels"><span>menor<br><b>{money(row.admissoes_p10)}</b></span><span>típico<br><b>{money(row.admissoes_p50)}</b></span><span>maior<br><b>{money(row.admissoes_p90)}</b></span></div>
    <div class="track"><i style="left:{pct:.0f}%"></i></div>
    <div class="src">Fonte: Novo CAGED · n = {count(row.admissoes_validos)} contratações</div>
  </div>
</div>''', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    k1.metric("Contratações", count(row.admissoes), help="Eventos de admissão, não pessoas únicas nem vagas abertas.")
    k2.metric("Saídas", count(row.desligamentos), help="Eventos de desligamento no período.")
    k3.metric("Diferença de movimentos", count(row.diferenca_mov), help="Admissões menos desligamentos nos arquivos MOV, sem os ajustes do saldo oficial.")

    st.subheader("Quanto pagam, por cargo")
    groups = caged_groups(package, geo, period, area, cargo)
    eligible = groups[groups.admissoes_validos.ge(MIN_N)].copy()
    if eligible.empty:
        st.info("Ainda não há dados suficientes para mostrar o salário por cargo aqui.")
    else:
        base = alt.Chart(eligible).encode(y=category_axis("rotulo", alt.SortField("admissoes_p50", order="descending")), tooltip=[alt.Tooltip("rotulo:N", title="Cargo ou área"), alt.Tooltip("admissoes_validos:Q", title="Contratações"), alt.Tooltip("admissoes_p10:Q", title="Mais baixo (R$)", format=",.0f"), alt.Tooltip("admissoes_p50:Q", title="Típico (R$)", format=",.0f"), alt.Tooltip("admissoes_p90:Q", title="Mais alto (R$)", format=",.0f")])
        rule = base.mark_rule(strokeWidth=7, color=theme.FAIXA_PREENCHIMENTO).encode(x=alt.X("admissoes_p10:Q", title="Salário mensal (R$)", scale=alt.Scale(zero=True)), x2="admissoes_p90:Q")
        points = base.mark_point(filled=True, color=theme.LARANJA, size=65).encode(x="admissoes_p50:Q")
        chart((rule + points).properties(height=alt.Step(34)))
    st.caption("A barra cobre os percentis 10 a 90 dos salários válidos. O ponto laranja é a mediana.")

    table = package["emprego"]
    months = periods[period]["meses"]
    month_labels = [labels[month] for month in months]
    monthly = table[table.geo.eq(geo) & table.tipo.eq(kind) & table.categoria.eq(category) & table.periodo.isin(months)].copy()
    monthly["mes"] = monthly.periodo.map(labels)
    st.subheader("Contratações e saídas, mês a mês")
    movement = monthly.melt(id_vars=["mes"], value_vars=["admissoes", "desligamentos"], var_name="movimento", value_name="n")
    movement["movimento"] = movement.movimento.map({"admissoes": "Contratações", "desligamentos": "Saídas"})
    movement_order = ["Contratações", "Saídas"]
    chart(alt.Chart(movement).mark_bar().encode(
        x=alt.X("n:Q", title="Movimentações", scale=alt.Scale(zero=True), axis=alt.Axis(tickCount=8)),
        y=category_axis("mes", month_labels),
        yOffset=alt.YOffset("movimento:N", sort=movement_order),
        color=alt.Color("movimento:N", title=None,
                        scale=alt.Scale(domain=movement_order, range=[theme.LARANJA, theme.NEUTRO_GRAFICO]),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("mes:N", title="Mês"), alt.Tooltip("movimento:N", title="Movimento"),
                 alt.Tooltip("n:Q", title="Movimentações")],
    ).properties(height=max(170, len(month_labels) * 50)))

    st.subheader("Salário de entrada ao longo dos meses")
    salary = alt.Chart(monthly).encode(
        x=alt.X("mes:N", sort=month_labels, title=None, axis=alt.Axis(labelAngle=-45, labelOverlap="greedy")),
        y=alt.Y("admissoes_p50:Q", title="Salário mensal (R$)", scale=alt.Scale(zero=True),
                axis=alt.Axis(tickCount=8, labelOverlap=False)),
        tooltip=[alt.Tooltip("mes:N", title="Mês"), alt.Tooltip("admissoes_p50:Q", title="Salário típico", format=",.0f")],
    )
    valid_months = int(monthly.admissoes_p50.notna().sum())
    if valid_months == 0:
        st.info("Nenhum mês do recorte tem salários suficientes para calcular a mediana.")
    else:
        if valid_months == 1:
            salary = salary.mark_point(color=theme.LARANJA, filled=True, size=70)
        else:
            salary = salary.mark_line(color=theme.LARANJA, point=False)
        chart(salary.properties(height=330))
    if row.admissoes_validos >= MIN_N and row.desligamentos_validos >= MIN_N:
        st.subheader("Quem entra e quem sai")
        st.write(f"A mediana de entrada é {money_text(row.admissoes_p50)}. A mediana dos desligamentos é {money_text(row.desligamentos_p50)}. São grupos de eventos: não acompanhamos o salário da mesma pessoa.")
    with st.expander("Comparar janeiro a setembro de 2025 e 2026"):
        comparable = pd.concat([caged_query(package, geo, key, kind, category) for key in ("2025YTD", "2026YTD")])
        comparable["periodo"] = comparable.periodo.map(labels)
        st.dataframe(comparable[["periodo", "admissoes", "desligamentos", "admissoes_p50"]].rename(columns={
            "periodo": "Período", "admissoes": "Contratações", "desligamentos": "Saídas", "admissoes_p50": "Mediana de entrada (R$)",
        }), hide_index=True)
        st.caption("Mesmo cargo e local, com nove meses em cada ano.")
    download("Baixar dados desta tela (CSV)", rows, "salarios_e_vagas.csv")


EDUCATION_LABELS = {
    "Não tenho graduação formal": "Sem graduação",
    "Estudante de Graduação": "Graduando",
    "Graduação/Bacharelado": "Graduação",
    "Pós-graduação": "Especialização",
    "Mestrado": "Mestrado",
    "Doutorado ou Phd": "Doutorado",
    "Prefiro não informar": "Não informado",
}
EMPLOYMENT_LABELS = {
    "Estagio": "Estágio", "Servidor publico": "Servidor público",
    "Academico ou pesquisador": "Acadêmico / pesquisa", "Nao informado": "Não informado",
}


def distribution_chart(frame, field, title):
    selected = frame[frame.variavel.eq(field)].copy()
    st.subheader(title)
    if selected.empty:
        st.info("Base respondida insuficiente para esta distribuição.")
        return
    order = alt.SortField("n", order="descending")
    if field == "salario":
        selected["rotulo"] = selected.categoria.str.replace("de R$ ", "", regex=False).str.replace("/mês", "", regex=False)
        order = list(selected.sort_values("ordem").rotulo)
    else:
        aliases = EDUCATION_LABELS if field == "formacao" else EMPLOYMENT_LABELS
        selected["rotulo"] = selected.categoria.replace(aliases)
        if field == "formacao":
            education_order = list(EDUCATION_LABELS.values())
            present = selected.rotulo.unique()
            order = [label for label in education_order if label in present]
            order.extend(label for label in present if label not in education_order)
    bars = alt.Chart(selected).mark_bar(color=theme.LARANJA).encode(
        y=category_axis("rotulo", order),
        x=alt.X("proporcao:Q", title="% das pessoas", axis=alt.Axis(format="%"), scale=alt.Scale(zero=True)),
        tooltip=[alt.Tooltip("rotulo:N", title="Categoria"), alt.Tooltip("categoria:N", title="Resposta original"),
                 alt.Tooltip("n:Q", title="Pessoas"), alt.Tooltip("proporcao:Q", format=".1%", title="% das pessoas")],
    )
    if field == "formacao":
        bars = bars.encode(color=alt.condition(alt.datum.rotulo == "Especialização",
                                              alt.value(theme.LARANJA), alt.value(theme.NEUTRO_GRAFICO)))
    chart(bars.properties(height=alt.Step(31)))
    st.caption(f"Com base em {count(selected.denominador.iloc[0])} respostas.")


def profiles(package):
    st.markdown('<div class="pintro"><span class="eyebrow">retrato da área</span>'
                '<h2>Como é o perfil de quem responde à pesquisa?</h2>'
                '<p>Salários, experiência e ferramentas no State of Data Brazil. As edições são amostras voluntárias diferentes.</p></div>',
                unsafe_allow_html=True)
    with st.container(key="filtros_perfil"):
        editions = package["metadata"]["edicoes"]
        edition = st.selectbox("edição da pesquisa", list(editions), key="p_edicao", persist_state="session")
        pf1, pf2 = st.columns(2)
        with pf1:
            regions = ["Brasil", "Nordeste", "Pernambuco"]
            region = st.selectbox("onde?", regions, key="p_regiao", on_change=clear_uf, args=("p_",), persist_state="session")
        with pf2:
            levels = ["Todos", "Junior", "Pleno", "Senior", "Nao informado"]
            if edition == "2025/2026":
                levels.insert(4, "Especialista/Staff+")
            if st.session_state.get("p_senior") not in levels:
                st.session_state["p_senior"] = "Todos"
            senior = st.selectbox("nível de experiência", levels, format_func=lambda v: {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(v, v), key="p_senior", persist_state="session")
        st.divider()
        mm1, mm2 = st.columns(2)
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("p_uf") not in uf_options:
            st.session_state["p_uf"] = uf_options[0]
        uf = mm1.selectbox("estado", uf_options, key="p_uf", disabled=region == "Pernambuco", persist_state="session")
        work = mm2.selectbox("modelo de trabalho", ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"], format_func=lambda v: {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(v, v), key="p_modelo", persist_state="session")
        st.button("Limpar filtros", icon=":material/restart_alt:", key="reset_perfis", on_click=reset, args=("p_",))
    geo = geography(region, uf)
    location = "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)
    result = profile_query(package, geo, senior, work, edition)
    st.subheader(location)
    senior_label = {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(senior, senior)
    work_label = {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(work, work)
    st.caption(f"Edição {edition} · Coleta: {editions[edition]['coleta']} · Senioridade: {senior_label} · Trabalho: {work_label}")
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
    distribution_chart(result["distribuicoes"], "salario", "Faixas de salário")
    st.caption("São faixas informadas pelas pessoas, não um salário exato.")
    st.subheader("Tecnologias mais usadas")
    tech = result["tecnologias"].dropna(subset=["proporcao"])
    if tech.empty:
        st.info("Ainda não há respostas suficientes sobre tecnologias neste recorte.")
    else:
        chart(alt.Chart(tech).mark_bar(color=theme.LARANJA).encode(
            y=category_axis("tecnologia", "-x"),
            x=alt.X("proporcao:Q", title="% das pessoas", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%")),
            tooltip=["tecnologia:N", alt.Tooltip("n:Q", title="Pessoas"), alt.Tooltip("proporcao:Q", title="% das pessoas", format=".1%")],
        ).properties(height=alt.Step(31)))
    st.caption("Múltiplas escolhas; a base de respostas válidas varia por tecnologia.")
    distribution_chart(result["distribuicoes"], "formacao", "Formação")
    distribution_chart(result["distribuicoes"], "vinculo", "Tipo de vínculo")
    download("Baixar distribuições agregadas", result["distribuicoes"], "perfis_distribuicoes.csv")


MODEL_LABELS = {
    "mediana": "Mediana do treino", "idade": "Regressão simples", "multipla": "Regressão múltipla",
    "majoritaria": "Classe majoritária", "logistica": "Regressão logística", "arvore": "Árvore de decisão",
}


def models(package):
    st.markdown('<div class="pintro"><span class="eyebrow">visão experimental</span>'
                '<h2>O que dá para estimar?</h2>'
                '<p>Resultados dos modelos de salário de admissão e busca ativa de emprego, avaliados em dados reservados para teste.</p></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="experiment"><strong>Esta seção é experimental</strong>'
                '<p>Mostra tendências de grupos. Não é uma calculadora pessoal nem uma promessa de salário.</p></div>',
                unsafe_allow_html=True)
    view = st.segmented_control("Análise", ["Estimar salário", "Quem procura emprego"], default="Estimar salário", required=True, key="modelo_visao", persist_state="session")
    if view == "Estimar salário":
        table = package["regressao"]
        meta = package["metadata"]["modelos"]["regressao"]
        chosen = table[table.modelo.eq(meta["selecionado"])].iloc[0]
        baseline = table.set_index("modelo").loc["mediana"]
        st.markdown(f'''<div class="prediction">
  <span class="eyebrow">diferença comum entre estimativa e realidade</span>
  <div class="val">{money(chosen.mae)}</div>
  <h3>Erro médio da estimativa</h3>
  <p>Em média, o salário estimado ficou a essa distância do salário observado no teste.</p>
</div>''', unsafe_allow_html=True)
        first, second = st.columns(2)
        first.metric("Erro da referência", money(baseline.mae), help="A referência estima sempre a mediana dos salários do treino.")
        second.metric("Variação explicada (R²)", percent(chosen.r2))
        st.caption(f"Treino: {meta['treino']} ({count(meta['n_treino'])} admissões). Teste reservado: {meta['teste']} ({count(meta['n_teste'])} admissões). Valores a preços de março de 2025.")
        if chosen.previsoes_negativas:
            st.warning(f"{count(chosen.previsoes_negativas)} estimativas negativas foram mantidas nas métricas. Não use o modelo para estimativas individuais.")
        with st.expander("Ver métricas e diagnóstico da regressão", expanded=True):
            display = table[["modelo", "mae", "rmse", "r2", "previsoes_negativas"]].assign(modelo=table.modelo.replace(MODEL_LABELS))
            st.dataframe(display.rename(columns={"modelo": "Modelo", "mae": "MAE (R$)", "rmse": "RMSE (R$)",
                                                 "r2": "R²", "previsoes_negativas": "Estimativas negativas"}), hide_index=True)
            st.markdown("**Salários observados e estimados**")
            scatter = package["regressao_dispersao"]
            chart(alt.Chart(scatter).mark_circle(color=theme.LARANJA, opacity=.6).encode(
                x=alt.X("observado:Q", title="Salário observado (R$)"), y=alt.Y("previsto:Q", title="Salário estimado (R$)"),
                size=alt.Size("n:Q", title="Admissões"), tooltip=["observado", "previsto", "n"]).properties(height=245))
            st.caption("Dispersão agregada em faixas de R$ 1 mil, de R$ 0 a R$ 30 mil, com pelo menos 30 eventos por ponto. As métricas incluem todo o teste.")
            st.markdown("**Medianas por mês de teste**")
            series = package["regressao_mensal"].melt(id_vars="competencia", value_vars=["observado", "previsto"], var_name="serie", value_name="mediana")
            chart(alt.Chart(series).mark_line(point=True).encode(
                x=alt.X("competencia:O", title="Mês de teste"), y=alt.Y("mediana:Q", title="Salário mediano (R$)"),
                color=alt.Color("serie:N", title=None), tooltip=["competencia", "serie", "mediana"]).properties(height=245))
            residuals = package["regressao_residuos"]
            st.markdown("**Distribuição dos erros**")
            chart(alt.Chart(residuals).mark_bar(color=theme.LARANJA).encode(
                y=category_axis("faixa", list(residuals.faixa)),
                x=alt.X("n:Q", title="Admissões"), tooltip=[alt.Tooltip("faixa:N", title="Faixa do resíduo (R$)"), "n"]).properties(height=alt.Step(30)))
            st.caption("Resíduo = salário observado menos estimativa. Faixas com menos de 30 eventos não são exibidas.")
        download("Baixar dados desta tela (CSV)", table, "estimativa_salario.csv")
        return
    meta = package["metadata"]["modelos"]["classificacao"]
    table = package["classificacao"]
    best = table.set_index("modelo").loc[meta["selecionado"]]
    st.markdown(f'''<div class="prediction">
  <span class="eyebrow">acurácia do modelo selecionado</span>
  <div class="val">{percent(best.acuracia)}</div>
  <h3>Quem declarou buscar emprego</h3>
  <p>O modelo identificou <b>{count(best.tp)} de {count(best.n_ativos)}</b> pessoas que declararam busca ativa. A acurácia geral não reflete essa dificuldade.</p>
</div>''', unsafe_allow_html=True)
    st.caption(f"Treino: edição {meta['treino']} ({count(meta['n_treino'])} respostas válidas). Teste reservado: edição {meta['teste']} ({count(meta['n_teste'])} respostas válidas). Mede busca ativa declarada, não o que a pessoa fará depois.")
    first, second = st.columns(2)
    first.metric("Recall de busca ativa", percent(best.recall), help="Parcela de quem declarou busca ativa que o modelo identificou.")
    second.metric("Acurácia da referência", percent(table.set_index("modelo").loc["majoritaria", "acuracia"]), help="Referência que prevê apenas a classe mais comum do treino.")
    with st.expander("Ver métricas e diagnóstico da classificação", expanded=True):
        display = table[["modelo", "acuracia", "precisao", "recall", "f1", "roc_auc", "average_precision"]].assign(modelo=table.modelo.replace(MODEL_LABELS))
        st.dataframe(display.rename(columns={"modelo": "Modelo", "acuracia": "Acurácia", "precisao": "Precisão",
                                             "recall": "Recall", "f1": "F1", "roc_auc": "ROC-AUC",
                                             "average_precision": "Precisão média"}), hide_index=True)
        matrix = pd.DataFrame({"observado": ["Não", "Não", "Sim", "Sim"], "estimado": ["Não", "Sim", "Não", "Sim"],
                               "n": [best.tn, best.fp, best.fn, best.tp]})
        st.markdown("**Matriz de confusão do modelo selecionado**")
        base = alt.Chart(matrix).encode(x="estimado:N", y="observado:N", tooltip=["observado", "estimado", "n"])
        chart((base.mark_rect().encode(color=alt.Color("n:Q", scale=alt.Scale(scheme="oranges"))) +
               base.mark_text(color=theme.GRAFITE).encode(text="n:Q")).properties(height=170))
        curves = package["classificacao_curvas"]
        left, right = st.columns(2)
        for column, x, y, title, x_title, y_title in (
            (left, "fpr", "recall", "ROC", "Taxa de falsos positivos", "Recall"),
            (right, "recall", "precisao", "Precisão × recall", "Recall", "Precisão"),
        ):
            with column:
                st.markdown(f"**{title}**")
                chart(alt.Chart(curves).mark_line().encode(
                    x=alt.X(f"{x}:Q", title=x_title, scale=alt.Scale(domain=[0, 1])),
                    y=alt.Y(f"{y}:Q", title=y_title, scale=alt.Scale(domain=[0, 1])),
                    color=alt.Color("modelo:N", title=None), order="limiar:Q", tooltip=["modelo", "limiar", x, y]).properties(height=225))
        st.caption("Curvas visualizadas em 101 limiares; AUC e AP da tabela foram calculados diretamente no teste.")
    download("Baixar dados desta tela (CSV)", table, "quem_procura_emprego.csv")


def sources(package):
    meta = package["metadata"]
    caged_n = count(meta["fontes"]["caged_ti"]["n"])
    sod_new = count(meta["edicoes"]["2025/2026"]["n"])
    sod_old = count(meta["edicoes"]["2024/2025"]["n"])
    st.markdown('<div class="pintro"><span class="eyebrow">transparência</span>'
                '<h2>De onde vêm os números?</h2>'
                '<p>Usamos fontes oficiais e pesquisas conhecidas. Aqui está o que cada uma mostra — e o que fica de fora.</p></div>',
                unsafe_allow_html=True)
    st.markdown(f'''<div class="sources-list">
  <article class="source-card">
    <div class="num">01</div>
    <div>
      <span class="source-tag">fonte oficial</span>
      <h3>Novo CAGED</h3>
      <p>Admissões e desligamentos em TI no Brasil, de jan/2025 a set/2026. {caged_n} movimentações em 21 meses. Arquivos MOV, sem os ajustes do saldo oficial.</p>
      <div class="doesnt-cover"><strong>O que não cobre</strong>Trabalho por conta própria, estágio sem carteira e trabalho informal. Também não identifica senioridade nem acompanha a mesma pessoa no tempo.</div>
      <a href="https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged" target="_blank" rel="noreferrer">Conhecer a fonte ↗</a>
    </div>
  </article>
  <article class="source-card">
    <div class="num">02</div>
    <div>
      <span class="source-tag">pesquisa nacional</span>
      <h3>State of Data Brazil</h3>
      <p>Residentes no Brasil: {sod_old} respostas da edição 2024/2025 (coleta out–dez/2024) e {sod_new} da edição 2025/2026 (coleta out–dez/2025). As amostras ficam separadas.</p>
      <div class="doesnt-cover"><strong>O que não cobre</strong>Pesquisa voluntária e autodeclarada; não representa igualmente todas as carreiras de TI nem todas as cidades.</div>
      <a href="https://github.com/data-hackers-br/state-of-data-brazil" target="_blank" rel="noreferrer">Conhecer as duas edições ↗</a>
    </div>
  </article>
  <article class="source-card">
    <div class="num">03</div>
    <div>
      <span class="source-tag">pesquisa acadêmica</span>
      <h3>Pesquisa do Grupo 12 / Cesar School</h3>
      <p>O que estudantes da turma pensam sobre carreira, salário e futuro.</p>
      <div class="doesnt-cover"><strong>O que não cobre</strong>É um retrato de uma turma, não de todos os estudantes do Brasil.</div>
      <span class="source-local">35 respostas · realizada em 2026</span>
    </div>
  </article>
</div>''', unsafe_allow_html=True)
    st.markdown(f'''<div class="privacy-panel">{theme.aro_svg(48)}
  <div><span class="eyebrow">privacidade total</span>
    <h3>Nunca mostramos dados de uma pessoa</h3>
    <p>O painel não carrega microdados. Comparações salariais do CAGED e distribuições de perfis exigem pelo menos 30 observações válidas. A aba CESAR School mostra somente os resultados agregados da turma. Versão dos dados: {meta["preparado_em"][:10]}.</p>
  </div>
</div>''', unsafe_allow_html=True)
    st.download_button("Baixar manifesto público", json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"), file_name="manifesto_publico.json", mime="application/json", icon=":material/download:")


SURVEY = AREA / "cesar_pesquisa_agregada.json"


def cesar_school(package):
    data = json.loads(SURVEY.read_text(encoding="utf-8"))
    k = data["kpis"]
    n = data["n"]
    usariam = round(k["usariam_n"] / n * 100)
    cogitaram = round(k["cogitaram_n"] / n * 100)
    st.markdown('<div class="pintro"><span class="eyebrow">pesquisa do grupo 12</span>'
                '<h2>O que a turma da Cesar School espera da carreira?</h2>'
                '<p>Respostas de estudantes de Ciência da Computação sobre futuro, salário e oportunidades em tecnologia.</p></div>',
                unsafe_allow_html=True)
    st.markdown(f'''<div class="survey-hero">
  <article><span>{n} respostas</span><strong>{usariam}%</strong><p>usariam uma ferramenta para comparar salários e vagas</p></article>
  <article><span>ao longo do curso</span><strong>{cogitaram}%</strong><p>já pensaram em desistir ou mudar de área por falta de informação clara</p></article>
  <article class="salary"><span>expectativa de entrada</span><strong>{money(k["sal_mediana"])}</strong><p>valor típico esperado por mês no primeiro emprego</p></article>
</div>''', unsafe_allow_html=True)
    eyebrows = {"infos_painel": "prioridades da turma", "curso": "quem respondeu",
                "periodo": "quem respondeu", "momento": "momento de carreira", "regime": "vínculo",
                "salario": "expectativa salarial", "experiencia": "experiência em TI",
                "dificuldade": "principais dores", "facilidade": "acesso à informação"}

    def painel_pesquisa(bloco):
        itens = bloco["itens"]
        mx = max((it["n"] for it in itens), default=1) or 1
        idx_hl = next((i for i, it in enumerate(itens) if it["n"] == mx), 0)
        linhas = "".join(
            f'<div class="sbar"><span>{it["rotulo"]}</span><div class="trk">'
            f'<i class="{"hl" if i == idx_hl else ""}" style="width:{it["n"]/mx*100:.0f}%"></i></div>'
            f'<strong>{it["n"]}</strong></div>'
            for i, it in enumerate(itens))
        nota = f'<div class="chart-note">{bloco["nota"]}</div>' if bloco.get("nota") else ""
        st.markdown(f'<div class="panel-fig"><div class="ph">'
                    f'<span class="eyebrow">{eyebrows.get(bloco["id"], "pesquisa")}</span>'
                    f'<h3>{bloco["titulo"]}</h3></div>'
                    f'<div class="simple-bars">{linhas}</div>{nota}</div>', unsafe_allow_html=True)

    ordem = ([b for b in data["blocos"] if b["id"] == "infos_painel"]
             + [b for b in data["blocos"] if b["id"] != "infos_painel"])
    for bloco in ordem:
        painel_pesquisa(bloco)
    st.markdown('<div class="transp">Pesquisa acadêmica com participação voluntária. Os números são mostrados apenas em grupo — nenhuma resposta individual é exibida.</div>', unsafe_allow_html=True)


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
st.markdown('<p class="ajuda">Escolha o que você quer ver</p>', unsafe_allow_html=True)
_labels = list(LABELS)
if st.session_state.get("visao") not in _labels:
    st.session_state["visao"] = _labels[0]
_cols = st.columns(len(_labels))
for _i, _label in enumerate(_labels):
    with _cols[_i]:
        if st.button(_label, key=f"navtab_{_i}", use_container_width=True,
                     type="primary" if st.session_state["visao"] == _label else "secondary"):
            st.session_state["visao"] = _label
            st.rerun()
LABELS[st.session_state["visao"]](package)
st.divider()
st.markdown(f'''<div class="footer-fig">
  <div class="fb">{theme.aro_svg(30)}<div><strong>Radar de Carreiras</strong><span>Projeto acadêmico · Grupo 12 · 2026.2</span></div></div>
  <p style="margin:0; max-width:520px;">Fontes: Novo CAGED, State of Data Brazil e pesquisa CESAR School. Dados agregados, privacidade preservada.</p>
  <span>Cada fonte é analisada separadamente</span>
</div>''', unsafe_allow_html=True)

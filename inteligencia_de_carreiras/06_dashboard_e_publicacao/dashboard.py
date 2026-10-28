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
    st.markdown('<div class="pintro"><span class="eyebrow">salários e oportunidades</span>'
                '<h2>Quanto pagam, e onde tem vaga?</h2>'
                '<p>Escolha um cargo e um lugar. O restante se atualiza na hora. Valores de contratações com carteira assinada (Novo CAGED), já corrigidos pela inflação.</p></div>',
                unsafe_allow_html=True)

    catalog = package["metadata"]["catalogo"]
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
        period = m1.selectbox("período", list(PERIODS), format_func=PERIODS.get, key="c_periodo", persist_state="session")
        areas = ["Todas", *[v["categoria"] for v in catalog if v["tipo"] == "area"]]
        area = m2.selectbox("área", areas, key="c_area", persist_state="session")
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("c_uf") not in uf_options:
            st.session_state["c_uf"] = uf_options[0]
        uf = m3.selectbox("estado", uf_options, key="c_uf", disabled=region == "Pernambuco", persist_state="session")

    geo = geography(region, uf)
    location = "Pernambuco" if region == "Pernambuco" else (uf if uf != "Todas" else region)
    kind, category = occupation(area, cargo)
    rows = caged_query(package, geo, period, kind, category)
    if rows.empty or rows.iloc[0].n_eventos == 0:
        st.info("Não encontramos contratações para essa combinação. Experimente 'Todos os cargos' ou uma região maior, como o Brasil.")
        return
    row = rows.iloc[0]
    cargo_label = occupations[cargo] if cargo != "Todos" else "TI em geral"

    if row.admissoes_validos < MIN_N:
        st.markdown(f"**Salário típico de entrada · {cargo_label} · {location}**")
        st.warning(f"Há poucos dados de salário aqui (menos de {MIN_N} contratações), então não mostramos o valor para não enganar. Experimente 'Todos os cargos' ou uma região maior.")
    else:
        pct = max(6, min(94, (row.admissoes_p50 - row.admissoes_p10) / max(row.admissoes_p90 - row.admissoes_p10, 1) * 100))
        st.markdown(f'''<div class="answer-fig">
  <div>
    <div class="lbl">Salário típico de entrada · {cargo_label} · {location}</div>
    <div class="big">{money(row.admissoes_p50)}<small> /mês</small></div>
    <div class="faixa">A maioria entra ganhando entre <b>{money(row.admissoes_p10)}</b> e <b>{money(row.admissoes_p90)}</b> por mês.</div>
  </div>
  <div class="track-wrap">
    <div class="tlabels"><span>menor<br><b>{money(row.admissoes_p10)}</b></span><span>típico<br><b>{money(row.admissoes_p50)}</b></span><span>maior<br><b>{money(row.admissoes_p90)}</b></span></div>
    <div class="track"><i style="left:{pct:.0f}%"></i></div>
    <div class="src">Fonte: Novo CAGED · n = {count(row.admissoes_validos)} contratações</div>
  </div>
</div>''', unsafe_allow_html=True)

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
    st.markdown('<div class="pintro"><span class="eyebrow">retrato da área</span>'
                '<h2>Como é quem já trabalha em tecnologia?</h2>'
                '<p>Salários, experiência e ferramentas de profissionais da área, pela pesquisa State of Data Brazil (2024-2025). As pessoas informam seus próprios dados.</p></div>',
                unsafe_allow_html=True)
    with st.container(key="filtros_perfil"):
        pf1, pf2 = st.columns(2)
        with pf1:
            regions = ["Brasil", "Nordeste", "Pernambuco"]
            region = st.selectbox("onde?", regions, key="p_regiao", on_change=clear_uf, args=("p_",), persist_state="session")
        with pf2:
            senior = st.selectbox("nível de experiência", ["Todos", "Junior", "Pleno", "Senior", "Nao informado"], format_func=lambda v: {"Junior": "Júnior", "Senior": "Sênior", "Nao informado": "Não informado"}.get(v, v), key="p_senior", persist_state="session")
        st.divider()
        mm1, mm2 = st.columns(2)
        ufs = [p["sigla"] for p in package["metadata"]["ufs"] if region != "Nordeste" or p["nordeste"]]
        uf_options = ["PE"] if region == "Pernambuco" else ["Todas", *ufs]
        if st.session_state.get("p_uf") not in uf_options:
            st.session_state["p_uf"] = uf_options[0]
        uf = mm1.selectbox("estado", uf_options, key="p_uf", disabled=region == "Pernambuco", persist_state="session")
        work = mm2.selectbox("modelo de trabalho", ["Todos", "Remoto", "Hibrido", "Presencial", "Nao informado"], format_func=lambda v: {"Hibrido": "Híbrido", "Nao informado": "Não informado"}.get(v, v), key="p_modelo", persist_state="session")
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
    st.markdown('<div class="pintro"><span class="eyebrow">visão experimental</span>'
                '<h2>O que dá para estimar?</h2>'
                '<p>Uma leitura do mercado como um todo, sem tentar prever o salário de uma pessoa específica.</p></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="experiment"><strong>Esta seção é experimental</strong>'
                '<p>Mostra tendências de grupos. Não é uma calculadora pessoal nem uma promessa de salário.</p></div>',
                unsafe_allow_html=True)
    view = st.segmented_control("Análise", ["Estimar salário", "Quem procura emprego"], default="Estimar salário", required=True, key="modelo_visao", persist_state="session")
    if view == "Estimar salário":
        table = package["R1_teste_marco"]
        meta = package["metadata"]["modelos"]["regressao"]
        chosen = table[table.modelo.eq(meta["modelo_selecionado"])].iloc[0]
        st.markdown(f'''<div class="prediction">
  <span class="eyebrow">diferença comum entre estimativa e realidade</span>
  <div class="val">{money(chosen.mae)}</div>
  <h3>Erro médio da estimativa</h3>
  <p>Na prática, a estimativa erra, em média, cerca desse valor por mês. Por isso o Radar mostra <b>faixas</b> de salário, e não um número exato. O modelo capta cerca de {max(chosen.r2, 0)*100:.0f}% da variação.</p>
</div>''', unsafe_allow_html=True)
        st.caption("Como chegamos nisso: comparamos estimativas com dados reais de grupos parecidos (cargo, idade e região) em um período de teste separado. Quanto menor o erro, mais perto a estimativa ficou — e o modelo olha grupos, nunca uma pessoa específica.")
        download("Baixar dados desta tela (CSV)", table, "estimativa_salario.csv")
        return
    best = package["C1_metricas_teste"].set_index("modelo").loc["logistica"]
    st.markdown(f'''<div class="prediction">
  <span class="eyebrow">acerto do melhor modelo</span>
  <div class="val">{percent(best.acuracia)}</div>
  <h3>Quem está querendo trocar de emprego</h3>
  <p>Testamos adivinhar, pelo perfil da pessoa, quem busca uma nova vaga. Mesmo o melhor modelo deixa passar {int(best.fn)} de {int(best.n_ativos)} pessoas que realmente procuravam — serve para enxergar grupos, não para prever uma pessoa.</p>
</div>''', unsafe_allow_html=True)
    st.caption("Mede intenção de troca hoje, não o que a pessoa fará no futuro. Pesquisa voluntária (State of Data), que pode não representar todo mundo.")
    download("Baixar dados desta tela (CSV)", package["C1_metricas_teste"], "quem_procura_emprego.csv")


def sources(package):
    meta = package["metadata"]
    caged_n = count(meta["fontes"]["caged_ti"]["n"])
    sod_n = count(meta["fontes"]["state_of_data_brasil"]["n"])
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
      <p>Contratações e saídas de empregos com carteira assinada no Brasil (jan–mar/2025). {caged_n} registros preparados.</p>
      <div class="doesnt-cover"><strong>O que não cobre</strong>Trabalho por conta própria, estágio sem carteira e trabalho informal. Também não identifica senioridade nem acompanha a mesma pessoa no tempo.</div>
      <a href="https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged" target="_blank" rel="noreferrer">Conhecer a fonte ↗</a>
    </div>
  </article>
  <article class="source-card">
    <div class="num">02</div>
    <div>
      <span class="source-tag">pesquisa nacional</span>
      <h3>State of Data Brazil</h3>
      <p>Respostas de profissionais de dados sobre trabalho, salário e ferramentas (2024–2025). {sod_n} respostas preparadas.</p>
      <div class="doesnt-cover"><strong>O que não cobre</strong>Pesquisa voluntária e autodeclarada; não representa igualmente todas as carreiras de TI nem todas as cidades.</div>
      <a href="https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025" target="_blank" rel="noreferrer">Conhecer a fonte ↗</a>
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
    <p>Todos os números são agrupados por cargo, local e período. Se um grupo tiver menos de 30 registros, o valor fica oculto. Versão dos dados: {meta["preparado_em"][:10]}.</p>
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

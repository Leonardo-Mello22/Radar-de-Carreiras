"""
Radar de Carreira em TI — Dashboard v1 (Streamlit).

Visual: docs/identidade_visual.md (cores em app/theme.py, gráficos via src/plotting.py).
Estrutura: cabeçalho escuro -> filtros em linha -> número principal -> 2 gráficos -> rodapé.

Rodar:  streamlit run app/dashboard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import theme  # noqa: E402
from src import config as cfg  # noqa: E402
from src import plotting  # noqa: E402

st.set_page_config(page_title="Radar de Carreira em TI", page_icon=None, layout="wide")
theme.aplicar_tema()
plotting.configurar()


@st.cache_data
def carregar() -> pd.DataFrame:
    return pd.read_parquet(cfg.CAGED_TI_PARQUET)


try:
    df = carregar()
except FileNotFoundError:
    st.error("base tratada não encontrada — rode: python -m src.transform")
    st.stop()

# --------------------------------------------------------------------------- #
# Cabeçalho escuro com o aro de radar (sem emoji)
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <div class="header-escuro">
      {theme.aro_marca_dagua(420, 0.10)}
      <div class="nome">{theme.aro_svg(42)} Radar de Carreira em TI</div>
      <div class="sub">faixa salarial real do emprego formal em TI, a partir dos microdados
      oficiais do Novo CAGED — foco em Pernambuco e Nordeste</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# Filtros em UMA LINHA (nunca na sidebar)
# --------------------------------------------------------------------------- #
qp = st.query_params


def _idx(opcoes: list[str], chave: str) -> int:
    val = qp.get(chave)
    return opcoes.index(val) if val in opcoes else 0


st.markdown('<div class="kicker">explorar</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    cargos = ["(todos)"] + sorted(df["cbo_nome"].dropna().unique())
    cargo = st.selectbox("cargo", cargos, index=_idx(cargos, "cargo"))
with c2:
    ufs = ["(todas)"] + sorted(df["uf_nome"].dropna().unique())
    uf = st.selectbox("uf", ufs, index=_idx(ufs, "uf"))
with c3:
    df_uf = df if uf == "(todas)" else df[df["uf_nome"] == uf]
    municipios = ["(todos)"] + sorted(df_uf["municipio_nome"].dropna().unique())
    municipio = st.selectbox("município", municipios, index=_idx(municipios, "municipio"))
with c4:
    periodos = ["(todos)"] + sorted(df["competencia"].dropna().unique())
    periodo = st.selectbox("período", periodos, index=_idx(periodos, "periodo"))

movimentos = ["admissão", "desligamento", "ambos"]
movimento = st.radio("movimento", movimentos, index=_idx(movimentos, "movimento") or 0,
                     horizontal=True,
                     help="a faixa de entrada (admissão) é a mais útil para início de carreira")

# aplica filtros
f = df.copy()
if cargo != "(todos)": f = f[f["cbo_nome"] == cargo]
if uf != "(todas)": f = f[f["uf_nome"] == uf]
if municipio != "(todos)": f = f[f["municipio_nome"] == municipio]
if periodo != "(todos)": f = f[f["competencia"] == periodo]
if movimento != "ambos": f = f[f["movimento"] == movimento]

fs = f[f["salario_valido"]]
n = len(fs)
comp_ref = periodo if periodo != "(todos)" else cfg.MESES[-1]
rotulo_recorte = " · ".join([
    cargo if cargo != "(todos)" else "todos os cargos",
    uf if uf != "(todas)" else "Brasil",
    municipio if municipio != "(todos)" else "todas as cidades",
    f"movimento: {movimento}",
])
st.markdown(f'<div class="kicker" style="margin-top:14px;">recorte</div>'
            f'<div class="titulo-secao">{rotulo_recorte}</div>', unsafe_allow_html=True)
st.markdown("")

# --------------------------------------------------------------------------- #
# Amostra mínima -> caixa de aviso (sem número cinza, sem gráfico vazio)
# --------------------------------------------------------------------------- #
if n < cfg.MIN_AMOSTRA:
    st.markdown(
        f'<div class="aviso">poucos registros para este recorte '
        f'(n = {n}, mínimo {cfg.MIN_AMOSTRA}) — tente uma cidade maior, a UF inteira '
        f'ou um período mais longo.</div>',
        unsafe_allow_html=True,
    )
else:
    p10, p50, p90 = (fs["salario_real"].quantile(q / 100) for q in cfg.PERCENTIS)

    col_num, col_amostra = st.columns([2, 1])
    with col_num:
        st.markdown(
            f"""
            <div class="destaque">
              <div class="rotulo">mediana do salário de {movimento if movimento!='ambos' else 'entrada/saída'}</div>
              <div class="mediana">{theme.reais(p50)}</div>
              <div class="faixa-txt">piso (p10) <b>{theme.reais(p10)}</b> &nbsp;·&nbsp;
                 teto (p90) <b>{theme.reais(p90)}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_amostra:
        st.markdown(
            f"""
            <div class="card">
              <div class="rotulo" style="color:{theme.TEXTO_TERCIARIO}">amostra</div>
              <div style="font-size:40px; font-weight:800; color:{theme.GRAFITE}; line-height:1.1">
                 {('{:,}'.format(n)).replace(',', '.')}</div>
              <div class="legenda">movimentações · referência {theme.competencia_para_mm_aaaa(comp_ref)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    g1, g2 = st.columns(2)

    with g1:
        st.markdown('<div class="kicker">distribuição</div>'
                    '<div class="titulo-secao" style="font-size:19px">como os salários se espalham</div>',
                    unsafe_allow_html=True)
        from matplotlib.ticker import MaxNLocator
        dados = fs["salario_real"]
        dados = dados[dados <= dados.quantile(0.99)]
        fig, ax = plt.subplots(figsize=(5.6, 3.6))
        ax.axvspan(p10, p90, color=theme.FAIXA_PREENCHIMENTO, alpha=0.45, lw=0)
        ax.hist(dados, bins=30, color=theme.NEUTRO_GRAFICO)
        ax.axvline(p50, color=theme.LARANJA, lw=2.5)
        ax.annotate("mediana", xy=(p50, 1), xycoords=("data", "axes fraction"),
                    xytext=(5, -6), textcoords="offset points",
                    color=theme.LARANJA, fontsize=9, fontweight="bold",
                    ha="left", va="top")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.xaxis.set_major_formatter(plotting.REAIS_KILO)
        ax.margins(x=0.02)
        ax.set_ylabel("nº de movimentações")
        plotting.fonte(fig, comp_ref, n)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        st.pyplot(fig)

    with g2:
        st.markdown('<div class="kicker">evolução</div>'
                    '<div class="titulo-secao" style="font-size:19px">mediana ao longo do tempo</div>',
                    unsafe_allow_html=True)
        serie = fs.groupby("competencia")["salario_real"].median()
        fig2, ax2 = plt.subplots(figsize=(5.6, 3.6))
        rotulos = [theme.competencia_para_mm_aaaa(c) for c in serie.index]
        ax2.plot(rotulos, serie.values, "o-", color=theme.LARANJA, ms=9, lw=2.5)
        ax2.yaxis.set_major_formatter(plotting.REAIS)
        if len(serie) == 1:
            ax2.text(0.5, 0.45, "apenas 1 competência ingerida\nadicione meses em config.MESES",
                     transform=ax2.transAxes, ha="center", color=theme.TEXTO_TERCIARIO, fontsize=9)
        plotting.fonte(fig2, comp_ref, n)
        plt.tight_layout(rect=(0, 0.04, 1, 1))
        st.pyplot(fig2)

# --------------------------------------------------------------------------- #
# Rodapé fixo: fonte, mês de referência e limites declarados
# --------------------------------------------------------------------------- #
st.markdown(
    f'<div class="rodape"><b>fonte:</b> {cfg.FONTE_DADOS}.<br>'
    f'<b>mês de referência (deflação ipca):</b> {theme.competencia_para_mm_aaaa(cfg.IPCA_MES_REFERENCIA)}'
    f' &nbsp;·&nbsp; <b>amostra mínima:</b> {cfg.MIN_AMOSTRA} registros.<br>'
    f'<b>limites declarados:</b> {cfg.LIMITES_DECLARADOS}</div>',
    unsafe_allow_html=True,
)

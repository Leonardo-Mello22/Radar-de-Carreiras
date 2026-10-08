"""
Identidade visual do Radar de Carreira em TI — FONTE ÚNICA DE CORES.

Nenhum outro arquivo do projeto deve conter hexadecimal escrito à mão: todos importam daqui.
Ver docs/identidade_visual.md para a especificação completa.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# 1. Paleta
# --------------------------------------------------------------------------- #
LARANJA = "#FF7200"              # ação, destaque, número principal, série em evidência
LARANJA_PRESSIONADO = "#E05F00"  # hover / estado ativo
LARANJA_CLARO = "#FFF0E3"        # caixas de destaque, chips ativos
LARANJA_ESCURO_TEXTO = "#B34F00"  # texto sobre LARANJA_CLARO
GRAFITE = "#16181D"              # painéis escuros, títulos, cabeçalho
GRAFITE_ELEVADO = "#22252B"      # cards dentro de painel escuro
BORDA_ESCURA = "#2C2F35"         # divisórias em painel escuro
CINZA_CLARO = "#F3F3F4"          # fundo de card neutro
BORDA_CLARA = "#E6E7EA"          # bordas em fundo branco
TRILHO_GRAFICO = "#EDEEF0"       # grade / track
TEXTO = "#1C1C1C"                # corpo em fundo claro
TEXTO_SECUNDARIO = "#5A5E66"     # descrições
TEXTO_TERCIARIO = "#8A8E96"      # legendas, fonte do dado, amostra
TEXTO_SOBRE_ESCURO = "#C9CBD0"   # corpo em painel escuro
NEUTRO_GRAFICO = "#B9BCC2"       # séries e barras sem destaque
FAIXA_PREENCHIMENTO = "#FFC08F"  # área entre piso e teto
LEAD = "#4A4E55"                 # cor do subtítulo/lead
BRANCO = "#FFFFFF"

GRAD_ESCURO = "linear-gradient(100deg, #16181D 0%, #1E1A16 55%, #33210F 100%)"
GRAD_CARD_LARANJA = "linear-gradient(90deg, #FF7200 0%, #E05F00 100%)"

# --------------------------------------------------------------------------- #
# 2. Tipografia
# --------------------------------------------------------------------------- #
FONTE_FAMILIA = "Barlow"
FONTE_FALLBACK = "Arial, Helvetica, sans-serif"
FONTE_MPL = ["Barlow", "DejaVu Sans"]  # matplotlib: cai para DejaVu Sans se Barlow ausente


# --------------------------------------------------------------------------- #
# 3. Formatação de valores
# --------------------------------------------------------------------------- #
def reais(v: float) -> str:
    """R$ 3.240 — sem centavos, milhar com ponto (padrão BR)."""
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def linha_fonte(referencia_mm_aaaa: str, n: int, fonte: str = "Novo CAGED") -> str:
    """'Fonte: Novo CAGED · referência 01/2025 · n = 1.284'."""
    n_fmt = f"{n:,}".replace(",", ".")
    return f"Fonte: {fonte} · referência {referencia_mm_aaaa} · n = {n_fmt}"


def competencia_para_mm_aaaa(competencia: str) -> str:
    """'202501' -> '01/2025'."""
    c = str(competencia)
    return f"{c[4:6]}/{c[0:4]}" if len(c) == 6 else c


# --------------------------------------------------------------------------- #
# 4. Símbolo (aro de radar) — SVG fixo, não redesenhar
# --------------------------------------------------------------------------- #
def aro_svg(tamanho: int = 44, cor: str = LARANJA) -> str:
    return f"""<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 64 64" fill="{cor}" stroke="{cor}">
  <circle cx="32" cy="32" r="27"   fill="none" stroke-width="2.6" opacity=".38"/>
  <circle cx="32" cy="32" r="19.5" fill="none" stroke-width="2.8" opacity=".58"/>
  <circle cx="32" cy="32" r="12"   fill="none" stroke-width="3"   opacity=".8"/>
  <circle cx="32" cy="32" r="4.6"/>
</svg>"""


def aro_marca_dagua(tamanho: int = 420, opacidade: float = 0.10) -> str:
    """Mesmo aro, grande e translúcido, para sangrar no canto de um painel escuro."""
    svg = aro_svg(tamanho, LARANJA)
    return (f'<div style="position:absolute; top:-90px; right:-90px; '
            f'opacity:{opacidade}; pointer-events:none;">{svg}</div>')


# --------------------------------------------------------------------------- #
# 5. Tema do Streamlit — CSS injetado uma única vez
# --------------------------------------------------------------------------- #
def _css() -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, p, div, span, label, input, button {{
        font-family: '{FONTE_FAMILIA}', {FONTE_FALLBACK};
        color: {TEXTO};
    }}
    .stApp {{ background: {BRANCO}; }}
    #MainMenu, header[data-testid="stHeader"], footer {{ visibility: hidden; height: 0; }}
    .block-container {{ padding-top: 1.2rem; max-width: 1180px; }}

    h1,h2,h3,h4 {{ color: {GRAFITE}; font-weight: 800; letter-spacing: -0.2px; }}

    /* kicker -> titulo -> lead */
    .kicker {{ color:{LARANJA}; font-weight:700; font-size:13px; text-transform:uppercase;
               letter-spacing:2.5px; margin:0 0 6px 0; }}
    .titulo-secao {{ color:{GRAFITE}; font-weight:800; font-size:26px; line-height:1.14; margin:0; }}
    .lead {{ color:{LEAD}; font-weight:400; font-size:16.5px; line-height:1.6; max-width:820px; }}
    .legenda {{ color:{TEXTO_TERCIARIO}; font-size:12.5px; }}

    /* cabeçalho escuro */
    .header-escuro {{ position:relative; overflow:hidden; background:{GRAD_ESCURO};
        border-radius:18px; padding:30px 34px; margin-bottom:18px; }}
    .header-escuro .nome {{ color:#FFFFFF; font-weight:800; font-size:32px; line-height:1;
        display:flex; align-items:center; gap:14px; }}
    .header-escuro .sub {{ color:{TEXTO_SOBRE_ESCURO}; font-size:15px; margin-top:10px; max-width:720px; }}

    /* número principal em destaque */
    .destaque {{ background:{LARANJA_CLARO}; border-radius:14px; padding:22px 26px;
        border-left:6px solid {LARANJA}; }}
    .destaque .mediana {{ color:{LARANJA}; font-weight:800; font-size:56px; line-height:1; }}
    .destaque .rotulo {{ color:{LARANJA_ESCURO_TEXTO}; font-weight:800; font-size:11px;
        text-transform:uppercase; letter-spacing:1.1px; }}
    .faixa-txt {{ color:{TEXTO_SECUNDARIO}; font-size:15px; margin-top:6px; }}
    .faixa-txt b {{ color:{GRAFITE}; }}

    .card {{ background:{CINZA_CLARO}; border:1px solid {BORDA_CLARA}; border-radius:14px;
        padding:20px 24px; }}

    /* aviso de amostra insuficiente */
    .aviso {{ background:{LARANJA_CLARO}; border-left:6px solid {LARANJA}; border-radius:14px;
        padding:20px 24px; color:{LARANJA_ESCURO_TEXTO}; font-weight:600; font-size:16px; }}

    /* rodapé */
    .rodape {{ background:{GRAFITE}; color:{TEXTO_SOBRE_ESCURO}; font-size:12.5px;
        padding:18px 22px; border-radius:14px; margin-top:22px; line-height:1.6; }}
    .rodape b {{ color:#FFFFFF; }}

    /* filtros: rótulos minúsculos */
    .stSelectbox label, .stRadio label {{ color:{TEXTO_SECUNDARIO} !important;
        font-weight:600 !important; font-size:13px !important; }}
    div[data-baseweb="select"] > div {{ border-radius:12px !important; border-color:{BORDA_CLARA} !important; }}
    </style>
    """


def aplicar_tema() -> None:
    """Injeta o CSS do tema. Chamar na primeira linha do dashboard."""
    import streamlit as st
    st.markdown(_css(), unsafe_allow_html=True)

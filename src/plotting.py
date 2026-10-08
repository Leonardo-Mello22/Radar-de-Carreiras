"""
Configuração ÚNICA do matplotlib para o projeto (regras de gráfico da identidade visual).

Chame `plotting.configurar()` uma vez no topo de qualquer notebook/script. Nenhum gráfico
deve ser estilizado célula a célula. Cores importadas de app.theme (fonte única de hex).

Regras aplicadas (ver docs/identidade_visual.md §5):
  - uma cor de destaque (LARANJA); resto NEUTRO_GRAFICO
  - grade só horizontal, TRILHO_GRAFICO, 1px; sem spines de cima/direita
  - texto em cor de texto, nunca na cor da série
  - faixa = área FAIXA_PREENCHIMENTO; mediana = marca LARANJA
  - toda figura leva linha de fonte (helper `fonte`)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from app import theme

# atalhos de cor
LARANJA = theme.LARANJA
NEUTRO = theme.NEUTRO_GRAFICO
FAIXA = theme.FAIXA_PREENCHIMENTO
TEXTO = theme.TEXTO
TERCIARIO = theme.TEXTO_TERCIARIO
GRAFITE = theme.GRAFITE

# formatador de reais para eixos (R$ 3.240, sem centavos)
REAIS = FuncFormatter(lambda v, _: theme.reais(v))


def _reais_kilo(v, _):
    """Compacto para eixos com valores altos: R$ 0, R$ 5k, R$ 12k (evita rótulos sobrepostos)."""
    if abs(v) < 1000:
        return f"R$ {v:,.0f}".replace(",", ".")
    return f"R$ {v/1000:.0f}k"


# formatador compacto de reais para eixos muito espalhados (milhares)
REAIS_KILO = FuncFormatter(_reais_kilo)

_BARLOW_CANDIDATAS = [
    "/Library/Fonts/Barlow-Regular.ttf",
    str(Path.home() / "Library/Fonts/Barlow-Regular.ttf"),
    "/usr/share/fonts/truetype/barlow/Barlow-Regular.ttf",
]


def _registrar_barlow() -> list[str]:
    for p in _BARLOW_CANDIDATAS:
        if Path(p).exists():
            try:
                for f in Path(p).parent.glob("Barlow*.ttf"):
                    mpl.font_manager.fontManager.addfont(str(f))
                return ["Barlow", "DejaVu Sans"]
            except Exception:
                break
    return ["DejaVu Sans"]  # Barlow ausente -> fallback sans-serif


def configurar() -> None:
    familia = _registrar_barlow()
    plt.rcParams.update({
        "figure.figsize": (8.4, 4.6),
        "figure.dpi": 120,
        "font.family": familia,
        "font.size": 11,
        "text.color": TEXTO,
        "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": GRAFITE,
        "axes.labelsize": 11, "axes.labelcolor": theme.TEXTO_SECUNDARIO,
        "axes.edgecolor": theme.BORDA_CLARA,
        "axes.linewidth": 1.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": theme.TRILHO_GRAFICO, "grid.linewidth": 1.0,
        "xtick.color": TEXTO, "ytick.color": TEXTO,
        "xtick.labelcolor": theme.TEXTO_SECUNDARIO, "ytick.labelcolor": theme.TEXTO_SECUNDARIO,
        "legend.frameon": False, "legend.fontsize": 10,
        "figure.facecolor": theme.BRANCO, "axes.facecolor": theme.BRANCO,
    })


def fonte(fig, competencia: str, n: int, fonte_dado: str = "Novo CAGED") -> None:
    """Adiciona a linha de fonte (12.5px, terciário) no rodapé da figura."""
    txt = theme.linha_fonte(theme.competencia_para_mm_aaaa(competencia), n, fonte_dado)
    fig.text(0.01, 0.005, txt, fontsize=8.5, color=TERCIARIO)


def valor_na_ponta(ax, ys, valores, *, horizontal=True, fmt=theme.reais, dx=0):
    """Rótulo direto na ponta da barra (até 8 categorias -> dispensar legenda)."""
    for y, v in zip(ys, valores):
        if horizontal:
            ax.text(v + dx, y, "  " + fmt(v), va="center", ha="left",
                    fontsize=9, color=TEXTO)
        else:
            ax.text(y, v + dx, fmt(v), ha="center", va="bottom", fontsize=9, color=TEXTO)

"""
Configuração central do projeto Radar de Carreira em TI.

Toda constante que mais de um módulo precisa mora aqui — em especial a amostra
mínima (restrição do projeto), as famílias CBO de TI confirmadas no layout oficial,
o mês de referência do IPCA e a paleta visual.

Caminhos sempre via pathlib (projeto roda em Windows, macOS e Linux).
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Caminhos (todos relativos à raiz do repositório)
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
DOCS = ROOT / "docs"
EVIDENCIAS = ROOT / "evidencias"

LAYOUT_XLSX = RAW / "Layout_Novo_Caged_Movimentacao.xlsx"
CAGED_TI_PARQUET = PROCESSED / "caged_ti.parquet"
CBO_TI_PARQUET = PROCESSED / "cbo_ti.parquet"
IPCA_PARQUET = PROCESSED / "ipca.parquet"

# --------------------------------------------------------------------------- #
# Fonte de dados — FTP do Novo CAGED (PDET / Ministério do Trabalho)
# --------------------------------------------------------------------------- #
FTP_HOST = "ftp.mtps.gov.br"
FTP_BASE = "/pdet/microdados/NOVO CAGED"
# ATENÇÃO: os NOMES DE ARQUIVO no FTP usam latin-1 (ã->%E3, ç->%E7) na URL.
# Já o CONTEÚDO do .txt descompactado é UTF-8 (ver docs/00_verificacao_layout.md).

# Formato do arquivo .txt descompactado — VERIFICADO contra o dado real de 2025-01.
# O briefing dizia latin-1; o arquivo real é UTF-8. Mantemos o valor verificado.
TXT_ENCODING = "utf-8"
TXT_SEP = ";"
TXT_DECIMAL = ","

# --------------------------------------------------------------------------- #
# Restrições do projeto (Seção 5 do briefing) — NÃO violar
# --------------------------------------------------------------------------- #
# Recorte com menos de MIN_AMOSTRA registros não exibe número: exibe aviso.
# Constante única de todo o projeto — referenciada por EDA, dashboard e checks.
MIN_AMOSTRA = 30

# Percentis de faixa salarial (piso, mediana, teto). Média sozinha é proibida.
PERCENTIS = (10, 50, 90)

# Limiares de plausibilidade do salário mensal (R$). Fora disso = outlier/erro,
# marcado como salario_valido=False na base tratada (não é apagado, é sinalizado).
SAL_MIN_PLAUSIVEL = 300.0
SAL_MAX_PLAUSIVEL = 200_000.0
IDADE_MIN, IDADE_MAX = 14, 90

# --------------------------------------------------------------------------- #
# Famílias CBO-2002 de TI — CONFIRMADAS na aba 'cbo2002ocupação' do layout oficial
# (ver docs/dicionario_de_variaveis.md para a lista de ocupações de cada família).
#
# Correções feitas sobre a lista "aproximada" do briefing (que pedia confirmação):
#   - 3173 REMOVIDA: não existe nenhuma ocupação iniciando em 3173 na CBO-2002.
#   - 1425 ADICIONADA: é a família real de "Gerentes de Tecnologia da Informação".
#     O briefing associava gerência de TI ao 1236, mas 1236 = "Diretor de Serviços
#     de Informática" (apenas 123605). 1425 cobre gerentes de dev, projetos,
#     segurança e suporte de TI.
# --------------------------------------------------------------------------- #
CBO_FAMILIAS_TI = ["1236", "1425", "2122", "2123", "2124", "3171", "3172"]

# Famílias de TI candidatas NÃO incluídas no recorte principal deste ciclo
# (registradas para avaliação em ciclos futuros — ver verificação do layout):
#   2031 (pesquisador em ciência da computação, carreira acadêmica),
#   3132 (técnico em manutenção de equipamentos de informática),
#   3133 (técnico de comunicação de dados).
CBO_FAMILIAS_TI_CANDIDATAS = ["2031", "3132", "3133"]

# --------------------------------------------------------------------------- #
# Deflação IPCA (SIDRA / IBGE) — tabela 1737, variável 2266 (número-índice)
# --------------------------------------------------------------------------- #
SIDRA_IPCA_URL = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all"
# Mês de referência para o qual todos os salários são trazidos a preços constantes.
# Usamos o último mês de dados do ciclo. Ajustar quando novos meses forem ingeridos.
IPCA_MES_REFERENCIA = "202501"  # AAAAMM

# --------------------------------------------------------------------------- #
# Meses de CAGEDMOV a processar neste ciclo (AAAAMM).
# Adicionar mais meses aqui habilita automaticamente séries temporais na EDA/dash.
# --------------------------------------------------------------------------- #
MESES = ["202501"]

# UFs do Nordeste (foco do produto) — códigos IBGE.
UF_NORDESTE = {
    21: "Maranhão", 22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte",
    25: "Paraíba", 26: "Pernambuco", 27: "Alagoas", 28: "Sergipe", 29: "Bahia",
}

# --------------------------------------------------------------------------- #
# Identidade visual — a FONTE ÚNICA de cores é app/theme.py (nenhum hex aqui).
# Mantemos estes aliases só por compatibilidade com código que importa de config.
# --------------------------------------------------------------------------- #
from app import theme as _theme  # noqa: E402

COR_LARANJA = _theme.LARANJA
COR_GRAFITE = _theme.GRAFITE
COR_CINZA_CLARO = _theme.CINZA_CLARO
COR_LARANJA_CLARO = _theme.LARANJA_CLARO
COR_TEXTO = _theme.TEXTO
COR_SECUNDARIO = _theme.TEXTO_SECUNDARIO
FONTE = _theme.FONTE_FAMILIA

# Procedência exibida em todo número (Seção 5).
FONTE_DADOS = "Novo CAGED (PDET/Ministério do Trabalho) — microdados de movimentações"

# Limites declarados da base — devem aparecer no dashboard e na documentação.
LIMITES_DECLARADOS = (
    "O CAGED cobre apenas o emprego formal com carteira assinada (CLT); PJ, MEI e "
    "informais ficam de fora. Não mede habilidade técnica nem senioridade. Cada linha "
    "é uma movimentação (admissão ou desligamento), não uma pessoa. Salários são "
    "deflacionados pelo IPCA a preços de " + IPCA_MES_REFERENCIA + "."
)

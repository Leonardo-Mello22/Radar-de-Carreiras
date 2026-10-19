# Datasets preparados para o Radar de Carreiras

Pacote de dados da area `inteligencia_de_carreiras`, integrado ao repositorio.
O dashboard existente continua usando suas fontes anteriores; a integracao destes
datasets ao aplicativo sera feita nas etapas de dashboard e validacao.

Consulte o [catalogo de dados](catalogo.md) para escolher a tabela adequada.
Os datasets de cada fonte permanecem separados. A pesquisa propria e a matriz G12
foram adicionadas com manifesto, mapa de perguntas, dicionario e relatorios.
Leia a [documentacao de integracao](organizacao_e_integracao.md) para regras de
comparacao, inconsistencias do questionario e privacidade.

## Comece por estes arquivos

| Arquivo em `tratados/` | Conteudo | Registros |
| --- | --- | ---: |
| `caged_ti.parquet` / `.csv` | Movimentacoes de TI em todo o Brasil, janeiro a marco de 2025 | 118.564 |
| `caged_ti_pernambuco.parquet` / `.csv` | Mesmo recorte, somente Pernambuco | 2.305 |
| `caged_ti_nordeste.parquet` / `.csv` | Mesmo recorte, somente Nordeste | 10.704 |
| `state_of_data_carreiras.parquet` / `.csv` | 51 campos selecionados e derivados sobre carreira em dados | 5.215 |
| `state_of_data_brasil.parquet` / `.csv` | Respondentes que declararam morar no Brasil | 5.076 |
| `state_of_data_pernambuco.parquet` / `.csv` | Respondentes que declararam morar em PE | 120 |
| `state_of_data_nordeste.parquet` / `.csv` | Respondentes que declararam morar no Nordeste | 516 |
| `state_of_data_completo_normalizado.parquet` / `.csv` | Todas as 403 colunas originais padronizadas, mais ID de linha e fonte | 5.215 |
| `state_of_data_tecnologias.parquet` / `.csv` | Uma linha por respondente e opcao de tecnologia selecionada | 28.881 |

Use Parquet no Python: preserva tipos e ocupa menos espaco. Os CSV usam UTF-8 com BOM,
virgula como separador, ponto decimal e campos ausentes vazios. No Excel, importe por
Dados > De Texto/CSV e mantenha codigos de CBO, municipio e competencia como texto.

## Categorias acrescentadas

CAGED: area de TI por ocupacao, funcao de gestao, faixa etaria, escolaridade agrupada,
jornada semanal, setor CNAE, tamanho do estabelecimento, recorte regional,
primeiro emprego formal, aprendizagem, trabalho parcial/intermitente, faixa salarial
real e indicadores de validade. Os codigos e descricoes oficiais foram preservados.

State of Data: area profissional, escolaridade agrupada, senioridade declarada,
vinculo CLT/PJ/estagio/estudante, remoto/hibrido/presencial, inicio na area de dados
ate dois anos, recorte regional, limites das faixas de salario e uso de SQL, Python,
R, Power BI, AWS, GCP e Azure. Outras tecnologias ficam na tabela longa e na base completa.

O mapeamento analitico de area de TI esta em `auxiliares/cbo_ti_categorias.csv`.
O recorte mantem as familias do projeto: 1236, 1425, 2122, 2123, 2124, 3171 e 3172.
Isso inclui algumas ocupacoes de automacao industrial, explicitamente categorizadas.
O recorte nao significa todas as carreiras possiveis em tecnologia.

## Normalizacao aplicada

- Nomes de colunas em snake_case, sem acentos, com nomes unicos.
- Textos em Unicode NFC, sem espacos extras. Descricoes oficiais mantem seus acentos.
- Numeros, inteiros, datas e booleanos com tipos explicitos no Parquet.
- Codigos geograficos e ocupacionais preservados como texto.
- Municipios e CBO traduzidos, sem nomes ou codigos sem correspondencia neste recorte.
- Salarios do CAGED corrigidos pelo IPCA para precos de marco de 2025.
- Salarios nominais abaixo de R$300 ou acima de R$200.000 sinalizados, nao apagados.
- Duas respostas exatamente repetidas do State of Data removidas da versao tratada.
- Linhas iguais do CAGED preservadas: a base nao identifica pessoas e podem ser eventos distintos.
- Valores ausentes mantidos. Nao foram preenchidos com media, zero ou senioridade inventada.

`modelagem/caged_features_numericas` fornece z-score, min-max e log1p separados dos
valores em reais. Os parametros estao em `modelagem/parametros_normalizacao.json`.
Eles foram ajustados sobre este pacote para exploracao. Para medir desempenho de
um modelo preditivo, separe treino/teste antes de ajustar escalas, categorias ou imputacao.

## Agregados e qualidade

`agregados/caged_indicadores_uf_area_mes` contem contagens e p10/p50/p90 de salarios
por mes, UF, area e movimento. Percentis ficam vazios quando ha menos de 30 salarios
validos no grupo. As contagens continuam disponiveis para reconciliacao.

`qualidade/controle_caged_mensal` reconcilia 13.530.056 linhas brutas examinadas com
o recorte de 118.564 movimentacoes TI. Ha 690 salarios sinalizados e 1.386 linhas
tratadas iguais, mantidas. Campos de trabalho parcial/intermitente podem estar ausentes.

`qualidade/relatorio_qualidade.json` detalha nulos, contagens e regras.
`qualidade/validacao_exports.json` registra as verificacoes feitas nos arquivos finais.
`auxiliares/dicionario_dados.csv` descreve campos, tipos, exemplos e valores ausentes.

## Limites de uso

O CAGED contem eventos de admissao e desligamento de emprego formal. Nao contem
identificador de pessoa, senioridade ou tempo de vinculo. Primeiro emprego formal
nao equivale a Junior. A unidade de salario se refere a parte fixa; o campo `salario`
ja e mensal segundo o layout oficial, portanto nao foi multiplicado por horas ou dias.

Este pacote usa apenas CAGEDMOV de janeiro, fevereiro e marco de 2025. Nao incorpora
CAGEDFOR/CAGEDEXC e nao deve ser apresentado como saldo oficial final com todos os ajustes,
serie anual completa ou mercado atual de 2026. As faixas de salario real usam intervalos
com limite inferior incluso e superior exclusivo; a ultima faixa nao tem teto.

State of Data e uma pesquisa autodeclarada da area de dados, com amostra voluntaria.
Nao representa todo o mercado de TI. Salarios sao faixas, nao valores exatos: nao foi
inventado ponto medio nem salario preciso. A faixa acima de R$40.001 permanece aberta.
Senioridade ausente permanece ausente. Experiencia em TI anterior a dados nao equivale
a experiencia total atual em TI. Nulos podem resultar do fluxo do questionario.

Mantenha as bases separadas. Nao concatene respostas da pesquisa e eventos do CAGED
como se fossem a mesma unidade, e nao una registros individuais por UF, cargo ou salario.
Cada ID novo identifica uma linha de origem, nao uma mesma pessoa entre bases.

## Fontes e arquivos originais

- [Novo CAGED e layout oficial, MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged)
- [State of Data Brazil 2024-2025, Data Hackers](https://www.kaggle.com/datasets/datahackers/state-of-data-brazil-20242025)
- [Espelho do arquivo usado, comunidade Data Hackers / Let's Data](https://github.com/letsdata/challenge-data-hackers-2025/tree/main/aula01/script/data/raw)
- [IPCA numero-indice, IBGE SIDRA](https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/202501-202503)
- [Municipios, API de Localidades IBGE](https://servicodados.ibge.gov.br/api/v1/localidades/municipios)

`brutos/` preserva os arquivos compactados originais, o layout e as respostas das APIs.
`fontes_manifesto.json` registra URLs, data de obtencao, tamanhos e hashes SHA-256.
RAIS, PNAD e Censo Superior nao foram incluidos nesta etapa: o pacote prioriza as
perguntas ja sustentadas pelo Radar e um complemento pronto sobre carreira em dados.
Eles, assim como Brasscom, Exame e similares, constam apenas como referencias na
matriz. Importar a matriz nao baixa automaticamente essas bases nem verifica seus
achados. A situacao de cada fonte esta em `registro_fontes.csv`.

## Reproduzir o pacote de dados

Execute na pasta deste pacote, com Python 3.11 ou superior:

```powershell
python -m pip install -r ../02_preparacao_dados/requirements_reproducao.txt
python scripts/run_preparation.py
```

Para reproduzir a pesquisa propria, use `scripts/prepare_grupo12.py` com os dois
XLSX locais, conforme [instrucoes de importacao](organizacao_e_integracao.md).
Nao publique respostas individuais; elas e os originais sao ignorados pelo Git.

O comando principal exige os originais e manifestos, nao baixa dados automaticamente.
Em outra maquina, `scripts/download_sources.py --output .` reconstroi as fontes
publicas. Obtenha a pesquisa propria por canal autorizado e registre seu manifesto
antes do pipeline completo. Para apenas conferir os exports, use `--mode validate`.

O [plano da etapa 02](../02_preparacao_dados/plano_de_preparacao.md) documenta
regras por variavel. O pipeline corrige o indicador de gestor do State of Data
para booleano anulavel, preservando ausentes e classificando gestores declarados
sem cargo tecnico como Gestao. Cache depende de codigo e hashes das fontes.
Resultados e ambiente estao em `qualidade/execucao_preparacao.json`.

Exemplo de leitura independente:

```python
import pandas as pd

caged = pd.read_parquet("tratados/caged_ti_pernambuco.parquet")
entradas = caged.loc[(caged["saldo"] == 1) & caged["salario_valido"]]
survey = pd.read_parquet("tratados/state_of_data_brasil.parquet")
```

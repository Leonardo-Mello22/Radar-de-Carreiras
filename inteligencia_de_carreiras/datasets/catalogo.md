# Catálogo de dados

Inventário do pacote local de inteligência de carreiras. Os volumes abaixo descrevem
os arquivos preparados, não resultados de modelos nem estimativas de toda a população.
Cada tabela tratada está disponível em CSV e Parquet com o mesmo nome-base.

Consulte a [decisão de organização e integração](organizacao_e_integracao.md) para
entender por que os datasets permanecem separados, e o
[registro de fontes](registro_fontes.csv) para distinguir bases importadas de
referências de contexto. Há três estudos de dados e uma matriz documental;
não existe uma tabela única de pessoas de todas as fontes.

## Tabelas de emprego formal

Fonte: Novo CAGED, arquivos CAGEDMOV de janeiro, fevereiro e março de 2025.
Unidade de observação: uma movimentação de admissão ou desligamento, não uma pessoa.

| Arquivo em `tratados/` | Linhas | Colunas | Recorte e uso |
| --- | ---: | ---: | --- |
| [caged_ti.parquet](tratados/caged_ti.parquet) | 118.564 | 62 | Brasil; base principal para salários e movimentações nas ocupações selecionadas. |
| [caged_ti_nordeste.parquet](tratados/caged_ti_nordeste.parquet) | 10.704 | 62 | Nordeste; comparação regional. |
| [caged_ti_pernambuco.parquet](tratados/caged_ti_pernambuco.parquet) | 2.305 | 62 | Pernambuco; foco territorial inicial do Radar. |

As famílias CBO selecionadas são 1236, 1425, 2122, 2123, 2124, 3171 e 3172.
O mapeamento de 27 ocupações está em
[cbo_ti_categorias.csv](auxiliares/cbo_ti_categorias.csv).
Esse recorte inclui algumas ocupações de automação e não equivale a todas as
carreiras de tecnologia.

Para estatísticas salariais, filtre `salario_valido=True` e use `salario_real`,
em reais mensais a preços de março de 2025. Para volumes de movimentação,
mantenha também os registros com salário sinalizado. A diferença entre admissões
e desligamentos deste pacote MOV não é o saldo oficial final com ajustes FOR/EXC.

## Tabelas de perfis e carreiras em dados

Fonte: State of Data Brazil 2024-2025, pesquisa voluntária e autodeclarada da área
de dados. Unidade principal: uma resposta de participante. Duas linhas exatamente
repetidas foram removidas da base original de 5.217 registros.

| Arquivo em `tratados/` | Linhas | Colunas | Recorte e uso |
| --- | ---: | ---: | --- |
| [state_of_data_carreiras.parquet](tratados/state_of_data_carreiras.parquet) | 5.215 | 51 | Campos selecionados e derivados de formação, experiência, vínculo, trabalho e salário. |
| [state_of_data_brasil.parquet](tratados/state_of_data_brasil.parquet) | 5.076 | 51 | Residentes no Brasil; universo inicial das análises de perfis e classificação. |
| [state_of_data_nordeste.parquet](tratados/state_of_data_nordeste.parquet) | 516 | 51 | Residentes no Nordeste; avaliar cobertura de cada variável. |
| [state_of_data_pernambuco.parquet](tratados/state_of_data_pernambuco.parquet) | 120 | 51 | Residentes em Pernambuco; atenção ao tamanho dos subgrupos. |
| [state_of_data_completo_normalizado.parquet](tratados/state_of_data_completo_normalizado.parquet) | 5.215 | 405 | 403 campos originais normalizados, mais identificação de linha e fonte. |
| [state_of_data_tecnologias.parquet](tratados/state_of_data_tecnologias.parquet) | 28.881 | 4 | Tabela longa: uma opção selecionada por respondente; não representa 28.881 pessoas. |

Os salários são intervalos declarados, não valores exatos. A experiência em dados
não representa necessariamente experiência total em TI. O percentual de uso de
tecnologia deve ser calculado com a elegibilidade e as respostas ao item na base
principal; contar apenas as linhas da tabela longa não fornece o denominador.

O alvo previsto para classificação é busca ativa declarada no item
`planos_mudar_emprego_6m`. Entre residentes no Brasil há 4.734 respostas válidas:
1.630 de busca ativa e 3.104 sem busca ativa. Ausentes não viram classe negativa.
O protocolo e as exclusões de preditores estão no
[plano de análise](../01_plano_de_analise/plano_de_analise.md).

## Pesquisa própria e desk research G12

O questionário tem 35 respostas a 12 perguntas, coletadas de 31/08 a 04/09/2026.
Há participantes de CC e Design; não é uma amostra representativa de todo o
mercado de TI. A matriz contém 21 registros documentais e 10 links preservados.

| Arquivo em `tratados/` | Linhas | Colunas | Unidade e finalidade |
| --- | ---: | ---: | --- |
| [pesquisa_grupo12_respostas.parquet](tratados/pesquisa_grupo12_respostas.parquet) | 35 | 31 | Uma resposta; necessidades, prioridades, expectativa e intenções. |
| [pesquisa_grupo12_respostas_longas.parquet](tratados/pesquisa_grupo12_respostas_longas.parquet) | 420 | 5 | Uma resposta por participante e pergunta; não são 420 participantes. |
| [pesquisa_grupo12_prioridades.parquet](tratados/pesquisa_grupo12_prioridades.parquet) | 101 | 4 | Uma seleção em Q08; o denominador é participantes que responderam ao item. |
| [matriz_pesquisa_grupo12.parquet](tratados/matriz_pesquisa_grupo12.parquet) | 21 | 12 | Uma referência/hipótese, com status declarado e alertas; não são microdados. |

Q07 tem três respostas fora do domínio Sim/Não; há uma expectativa salarial
sinalizada e um intervalo de experiência que não foi convertido em valor exato.
As âncoras de Q05 e o consentimento de divulgação precisam de confirmação.
O [guia de integração](organizacao_e_integracao.md) descreve cada regra.
As respostas individuais e os originais são locais e ignorados pelo Git.

## Apoio, agregados e qualidade

| Pasta ou arquivo | Finalidade |
| --- | --- |
| [fontes_manifesto.json](fontes_manifesto.json) | URLs, obtenção, tamanho e SHA-256 dos arquivos brutos. |
| [fontes_pesquisa_grupo12.json](fontes_pesquisa_grupo12.json) | Procedência, SHA-256 e volumes dos XLSX próprios. |
| [questionario_grupo12.csv](auxiliares/questionario_grupo12.csv) | Enunciados originais e correspondência de Q01 a Q12. |
| [dicionario_pesquisa_grupo12.csv](auxiliares/dicionario_pesquisa_grupo12.csv) | Tipos e definições dos 31 campos próprios. |
| `brutos/` | Originais compactados, layout oficial do CAGED e respostas das APIs do IBGE. |
| [dicionario_dados.csv](auxiliares/dicionario_dados.csv) | Definições, tipos, exemplos e ausências dos campos selecionados. |
| [mapa_colunas_state_of_data.csv](auxiliares/mapa_colunas_state_of_data.csv) | Correspondência entre perguntas originais e nomes normalizados. |
| [municipios_ibge.csv](auxiliares/municipios_ibge.csv) | Códigos e descrições territoriais do IBGE. |
| [ipca_deflatores.csv](auxiliares/ipca_deflatores.csv) | Índices e fatores usados na correção monetária. |
| [dominios_caged.json](auxiliares/dominios_caged.json) | Descrições dos códigos oficiais do CAGED. |
| [caged_indicadores_uf_area_mes.parquet](agregados/caged_indicadores_uf_area_mes.parquet) | 1.227 grupos por UF, área, mês e movimento, com contagens e quantis salariais. |
| [controle_caged_mensal.csv](qualidade/controle_caged_mensal.csv) | Reconciliação das 13.530.056 linhas brutas examinadas com o recorte de TI. |
| [relatorio_qualidade.json](qualidade/relatorio_qualidade.json) | Regras, nulos, contagens e sinalizações do tratamento. |
| [validacao_exports.json](qualidade/validacao_exports.json) | Resultado da conferência dos arquivos, fontes e regras do pacote. |
| [relatorio_pesquisa_grupo12.json](qualidade/relatorio_pesquisa_grupo12.json) | Alertas de domínio, expectativas, experiência, escala e privacidade. |
| [validacao_pesquisa_grupo12.json](qualidade/validacao_pesquisa_grupo12.json) | Reconciliação dos XLSX, conversões, prioridades e links. |
| [execucao_preparacao.json](qualidade/execucao_preparacao.json) | Pipeline completo: ambiente, código, nove fontes e produtos por SHA-256. |
| `modelagem/` | Escalas numéricas exploratórias e parâmetros; não reutilizar ajustes globais na avaliação de modelos. |
| [scripts/](scripts/) | Download, preparação e validação reproduzíveis. |

Os agregados mantêm os volumes, mas não apresentam quantis de salário quando
o grupo possui menos de 30 salários válidos. A base não identifica pessoas;
linhas iguais do CAGED foram preservadas porque podem ser eventos distintos.

## Uso e versionamento

Prefira Parquet para preservar tipos. Os CSV usam UTF-8 com BOM, vírgula,
ponto decimal e ausências vazias. Ao importar CSV, mantenha códigos geográficos,
CBO e competência como texto.

As bases CAGED, State of Data e pesquisa G12 devem permanecer separadas. Não concatene suas
linhas nem faça uma ligação de pessoas por cargo, UF ou salário. Não apresente
o pacote como uma série anual completa ou como o mercado atual de 2026.

Os dados completos estão nesta pasta local. `brutos/`, `tratados/`, `modelagem/`
e `.cache/` são ignorados pelo Git para evitar arquivos grandes e exposição de
respostas individuais. Eventuais agregados próprios em `agregados/pesquisa_grupo12/`
também ficam locais até revisão de privacidade.
Documentação, fontes, scripts, tabelas auxiliares e relatórios permitem reconstrução.
As instruções estão no [guia de preparação e reprodução](LEIA-ME.md).

A etapa 02 está documentada no [plano de preparação](../02_preparacao_dados/plano_de_preparacao.md)
e na [matriz de decisões por coluna](../02_preparacao_dados/matriz_preprocessamento.csv).
Na revisão, `atua_como_gestor` da base de carreiras passou a booleano anulável e
1.045 gestores declarados sem cargo técnico respondido passaram à categoria
`Gestao`. O número de participantes e o schema de 51 campos foram preservados.

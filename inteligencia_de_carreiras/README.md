# Inteligência de carreiras

Área de dados, análise, modelagem e comunicação visual do Radar de Carreira em TI.
O trabalho usa o Novo CAGED para emprego formal, o State of Data Brazil para
carreiras em dados e a pesquisa própria do Grupo 12 para necessidades e intenções.
A matriz do grupo registra referências e hipóteses. Os datasets permanecem
separados por fonte e unidade de observação, com um catálogo único.

## Comece aqui

Para revisar a solução completa, abra a [documentação final em PDF](08_documentacao_final/documentacao_final.pdf)
ou o [guia de entrega CC01-CC10](08_documentacao_final/guia_entrega.md).
O [índice geral da documentação](../docs/README.md) separa os materiais atuais
dos registros originais do Ciclo 1. Para abrir o dashboard com um ambiente próprio,
siga a [execução de AVD no README principal](../README.md#executar-o-dashboard-avd).

1. Leia o [plano de análise](01_plano_de_analise/plano_de_analise.md) ou a
   [versão em PDF](01_plano_de_analise/plano_de_analise.pdf).
2. Consulte o [guia dos datasets](datasets/LEIA-ME.md) e o
   [catálogo](datasets/catalogo.md) antes de escolher variáveis.
3. Acompanhe os critérios em [referências e critérios](00_referencias/README.md).
4. Consulte a [decisão de integração e privacidade](datasets/organizacao_e_integracao.md)
   e a [conferência da fase 01](01_plano_de_analise/verificacao_fase01.md).

## Organização e progresso

| Etapa | Pasta | Resultado esperado | Situação nesta área |
| --- | --- | --- | --- |
| 01 | [Plano de análise](01_plano_de_analise/) | Perguntas, métricas e visualizações justificadas | Completo documentalmente; revisão 1.1 com pesquisa G12 |
| 02 | [Preparação de dados](02_preparacao_dados/) | Plano de preparação e pipeline reproduzível | Concluída; pipeline completo validado, com alertas documentados |
| 03 | [Análise exploratória](03_analise_exploratoria/) | Notebook e interpretação dos gráficos | Executada; P1-P12 e análise multivariada, com resultados próprios restritos |
| 04 | [Regressão](04_regressao/) | Relações, tendências e resíduos | Executada; teste temporal, referência de mediana, seis gráficos e limites documentados |
| 05 | [Classificação](05_classificacao/) | Avaliação visual de classificadores | Executada; treino/teste separados, sete gráficos, métricas e baixo recall interpretados |
| 06 | [Dashboard e publicação](06_dashboard_e_publicacao/) | Dashboard inicial e plano de integração web | V1 local implementada e proposta pronta; hospedagem externa não realizada |
| 07 | [Validação](07_consolidacao_e_validacao/) | Dashboard consolidado e avaliação funcional | V1.1 consolidada e validada tecnicamente; revisão estruturada pelo grupo pendente |
| 08 | [Documentação](08_documentacao_final/) | Decisões, evidências e síntese dos achados | Concluída em PDF e Markdown; histórico, capturas, insights, reprodução e limites |

Os dez entregáveis de CC são cobertos por oito etapas: a etapa 06 reúne dashboard
inicial e proposta de integração, e a 07 reúne consolidação e versão quase final.
A matriz de critérios identifica cada entrega separadamente.

## Dados locais e reprodução

Os datasets completos estão em `datasets/`, com originais, dados tratados, versões
CSV/Parquet, dicionários, controles de qualidade e scripts de reprodução. Os arquivos
grandes e respostas individuais são mantidos localmente e ignorados pelo Git. Manifesto, catálogo, scripts,
dicionários e relatórios permitem reconstruir o pacote em outra máquina.

Na raiz de `inteligencia_de_carreiras/datasets`, execute:

```powershell
python -m pip install -r ../02_preparacao_dados/requirements_reproducao.txt
python scripts/run_preparation.py
```

Para importar os dois XLSX do grupo, use o comando descrito na
[documentação de integração](datasets/organizacao_e_integracao.md).
O pacote inclui 35 respostas a 12 perguntas e 21 registros de desk research,
com links, dicionário e controles de qualidade. A coleta própria ocorreu em 2026,
não no mesmo período do CAGED. Referências a RAIS, PNAD, INEP, Brasscom e Exame
não significam que esses microdados tenham sido baixados.

O [plano de preparação](02_preparacao_dados/plano_de_preparacao.md) justifica
as decisões por variável e registra a correção de gestão no State of Data.
A [matriz por coluna](02_preparacao_dados/matriz_preprocessamento.csv) e o
[relatório de execução](datasets/qualidade/execucao_preparacao.json) dão rastreabilidade.
O comando acima não baixa arquivos automaticamente; requer os originais e manifestos locais.

A [análise exploratória](03_analise_exploratoria/README.md) tem notebook executado,
HTML de leitura, gráficos, tabelas e interpretação. A
[síntese versionável](03_analise_exploratoria/sintese_achados.md) contém apenas
resultados das fontes públicas. A pesquisa G12 fica em saídas locais ignoradas pelo Git.

A [regressão salarial](04_regressao/README.md) compara modelos lineares com a
mediana do treino, reservando março de 2025 para avaliação. Inclui notebook executado,
HTML, diagnósticos de resíduos, métricas, recortes e testes. Previsões negativas
e erros de cauda são reportados; o modelo não é uma calculadora salarial pessoal.

A [classificação de busca ativa](05_classificacao/README.md) usa apenas o State
of Data, com referência majoritária, logística e árvore simples. Traz matrizes de
confusão, ROC, precision-recall e interpretação do desempenho limitado. A escolha
ocorre no treino; os escores individuais permanecem locais e fora do Git.

O [dashboard AVD](06_dashboard_e_publicacao/README.md), consolidado como v1.1,
integra as fontes em visões
separadas, com filtros, downloads agregados e evidências dos modelos. Usa um pacote
público compacto que não contém respostas individuais. A
[proposta de publicação](06_dashboard_e_publicacao/proposta_integracao_web.md)
define a hospedagem em Streamlit. A entrega inicial das oito etapas foi
versionada no commit `c789019`; a implantação externa continua pendente.

O pacote tem janeiro a março de 2025 do CAGED e a pesquisa State of Data 2024-2025.
Não representa todo o ano nem o mercado atual de 2026. O CAGEDMOV não inclui aqui
os ajustes CAGEDFOR/CAGEDEXC. A pesquisa não representa toda a população de TI.

## Relação com o restante do repositório

`app/`, `src/`, `notebooks/` e os documentos originais em `docs/` preservam o ciclo
existente; `docs/README.md` apenas acrescenta um índice geral de navegação.
O dashboard original continua lendo `data/processed` com seu recorte configurado.
Esta organização não altera automaticamente suas fontes, gráficos ou resultados.
A etapa 06 tem um novo entrypoint próprio e preserva esse aplicativo histórico.
A [etapa 07](07_consolidacao_e_validacao/README.md) consolida a versão 1.1 no mesmo
entrypoint, com persistência de filtros, contexto dos recortes, auditoria numérica
integral e avaliação funcional ampliada. O roteiro de revisão está pronto; ainda
não houve teste estruturado com colegas ou usuários.

Sequência atual: oito etapas com artefatos técnicos/documentais organizados,
dashboard v1.1 validado localmente e documentação final concluída. A entrega
inicial está versionada em `c789019`. Faltam revisão estruturada pelo grupo,
incorporação de feedback real e hospedagem externa com validação remota.
A prévia local não é um endereço público compartilhável.
Os relatórios e PDFs das etapas preservam o estado de seu momento de execução,
inclusive pendências de commit/push anteriores ao versionamento. A
[documentação final](08_documentacao_final/README.md) registra o fechamento técnico;
este índice e o README principal mantêm o estado posterior da entrega.

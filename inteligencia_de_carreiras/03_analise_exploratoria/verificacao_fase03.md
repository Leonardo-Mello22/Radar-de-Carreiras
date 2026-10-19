# Conferência da fase 03

Etapa 03, 14 de outubro de 2026. Escopo: análise exploratória da coluna CC,
Análise e Visualização de Dados, do documento de entregáveis fornecido pelo grupo.

## Critérios

| Componente solicitado | Evidência |
| --- | --- |
| Análise exploratória com visualizações | Notebook executado com salários, movimentos, regiões, escolaridade, perfis, tecnologias e pesquisa própria. |
| Distribuições e padrões | Quantis, boxplots, frequências, histogramas, composição de faixas e densidade bidimensional. |
| Correlações e relações | Spearman de idade/jornada e salário; relações por CBO/UF; expectativa e experiência em análise restrita. |
| Agrupamentos relevantes | KMeans em perfis agregados UF/área, com justificativa de variáveis, escalas, cobertura, silhouette e concordância entre sementes. |
| Interpretação textual | Explicação calculada em cada seção P1-P12/M1 e síntese das fontes públicas, com limites de interpretação. |
| Reprodução | Notebook de código, runner, ambiente fixado, hashes das fontes, registro de execução e testes. |

P8 foi respondida na parte exploratória: distribuição do alvo e associações
descritivas. Avaliação de classificadores (F1, ROC, matriz de confusão) pertence
à fase 05 e não é apresentada como realizada nesta entrega.

## Decisões analíticas

- CAGED usa salário válido nas distribuições, mas todas as movimentações nos volumes; há grupos salariais com n mínimo explícito.
- A comparação de admissão/desligamento usa mesma CBO, UF e mês; não significa progressão da mesma pessoa.
- Escolaridade é categórica. Idade não equivale a experiência. Correlações não demonstram causalidade.
- Perfis multivariados são agregados, não indivíduos; têm peso igual no ajuste. A projeção gráfica usa duas de três dimensões.
- O número de clusters é escolhido dentro de k=2 a 5. Silhouette e ARI não validam classes naturais ou segmentos preditivos de carreira.
- Coortes do State of Data se sobrepõem; faixas salariais não viram valores exatos; denominador de tecnologia é resposta válida por item.
- O alvo ausente não vira negativo. Nenhum classificador foi treinado e dados G12 não foram concatenados ao State of Data.
- Q05 não recebeu direção presumida, Q07 mantém alertas, expectativa sinalizada tem sensibilidade e experiência em intervalo não foi imputada.

## Privacidade e limites

O notebook executado e o HTML reúnem os resultados próprios do grupo e estão em
`resultados_locais/`, ignorados pelo Git. Algumas análises internas têm células
pequenas e pontos individuais: não publicar sem revisão de autorização,
agregação e risco de reidentificação. A síntese versionável exclui os resultados G12.

Os dados CAGED são de jan-mar/2025, sem ajustes FOR/EXC; State of Data é uma
amostra voluntária específica de dados; pesquisa própria não tem representatividade
comprovada. Não extrapolar para todo o ano ou mercado atual, não avaliar causalidade
e não tratar uso declarado de tecnologia como demanda de vagas.

## Evidências de execução

O [registro](registro_execucao.json) identifica células, figuras, dependências,
fontes e código. Os testes verificam limites amostrais, denominadores, alvo,
pareamento salarial, contagens, ausência de saídas privadas na área pública,
execução real das células e pixels não vazios dos gráficos.

Consultar o [notebook executado](resultados_locais/analise_exploratoria_executada.ipynb),
a [síntese](sintese_achados.md) e o [guia de reprodução](README.md).
Atender aos componentes da entrega não substitui a avaliação da professora.

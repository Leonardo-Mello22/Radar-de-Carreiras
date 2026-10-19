# Análise exploratória

Etapa 03: notebook com distribuições, associações, análise multivariada e
interpretação para P1-P12. Novo CAGED, State of Data e pesquisa G12 permanecem
separados por população, período e unidade de observação.

## Entrega

- [Notebook executado, com gráficos e interpretações](resultados_locais/analise_exploratoria_executada.ipynb).
- [Leitura em HTML, sem instalar Jupyter](resultados_locais/analise_exploratoria.html).
- [Notebook de código, sem saídas privadas](analise_exploratoria.ipynb).
- [Síntese das fontes públicas](sintese_achados.md).
- [Conferência da etapa 03](verificacao_fase03.md).
- [Ambiente, fontes e execução](registro_execucao.json).

A cópia executada e o HTML têm resultados da pesquisa própria e ficam locais,
ignorados pelo Git. Consentimento para divulgação não foi confirmado: não publicar
essas cópias ou os resultados G12 sem revisão. A versão sem saídas mantém o código
reproduzível no repositório. A entrega pode ser consultada nesta máquina.

## Conteúdo

| Seção | Universo e análise |
| --- | --- |
| P1-P4 | CAGED: quantis salariais, movimentos mensais, pares de mesmo cargo/UF/mês, escolaridade, densidade e correlações. |
| M1 | Perfis agregados UF/área com cobertura mínima; padronização, KMeans, silhouette e sensibilidade a semente. |
| P5-P8 | State of Data Brasil: coortes sobrepostas, faixas salariais, tecnologias por item e busca ativa declarada. |
| P9-P12 | Pesquisa G12 restrita: dificuldades, prioridades, intenção de uso, expectativa salarial e intenções distintas de mudança. |

O notebook mostra tabelas, gráficos e interpretação em cada seção. Tabelas longas
exibem as primeiras 16 linhas, com aviso; seus CSV completos ficam na pasta de
resultados correspondente. P3 mostra os oito pares de PE de maior cobertura;
P6 por cargo mostra os seis cargos de maior cobertura. Esses recortes visuais
não apagam as tabelas completas das análises disponíveis.

## Resultados e privacidade

`resultados_fontes_publicas/` contém tabelas e gráficos de CAGED/State of Data.
O nome indica a origem dos dados, não publicação automática da solução.
`resultados_locais/pesquisa_grupo12/` guarda as tabelas, gráficos e interpretação
próprios. Há células pequenas e dispersão interna nessa pasta: não são saídas
prontas para publicação. Revisar autorização, agregação e supressão complementar.

Não há junção de participantes entre fontes nem soma de recortes aninhados.
Valores ausentes não foram convertidos em respostas negativas. Comparações de
salário por grupo exigem n>=30; perfis multivariados exigem cobertura >=100 nas
três dimensões. A amostra própria não foi usada para treinar um classificador.

Regressão, classificação supervisionada, dashboard e publicação são etapas
posteriores. O notebook histórico da raiz continua preservado.

## Reproduzir

Na raiz do repositório, após a preparação completa da fase 02:

```powershell
python -m pip install -r inteligencia_de_carreiras/03_analise_exploratoria/requirements.txt
python inteligencia_de_carreiras/03_analise_exploratoria/executar_analise.py
python -m unittest discover -s inteligencia_de_carreiras/03_analise_exploratoria/tests -v
```

O runner registra um kernel Jupyter local nesta área, executa todas as células,
interrompe em erro e exporta o HTML com figuras embutidas. Não altera a instalação
global de kernels. Versões são fixadas; as quatro tabelas utilizadas são conferidas
contra os hashes da preparação. Fontes privadas devem ser fornecidas por canal
autorizado em outra máquina, sem respostas simuladas.

O notebook também pode ser aberto e executado pelo Jupyter/VS Code na raiz do
repositório ou nesta pasta. Em ambiente restrito, `TEMP`/`TMP` devem apontar para
uma pasta gravável. Não é necessário iniciar servidor para ler o HTML exportado.

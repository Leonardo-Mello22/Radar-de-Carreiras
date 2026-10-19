# Relatório de Consolidação

Radar de carreiras, versão 1.1. Referência: 19/10/2026. Escopo: CC08 (dashboard
consolidado) e CC09 (versão quase final). Evidências geradas nos JSONs desta pasta.

## Resultado e Aceitação

**Versão quase final tecnicamente validada em ambiente local, pronta para revisão
do grupo.** A avaliação estruturada por usuários ainda não ocorreu. O solicitante
relatou ter visto a prévia e achado boa, mas informou que enviará aos amigos depois.
Essa impressão informal não é tratada como teste de usabilidade ou aprovação final.

Execução de referência da v1.1: **111 testes aprovados** (92 anteriores + 19 desta
etapa), **22 verificações de navegador** (9 iniciais + 13 ampliadas) e **65.761
comparações numéricas sem divergências** em 4.408 recortes CAGED e 675 State of Data.
Os JSONs registram data, código, pacote e evidências desta execução.

| Critério | Evidência | Situação |
| --- | --- | --- |
| Consolidar dados, gráficos e textos | Um único entrypoint 1.1, fontes separadas, recorte ativo explícito e avisos metodológicos | Implementado |
| Incorporar feedback | `feedback_e_ajustes.csv` distingue impressão real, revisão técnica e avaliação futura | Feedback estruturado pendente |
| Conferir os números | Auditoria integral contra CAGED e State of Data tratados, hashes de origem e quantis independentes | Executado; resultado em `resultados/auditoria_numerica.json` |
| Testar filtros e interações | AppTest, download de CSV pelo navegador, persistência e restauração isolada por fonte | Executado |
| Testar telas pequenas | Quatro visões em 360x800, 768x1024 e 1440x1000, além do QA inicial em 390x844 | Executado no Chromium |
| Versão quase final rastreável | `registro_execucao.json`, hashes de código/pacote/evidências | Gerado automaticamente |
| Validar com o grupo e em URL pública | Roteiro pronto; não há estudo nem implantação externa concluídos | Pendente |

## Alterações Aplicadas

1. Filtros de emprego e perfis e seleção do modelo permanecem na sessão ao navegar.
   Restaurar filtros só altera a fonte corrente; sessões diferentes continuam isoladas.
2. Local, período, área e ocupação/CBO ficam explícitos fora do painel de filtros.
   Nos perfis, senioridade e trabalho também aparecem quando o painel está fechado.
3. Recortes sem respostas não mostram métricas antigas e mantêm contexto e restauração.
   A busca ativa informa quando a base válida do item é inferior a 30, mesmo se o
   total do recorte for maior. Dados ausentes não viram zero ou resposta negativa.
4. Indicadores centrais ganharam ajuda contextual sobre preços de março/2025,
   denominadores e diferença MOV. Não foram alteradas as métricas dos modelos.
5. O carregador rejeita manifesto sem hashes dos arquivos obrigatórios, tamanho
   divergente ou mínimo estatístico incompatível, além das verificações anteriores.
6. A navegação exige uma visão selecionada. Nenhum modelo foi retreinado ou
   transformado em recomendador individual; alertas de baixo recall e previsões
   negativas permanecem visíveis.
7. Downloads usam identidade vinculada ao conteúdo e não provocam novo rerun.
   O QA espera o botão do recorte atual e compara o arquivo efetivamente baixado,
   evitando considerar um botão da renderização anterior como evidência válida.
8. A inspeção visual identificou que uma ocupação específica com Todas as áreas
   podia deixar vazio o gráfico salarial, apesar de indicadores válidos. A seleção
   de grupos foi corrigida para consultar ocupações nesse caso e ganhou teste de regressão.
9. Restaurar filtros passa a atribuir explicitamente os valores padrão, em vez
   de apenas remover as chaves. Isso evita que controles persistentes do navegador
   reenviem seleções antigas ao sair e voltar à visão. O QA confere essa retomada.

A persistência usa a API nativa `persist_state="session"` do Streamlit 1.66.0,
conforme a [documentação oficial de selectbox](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox).
Ela vale para a sessão, não é persistência em conta, banco de dados ou link compartilhável.

## Conferência Numérica

`auditar_numeros.py` verifica todas as combinações dos cubos publicados, inclusive
recortes vazios. Não usa `summarize_caged`, `caged_cube` ou `sod_cube` do gerador.
Os salários são conferidos com `pandas.Series.quantile` sobre os eventos elegíveis;
não se faz média de medianas ou soma de geografias sobrepostas.

- CAGED: chaves completas/únicas, eventos, admissões/desligamentos, bases salariais,
  diferença MOV e p10/p50/p90; supressão quando n válido é inferior a 30.
- State of Data: chaves, respondentes, bases por item, duas respostas positivas
  explícitas de busca ativa, categorias pequenas agrupadas e tecnologias com
  denominadores próprios. Ausentes e ramificações permanecem ausentes.
- Integridade: fontes tratadas e pacote identificados por SHA-256; nenhum agregado
  é reconstruído a partir de dados diferentes dos registrados no manifesto.
- Modelos: resultados congelados das etapas 04 e 05 continuam verificados pelo
  pacote; testes e navegador conferem os avisos, a referência majoritária e a troca
  de classificadores. A auditoria integral dos cubos não significa novo treino.

Controles: Brasil CAGED = 61.047 admissões, 57.517 desligamentos, diferença MOV
3.530; PE = 1.284 admissões e 1.021 desligamentos. State of Data Brasil = 5.076
respostas, das quais 4.734 respondem ao alvo e 1.630 declaram busca ativa.

Contagens e comparações efetivamente executadas, divergências e tolerâncias
constam no relatório numérico, não são números preenchidos manualmente como prova.
A auditoria confronta **dados tratados**, não revalida todos os arquivos originais
do MTE nem a veracidade de cada autodeclaração.

Três respostas do State of Data têm UF ausente: entram no total Brasil, sem serem
atribuídas a uma UF fictícia. Por isso, somar as UFs não recompõe esse total.

## Testes e Evidências

O comando `validar_consolidacao.py` executa a auditoria, nove checks de navegador
da etapa 06, a cobertura ampliada desta etapa, as suites anteriores e os 19 novos
testes. O total efetivo fica em `registro_execucao.json`. O download é realmente
baixado e comparado ao recorte escolhido, incluindo contagens e quantis.

O navegador verifica ausência de erros JavaScript, gráficos não vazios e largura
da página nas quatro visões. Há uma verificação básica de operação por teclado.
Capturas aguardam o fim da renderização. Isso **não é certificação WCAG**, revisão
com leitor de tela ou garantia em Safari/Firefox e todos os tamanhos de dispositivo.

## Pendências e Limitações

| Item | Responsável/próxima ação | Impacto |
| --- | --- | --- |
| Revisão estruturada por colegas | Grupo: executar `roteiro_revisao.md`, registrar comentários reais | Não declarar validação com usuários ainda |
| Documentação final | Etapa 08: reunir decisões, insights e referências de entrega | Ainda não concluída nesta etapa |
| Commit/push | Solicitante/grupo: revisar e autorizar envio | Nada enviado nesta etapa |
| Hospedagem externa | Grupo: configurar Streamlit e testar a URL remota | Prévia local não acessível aos amigos por este endereço |
| Divulgação G12 | Grupo: definir autorização e escopo | Respostas individuais continuam fora do dashboard e do Git |

O CAGED cobre emprego formal, o trimestre disponível não mede tendência atual
de 2026 e MOV não é saldo ajustado. A pesquisa voluntária não representa todo TI.
As fontes não formam uma única população. Regras de tamanho mínimo não garantem
representatividade ou anonimização universal. Persistência em URL, municípios,
leitores de tela e outros navegadores ficam fora do escopo validado desta versão.

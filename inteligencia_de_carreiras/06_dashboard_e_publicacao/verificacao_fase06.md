# Conferência da Etapa 06

19 de outubro de 2026. Entregas: CC06, dashboard interativo inicial; CC07,
proposta de integração visual e publicação web. Não equivale à aprovação docente.

## Critérios e Evidências

| Critério | Evidência | Situação |
| --- | --- | --- |
| Dashboard inicial utilizável | `dashboard.py`, Streamlit, quatro visões | Implementado localmente |
| Filtros e segmentação | Região, UF, período, área/ocupação; senioridade/modelo na pesquisa | Testado |
| Visualizações integradas | Quantis, fluxos, evolução, faixas, tecnologias, formação/vínculo e modelos | Implementado |
| Narrativa visual e limites | Indicadores, fonte/período, n válido, avisos de caudas, baixo recall e ausência | Implementado |
| Organização das páginas | Emprego formal, perfis em dados, modelos e fontes | Documentado e implementado |
| Ferramenta de publicação | Streamlit Community Cloud, entrypoint e dependências definidos | Proposta pronta |
| Processo de publicação | Autorização, GitHub, conta Streamlit, implantação e verificação remota | Planejado; não executado |
| Privacidade | Pacote só de agregados; sem IDs, G12 ou escores individuais | Verificado |
| Reprodução | Gerador de agregados, manifesto/hashes e versões fixadas | Implementado |

## Validação Local

- 23 testes novos de agregação, integridade, exportação e interface com AppTest.
- Nove verificações no Chromium: recorte inicial, filtro regional, download,
  separação de fontes, imagens dos modelos, limites, fontes, celular e gráficos.
- Desktop 1440x1000 e celular 390x844, sem overflow horizontal ou erros JavaScript.
- Capturas em `evidencias/`; código testado registrado por hash no relatório do navegador.
- O relatório completo das suites e versões está em `registro_execucao.json`;
  a verificação conjunta das etapas anteriores é feita por `validar_entrega.py`.
- O pacote tem aproximadamente 0,49 MB, com hashes por arquivo; não exige os
  datasets completos para executar o app em outra máquina.

Conferências de números: PE tem 1.284 admissões, 1.021 desligamentos e mediana
de admissão de aproximadamente R$3.165 em janeiro-março/2025. Brasil tem 61.047
admissões; pesquisa em dados tem 5.076 respostas no país e 4.734 alvos respondidos.
Esses números são apenas controles desta versão; o manifesto identifica a origem.

O QA confirmou filtros dependentes, restauração, recorte insuficiente e download
somente agregado. O painel de filtros é recolhível para não ocupar a primeira
tela inteira do celular. Capturas esperam o fim da renderização do Streamlit,
evitando registrar elementos transitórios da visão anterior.

## Privacidade e Limites

Quantis de cada recorte vêm dos eventos elegíveis, nunca da média de quantis.
Os períodos e as populações são separados. Contagens CAGED mantêm salários
sinalizados; estatísticas salariais não os usam. Faixas de salário autodeclarado
não viram remuneração exata. Tecnologias mantêm o denominador válido do item.

Grupos pequenos não exibem estatísticas. Categorias raras na pesquisa são
reunidas como Outras respostas. As regras não comprovam representatividade ou
anonimização universal. G12 não foi publicado; autorização continua pendente.
O classificador de baixo recall e a regressão com previsões negativas mantêm
seus alertas. Nenhum modelo foi convertido em ferramenta individual de decisão.

## Pendências Claras

**Não há hospedagem pública externa concluída.** É necessária autorização para
commit/push e configuração da conta Streamlit. A proposta descreve esse caminho,
mas não substitui a implantação e a checagem da URL remota. Nenhum commit foi feito.

O aplicativo histórico não foi substituído. A [etapa 07](../07_consolidacao_e_validacao/README.md)
agora registra a consolidação técnica v1.1 e avaliação funcional ampliada no mesmo
entrypoint. Feedback estruturado de usuários permanece pendente; a etapa 08 reúne
a documentação final. Não há declaração de validação com participantes ou
acessibilidade completa sem que essas avaliações ocorram.

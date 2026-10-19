# Guia de Entrega e Revisão

Radar de carreiras v1.1. Referência: 19/10/2026. As oito etapas têm artefatos
técnicos/documentais; feedback estruturado e publicação externa permanecem pendentes.

## Mapa de Evidências

| Critério | Material principal | Estado |
| --- | --- | --- |
| CC01 - Plano de análise | [Plano e perguntas](../01_plano_de_analise/plano_de_analise.md) | Documentado |
| CC02 - Preparação | [Plano e pipeline](../02_preparacao_dados/README.md) | Executado e validado |
| CC03 - Exploração | [Notebook e leitura pública](../03_analise_exploratoria/README.md) | Executado; saídas G12 restritas |
| CC04 - Regressão | [Notebook executado em HTML](../04_regressao/resultados/regressao_salarial.html) | Executado e interpretado |
| CC05 - Classificação | [Notebook executado em HTML](../05_classificacao/resultados/classificacao_busca_ativa.html) | Executado e interpretado; desempenho limitado |
| CC06 - Dashboard inicial | [Entrypoint e execução](../06_dashboard_e_publicacao/README.md) | Implementado localmente |
| CC07 - Integração web | [Proposta de publicação](../06_dashboard_e_publicacao/proposta_integracao_web.md) | Proposta pronta; implantação pendente |
| CC08 - Dashboard consolidado | [Decisões, ajustes e capturas](../07_consolidacao_e_validacao/relatorio_validacao.md) | Consolidado tecnicamente; feedback estruturado pendente |
| CC09 - Versão quase final | [Validação e roteiro de revisão](../07_consolidacao_e_validacao/README.md) | Avaliação funcional local; revisão do grupo e remota pendentes |
| CC10 - Documentação final | [PDF](documentacao_final.pdf) e [Markdown](documentacao_final.md) | Concluída e conferida |

O [documento original de critérios](../00_referencias/criterios_avd_cc.pdf) continua
sendo a rubrica oficial. Não foram adicionadas como exigências de CC as entregas
das colunas de Design. Nenhum status equivale à aprovação da professora.

## Como os Colegas Abrem

Depois que o grupo disponibilizar o repositório atualizado, usar Python 3.12 e um
ambiente virtual. Na raiz do repositório, executar:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
cd inteligencia_de_carreiras/06_dashboard_e_publicacao
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py --global.developmentMode false --server.port 8502
```

Se a ativação for bloqueada pela política local, usar diretamente o Python do
ambiente virtual, sem precisar mudar a política do sistema. Se a porta 8502 estiver
ocupada, escolher outra porta. `127.0.0.1` só funciona na própria máquina.

O entrypoint correto desta entrega é o de `inteligencia_de_carreiras`, não
`app/dashboard.py` do ciclo histórico. O pacote `dados_publicos/` é suficiente para
abrir o app. Datasets grandes e respostas privadas não são exigidos nem devem ser
adicionados ao Git só para executar a interface.

## Checklist de Fechamento

- [x] Planos, exploração, regressão e classificação organizados por etapa.
- [x] Dashboard consolidado, fontes separadas e métricas com limites explícitos.
- [x] Validação técnica local com 111 testes, 22 verificações no Chromium e auditoria sem divergências.
- [x] Documentação final em PDF e Markdown, com histórico, capturas e insights.
- [x] Pesquisa G12 e resultados individuais mantidos fora do pacote público.
- [ ] Revisar alterações versionáveis antes de qualquer commit.
- [ ] Fazer commit/push quando o solicitante pedir e disponibilizar a versão aos colegas.
- [ ] Aplicar o [roteiro de revisão real](../07_consolidacao_e_validacao/roteiro_revisao.md).
- [ ] Registrar observações reais e decisões no [histórico de feedback](../07_consolidacao_e_validacao/feedback_e_ajustes.csv).
- [ ] Configurar a hospedagem Streamlit e validar a URL externa, caso o grupo vá publicá-la.
- [ ] Após mudanças funcionais, repetir a etapa 07 e regenerar a documentação 08.

Essa lista separa produção técnica de avaliação por pessoas e publicação. A etapa
08 não envia documentos à disciplina, mensagens aos colegas ou arquivos ao GitHub.

## O Que Não Enviar

Não incluir originais de pesquisa, respostas individuais, previsões por evento,
escores por participante, logs, caches, ambientes virtuais e pastas `resultados_locais`.
As regras estão no `.gitignore`. Manter resultados públicos agregados, scripts,
notebooks autorizados, manifestos, gráficos e documentação. Antes de divulgar
qualquer resultado G12, confirmar autorização e escopo com o grupo.

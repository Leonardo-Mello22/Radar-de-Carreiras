# Consolidação e Validação

Etapa 07, CC08 e CC09. Versão 1.1 do Radar de carreiras, consolidada para revisão
do grupo. **Validação técnica local concluída; teste estruturado com participantes
e validação da hospedagem externa ainda pendentes.** Não equivale à aprovação docente.

## Entregas

- [Relatório de consolidação e critérios](relatorio_validacao.md).
- [Registro de feedback e ajustes](feedback_e_ajustes.csv).
- [Roteiro para revisão do grupo](roteiro_revisao.md).
- [Execução técnica e hashes](registro_execucao.json).
- [Auditoria numérica integral](resultados/auditoria_numerica.json).
- [Verificação ampliada no navegador e capturas](evidencias/).

O aplicativo continua em [dashboard.py](../06_dashboard_e_publicacao/dashboard.py).
Não há uma segunda cópia do dashboard: a etapa 06 mantém o ponto de entrada;
esta pasta concentra consolidação, testes e evidências da versão quase final.

## Reprodução

Na raiz do repositório, use Python 3.12 e instale as dependências do dashboard:

```powershell
python -m pip install -r inteligencia_de_carreiras/06_dashboard_e_publicacao/requirements_testes.txt
python -m playwright install chromium
python -m streamlit run inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py --global.developmentMode false --server.port 8502
```

Para validar todas as etapas, instale o conjunto de dependências referenciadas
sem duplicar suas versões. Em outro terminal, usando o mesmo ambiente:

```powershell
python -m pip install -r inteligencia_de_carreiras/07_consolidacao_e_validacao/requirements_validacao.txt
python inteligencia_de_carreiras/07_consolidacao_e_validacao/validar_consolidacao.py --url http://127.0.0.1:8502
```

O comando executa auditoria dos quatro cubos, QA inicial/ampliado e suites das
etapas anteriores e desta etapa. Requer os datasets tratados locais e
os resultados das etapas anteriores; **servir o app não requer microdados**.
Use `--browser-executable CAMINHO` se já houver Chromium instalado fora do padrão.

As evidências começam como `EM_TESTE`/`EM_EXECUCAO`; falha não vira aprovação.
O registro final relaciona código, pacote, relatórios e capturas por SHA-256.
Executar novamente substitui as evidências, sem publicar, retreinar ou fazer commit.

## Organização

| Artefato | Finalidade |
| --- | --- |
| `auditar_numeros.py` | Comparar todos os recortes publicados com as fontes tratadas, sem chamar o gerador de agregados |
| `verificar_navegador.py` | Conferir persistência, CSV real, ausência de dados, teclado e três larguras de tela |
| `tests/test_consolidacao.py` | Regressão funcional e integridade do manifesto |
| `validar_consolidacao.py` | Porta única de aceitação técnica e registro da execução |
| `resultados/` | Auditoria agregada, sem registros individuais |
| `evidencias/` | Capturas e resultado do QA automatizado |

## Próximos Passos

A etapa 08 reúne a documentação final. Depois, revisar o conteúdo versionável,
realizar commit/push quando solicitado e enviar ao grupo. Os colegas podem executar
o dashboard com o pacote público; `127.0.0.1` só funciona nesta máquina. Após revisão,
registrar comentários reais, corrigir o que for necessário e repetir a validação.
A hospedagem Streamlit permanece planejada na etapa 06, não implantada.

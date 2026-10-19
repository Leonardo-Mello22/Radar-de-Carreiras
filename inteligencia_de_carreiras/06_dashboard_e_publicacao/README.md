# Dashboard e Publicação

Etapa 06. Dashboard em Streamlit e proposta de integração visual/publicação web.
O mesmo entrypoint foi consolidado como v1.1 na [etapa 07](../07_consolidacao_e_validacao/README.md),
que concentra a auditoria integral e a validação funcional ampliada.
Cobre CC06 e CC07. O aplicativo histórico em `app/dashboard.py` permanece preservado;
o novo ponto de entrada desta área é `dashboard.py`.

## Entregas

- [Proposta de integração e publicação](proposta_integracao_web.md).
- [Conferência dos critérios e evidências](verificacao_fase06.md).
- [Aplicativo v1](dashboard.py).
- [Manifesto dos agregados públicos](dados_publicos/manifesto.json).
- [Evidências visuais e teste no navegador](evidencias/).

## Executar

Na raiz do repositório, com Python 3.12, use um ambiente exclusivo da área AVD
para manter separadas as dependências da aplicação existente:

```powershell
python -m venv inteligencia_de_carreiras/.venv
$python = ".\inteligencia_de_carreiras\.venv\Scripts\python.exe"
& $python -m pip install -r inteligencia_de_carreiras/06_dashboard_e_publicacao/requirements.txt
& $python -m streamlit run inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py --server.port 8502
```

A URL local é mostrada pelo Streamlit; escolha outra porta se 8502 estiver ocupada.
Ela não é uma publicação pública. O app usa o pacote versionável de agregados,
não depende dos datasets grandes ou privados presentes em outra pasta. Não baixa
arquivos, não treina modelos e não envia respostas a serviços externos.

## Visões

| Visão | Conteúdo e filtros |
| --- | --- |
| Emprego formal | Região, UF, período, área e ocupação; mediana/p10/p90, volumes e evolução mensal |
| Perfis em dados | Região, UF, senioridade e modelo de trabalho; faixas salariais, tecnologias, formação e vínculo |
| Modelos | Evidências congeladas das etapas 04/05; regressão e classificação com limites e erros visíveis |
| Fontes | Procedência, unidades, períodos, privacidade e download do manifesto |

O padrão inicial é Pernambuco para CAGED e Brasil para State of Data. Filtros de
uma fonte não alteram as métricas reservadas dos modelos. Ausências de pesquisa
não viram respostas negativas. Estatísticas salariais e comparações exigem n>=30;
contagens continuam disponíveis. Há estados específicos para recorte vazio e insuficiente.

## Organização

```text
06_dashboard_e_publicacao/
  dashboard.py                  interface Streamlit
  dados.py                      leitura validada, filtros e exportação segura
  preparar_pacote.py             geração reproduzível dos agregados públicos
  requirements.txt              dependências de execução
  requirements_testes.txt        dependências adicionais de QA
  proposta_integracao_web.md     páginas, decisões visuais e plano de hospedagem
  verificacao_fase06.md          critérios, testes e limites
  dados_publicos/                pacote compacto versionável; sem microdados
  tests/                        regras e interface com AppTest
  verificar_navegador.py         QA desktop/mobile com Playwright
  validar_entrega.py             validação conjunta e registro das suites
  evidencias/                   capturas e relatório de navegador
  resultados_locais/            logs e estado de execução; fora do Git
```

## Regerar e Testar

Com os datasets preparados e as etapas 04/05 executadas, na raiz, use o mesmo
interpretador `$python` definido na seção Executar:

```powershell
& $python inteligencia_de_carreiras/06_dashboard_e_publicacao/preparar_pacote.py
& $python -m pip install -r inteligencia_de_carreiras/06_dashboard_e_publicacao/requirements_testes.txt
& $python -m unittest discover -s inteligencia_de_carreiras/06_dashboard_e_publicacao/tests -v
& $python -m playwright install chromium
& $python inteligencia_de_carreiras/06_dashboard_e_publicacao/verificar_navegador.py --url http://localhost:8502
```

O último comando exige o servidor já iniciado; ajuste a URL se usar outra porta.
Os testes de integração usam os
datasets locais apenas para conferir os agregados; o app publicado não os exige.
`validar_entrega.py` reúne as suites das etapas anteriores e exige também as
dependências das etapas 02-05; não é necessário para servir o dashboard.
O pacote tem hashes por arquivo e origem. Quantis de cada combinação de filtros
são calculados diretamente dos eventos elegíveis, nunca combinando percentis.
Na pesquisa, cada pergunta mantém seu denominador e categorias pequenas são
reunidas como Outras respostas, sem criar participantes adicionais.

## Publicação

**Dashboard local implementado; hospedagem externa ainda não executada.** A etapa
inclui a proposta completa de publicação no Streamlit Community Cloud. A entrega
inicial das oito etapas está versionada no commit `c789019`; isso não publica
automaticamente o dashboard. Vincular a conta de hospedagem e realizar o teste
remoto continuam pendentes e dependem de acesso do grupo. Os registros de execução
preservam a situação anterior ao versionamento, sem reescrever as evidências.

Somente `dados_publicos/` é usado para servir dados. Pesquisa G12, originais,
respostas individuais e escores por participante não entram nesta versão. A etapa 07
concluiu a consolidação técnica; incorporar feedback estruturado de colegas/usuários
continua pendente até a revisão real do grupo.

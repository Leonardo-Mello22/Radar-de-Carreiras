# Proposta de Integração e Publicação Web

Radar de carreiras. Etapa 06, versão 1.0. 19 de outubro de 2026.

## Objetivo e Estado

Comunicar os achados das etapas 01-05 em um dashboard navegável, preservando
unidade, período, população e limites de cada fonte. A v1 foi implementada em
Streamlit, a mesma ferramenta do aplicativo histórico. A integração desta área
tem entrada própria; não substitui silenciosamente o recorte do Ciclo 1.

Entrega desta etapa: aplicativo local v1 e esta proposta. **Não há URL pública
externa criada.** Não foi feito commit/push nem vínculo com conta de hospedagem.
A publicação real e o feedback de usuários deverão ser registrados em seguida.

## Arquitetura de Páginas

| Visão | Pergunta e informação prioritária | Filtros | Comunicação e saída |
| --- | --- | --- | --- |
| Emprego formal | Salários de admissão e fluxos de TI | Pernambuco/NE/Brasil, UF, trimestre/mês, área, ocupação | Quantis exatos, barras de eventos, mediana mensal e CSV agregado |
| Perfis em dados | Composição declarada da área de dados | Região, UF, senioridade, modelo de trabalho | Faixas salariais ordenadas, tecnologias por item, formação/vínculo e CSV agregado |
| Modelos: salários | Limites da aproximação linear no teste temporal | Visão de análise, sem recalcular o teste | MAE/RMSE/R², observado/previsto, resíduos e alerta de previsões negativas |
| Modelos: busca ativa | Que erros os classificadores cometem | Classificador, sem retreinar ou reescolher | Acurácia/precisão/recall/F1, matriz, ROC, PR/AP e falsos negativos |
| Fontes | O que os dados permitem afirmar | Sem filtros de pessoas | Período, unidade, privacidade, procedência e manifesto |

Não há página inicial de marketing. A primeira tela é o recorte de emprego formal
de Pernambuco, já carregado. A pesquisa nacional de dados começa em Brasil. A
navegação permanece no topo; filtros dependentes evitam UF incompatível com região
e ocupação fora da área selecionada. Restaurar filtros e exportar recortes são ações
explícitas. Casos vazios e insuficientes recebem estados distintos.

## Organização Visual

- Preservar a marca existente, com aro de radar e paleta de `app/theme.py`.
  Branco e cinzas estruturam a informação; laranja destaca a série principal.
- Cabeçalho compacto, navegação e filtros antes dos indicadores. Sem cartões de
  marketing, seções decorativas ou títulos que disputem espaço com o dado.
- Indicadores com unidades explícitas e tamanhos estáveis; títulos curtos e
  notas de fonte/período junto dos gráficos. Uso em celular com reflow de colunas.
- Posição/comprimento para comparar valores; p10-p90 e mediana para mostrar
  dispersão; barras com origem zero; tooltip com rótulo completo e denominador.
- Matrizes com contagem e orientação observada/prevista. Curvas de classificação
  usam probabilidades já avaliadas, não classes cortadas para calcular ROC/AP.
- Cor não é o único identificador: rótulos, legendas e tooltip complementam o
  destaque. Mensagens de limitação ficam junto da análise correspondente.

Os gráficos de modelos não reagem aos filtros de emprego/perfis, pois são
evidências de testes reservados, não novos modelos ajustados por recorte.
O seletor de classificador permite comparar, não substituir a escolha da validação.

## Integração de Dados

Fluxo: fontes verificadas da etapa 02 -> agregação para os filtros suportados ->
manifesto e hashes -> dashboard somente de leitura -> exportações agregadas.

`preparar_pacote.py` lê o CAGED e State of Data preparados, confere seus hashes
e calcula os quantis de cada combinação diretamente dos eventos correspondentes.
Não calcula média de medianas ou percentis. O pacote permite região/UF, quatro
períodos e área/ocupação sem distribuir os eventos individuais.

Na pesquisa, frequências e tecnologias preservam denominadores específicos.
Nulos não viram Não. Faixas não viram salários exatos. Categorias pequenas são
reunidas para apresentação; comparações com n<30 são suprimidas. Essa regra
operacional não prova representatividade, independência ou anonimização universal.

Artefatos dos modelos são copiados somente quando seus hashes correspondem às
execuções validadas das etapas 04/05. Não há treinamento no servidor web, cálculo
individual de risco ou upload de dados do visitante. O pacote não contém IDs,
microdados, respostas G12 ou escores por participante. Arquivos de dados grandes
continuam locais/ignorados. Modelos mostram inclusive desempenho desfavorável.

## Hospedagem Proposta

**Ferramenta:** Streamlit Community Cloud. O repositório já é Python/Streamlit;
a execução não exige serviços de inferência, banco externo ou chaves de API.

**Entrada:** `inteligencia_de_carreiras/06_dashboard_e_publicacao/dashboard.py`.
Dependências mínimas e fixadas em `requirements.txt` da mesma pasta. O pacote
de agregados e a identidade `app/theme.py` ficam versionados no repositório.
Os caminhos partem de `__file__`, sem depender de diretório Windows ou do cwd.
O Community Cloud inicia no diretório raiz do repositório e procura dependências
na pasta da entrada e depois na raiz, conforme a
[organização de arquivos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
e a [documentação de dependências](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

### Sequência de Publicação

1. Confirmar autorização do grupo, conta de hospedagem e acesso ao repositório
   `Leonardo-Mello22/Radar-de-Carreiras`. Não presumir acesso administrativo.
2. Revisar o diff, executar testes, conferir o manifesto e confirmar que o Git
   não inclui dados privados ou `resultados_locais/`.
3. Criar commit/branch revisados e enviar ao GitHub somente com autorização.
   Registrar SHA, autor, data e evidências; não considerar arquivo apenas local
   como já disponível no servidor remoto.
4. Na conta Community Cloud, conectar o GitHub autorizado e selecionar repositório,
   branch e a entrada acima. Definir visibilidade conforme as permissões da conta.
5. Instalar as versões fixadas, carregar apenas os agregados e conferir os logs.
   O [fluxo oficial de implantação](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
   documenta a seleção do repositório e arquivo de entrada.
6. Abrir a URL emitida pelo serviço e repetir os testes de números, filtros,
   downloads, assets, erros e celular. Só então registrar publicação concluída.
7. Registrar URL, SHA implantado, versão dos agregados e feedback na etapa 07.

Se o Community Cloud não estiver disponível, a alternativa é container/servidor
Python autorizado, preservando o mesmo entrypoint e pacote. Não migrar para um
host estático que não execute o servidor Streamlit. A alternativa não foi implantada.

## Aceitação e Próximo Ciclo

Critérios da v1: navegação nas quatro visões, filtros coerentes, números idênticos
aos agregados, recortes insuficientes sem estatísticas indevidas, downloads sem
identificadores, fontes visíveis e layout sem overflow no desktop/celular.
Testes usam AppTest, ferramenta oficial para exercitar apps sem refatoração de UI,
conforme a [documentação de testes](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest),
além de QA no navegador real.

A [etapa 07](../07_consolidacao_e_validacao/README.md) consolida a v1.1 com
persistência de filtros na sessão, clareza dos recortes, auditoria integral e QA
funcional ampliado. A revisão estruturada com participantes e a checagem da URL
remota continuam pendentes. O registro distingue ajustes técnicos de feedback real.
Comparações municipais e compartilhamento de filtros por URL não foram implementados.
A validação técnica local não substitui essas avaliações nem autoriza publicar G12.

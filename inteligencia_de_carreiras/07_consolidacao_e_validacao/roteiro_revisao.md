# Roteiro de Revisão do Grupo

**Planejado, ainda não aplicado.** Duração sugerida: 10 a 15 minutos por colega.
Objetivo: identificar problemas de entendimento e navegação, não medir desempenho
de contratação nem coletar dados pessoais. Não preencher resultados antecipadamente.

## Acesso

Após receber o repositório atualizado, seguir o README da etapa 06 para executar
o entrypoint desta área com os agregados públicos. O endereço `127.0.0.1:8502`
da máquina do solicitante não funciona na máquina de outra pessoa. Alternativamente,
revisar juntos por compartilhamento de tela ou usar a futura URL publicada.

## Tarefas

| Tarefa | O que observar | Resultado esperado, sem antecipar ao participante |
| --- | --- | --- |
| Encontrar admissões e desligamentos de PE no trimestre | Entendimento de fonte, período e MOV | 1.284 e 1.021; diferença 263 não é saldo ajustado |
| Filtrar Brasil, SP, fevereiro e uma ocupação | Clareza dos controles e do recorte ativo | Números e contexto mudam juntos |
| Ir a Fontes e voltar a Emprego formal | Perda de contexto ou dificuldade em retomar | Filtros e métricas mantidos |
| Baixar o CSV do recorte | Facilidade e entendimento do arquivo | Uma linha agregada do recorte, não microdados |
| Explorar Júnior e Remoto em Perfis em dados | Entendimento de faixas e bases por pergunta | Pesquisa distinta do CAGED, sem salário exato inferido |
| Selecionar AC e restaurar filtros de perfis | Clareza do estado vazio e recuperação | Sem resposta; restauração retorna ao Brasil |
| Comparar logística e classe majoritária | Interpretação de acurácia e recall | Maioria tem recall zero; logística também tem detecção limitada |
| Ler Fontes e limites | Limites de generalização e privacidade | Entender por que G12 não é publicado |

Não conduzir a resposta. Peça que a pessoa diga o que entendeu antes de explicar.
Registrar quando foi necessário ajudar. Em celular, repetir navegação e um filtro.

## Registro Real

Copiar este quadro somente quando houver uma sessão ou comentário efetivo:

| Campo | Preencher após revisão |
| --- | --- |
| Data e versão testada | Pendente |
| Revisor | Código ou papel; não precisa nome completo |
| Dispositivo/navegador | Pendente |
| Tarefa e observação literal | Pendente |
| Conseguiu sem ajuda? | Pendente; não converter ausência em sucesso |
| Problema e impacto | Pendente |
| Decisão do grupo | Corrigir, investigar ou manter com justificativa |
| Ajuste, evidência e reteste | Pendente |

Adicionar achados reais ao registro de feedback. Após mudança funcional, repetir
`validar_consolidacao.py`. Encerrar a pendência de revisão só depois de registrar
resultados reais; questões não corrigidas devem permanecer explícitas na etapa 08.

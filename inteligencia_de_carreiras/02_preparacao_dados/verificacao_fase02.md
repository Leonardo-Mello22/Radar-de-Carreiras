# Conferência da fase 02

14 de outubro de 2026. Critério aplicável: plano de preparação da coluna CC,
Análise e Visualização de Dados, no documento de entregáveis fornecido pelo grupo.

## Resultado

**Concluída documental e tecnicamente para o pacote atual, com alertas registrados.**
O plano identifica fontes e formatos, descreve limpeza/normalização e justifica
transformações por variável. O pipeline completo foi executado a partir dos nove
brutos disponíveis, com validação e testes. Aprovação da disciplina depende da
avaliação da professora; a exploração e os modelos permanecem para outras etapas.

| Componente | Evidência | Situação |
| --- | --- | --- |
| Fontes abertas, próprias ou simuladas | Escopo, formatos, catálogo e manifestos; fontes públicas e próprias; nenhuma simulação. | Atendido |
| Limpeza e normalização | Regras de tipos, texto, código, domínio, duplicatas, nulos e plausibilidade no plano e scripts. | Atendido |
| Transformações adequadas à análise | IPCA, recortes, categorias, faixas, tabelas longas, agregados e escalas separadas. | Atendido |
| Justificativa conforme as variáveis | Matriz por coluna com tipo, nulos, operação, razão e relação com P1-P12. | Atendido |
| Processo reproduzível e revisão | Execução completa, SHA-256, ambiente, validação em valores e testes automatizados. | Atendido |

Consultar o [plano](plano_de_preparacao.md), a
[matriz por coluna](matriz_preprocessamento.csv), o
[relatório da execução](../datasets/qualidade/execucao_preparacao.json) e a
[validação dos exports](../datasets/qualidade/validacao_exports.json).

## Correções de implementação

- State of Data: `atua_como_gestor` passou de texto a booleano anulável; 1.045 gestores sem cargo técnico informado passaram a `Gestao`, em vez de categoria residual. Contagens de participantes, nulos e origens foram preservadas.
- Cache CAGED: a chave agora inclui código e hashes dos insumos. Reaproveitamento não depende apenas do nome do mês.
- Validação: temporários de cache não são tratados como exports finais; CSV e Parquet são reconciliados também em valores, não apenas dimensão/schema.
- Reprodução: comando único para preparação pública, pesquisa própria, validação e testes; conferência de fontes ocorre antes de reprocessar.
- Evidência: preparação completa e validação isolada têm relatórios separados, evitando apagar a procedência da execução completa.

## Alertas mantidos

Os 690 salários CAGED sinalizados continuam nos movimentos; 395 jornadas
sinalizadas são excluídas somente de cálculos que usam jornada. Linhas iguais
CAGED permanecem porque não há identificador de pessoa. No State of Data,
senioridade não respondida não vira júnior; teto salarial aberto não vira valor exato.

Na pesquisa G12, três respostas Q07 fora do domínio, uma expectativa salarial
sinalizada e um intervalo de experiência permanecem registrados. Âncoras de Q05,
protocolo de recrutamento e consentimento de divulgação exigem confirmação.
Esses alertas não foram tratados como licença para inventar respostas.

Nenhuma tabela concatena movimentações CAGED, respostas State of Data e respostas
G12. Matriz de pesquisa contém referências/hipóteses, não novos microdados nem
evidência externa checada. Respostas individuais permanecem fora do Git.

## Limites de conclusão

Validar tipos, fontes e contagens não comprova representatividade, causalidade,
veracidade de relatos ou autorização de divulgação. Regras de treino/teste são
planejadas, mas nenhum modelo foi ajustado nesta fase. O dashboard histórico,
`app/` e `src/` permanecem sem alteração de comportamento.

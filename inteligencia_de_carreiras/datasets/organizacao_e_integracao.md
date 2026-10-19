# Organização e integração das fontes

## Decisão

Manter datasets separados por fonte e unidade de observação, com catálogo e
registro de fontes únicos. A organização comum facilita descoberta, reprodução
e navegação. Ela não transforma populações diferentes numa única amostra.

| Conjunto | O que cada linha representa | Finalidade |
| --- | --- | --- |
| Novo CAGED | Admissão ou desligamento formal | Fluxos de emprego e salários administrativos no recorte de TI. |
| State of Data | Resposta de participante da área de dados | Formação, tecnologias, perfis e busca declarada de emprego. |
| Pesquisa Grupo 12 | Resposta ao questionário próprio | Necessidades, prioridades, expectativa e intenções da amostra do grupo. |
| Matriz Grupo 12 | Referência, hipótese, dúvida ou risco de pesquisa | Rastreabilidade de desk research; não é uma base de trabalhadores. |
| IPCA e municípios | Índice por competência ou código territorial | Enriquecimento monetário e geográfico do CAGED. |

Não existe `dataset_total` com linhas dessas fontes concatenadas. Os nomes-base
em `tratados/` identificam sua origem. Tabelas derivadas de um questionário
continuam sendo o mesmo estudo: 420 respostas longas e 101 seleções não são
novos participantes nem novas amostras.

## Integrações permitidas

- Ligar CAGED ao IPCA pela competência e às dimensões CBO/município pelos códigos oficiais.
- Ligar respostas, perguntas e prioridades do G12 pelo ID de linha e pergunta dentro desse estudo.
- Ligar respostas do State of Data às suas tecnologias pelo ID interno desse estudo.
- Reunir fontes no mesmo produto, com seções, legendas, período, unidade e denominadores separados.
- Comparar temas entre fontes como triangulação exploratória, explicitando divergências de público e mensuração.

## Integrações proibidas ou não sustentadas

- Não ligar pessoas do CAGED às pesquisas por UF, cargo ou salário: o pacote não tem identificador comum.
- Não somar as 118.564 movimentações do CAGED às respostas das pesquisas como um total de pessoas.
- Não somar recortes regionais à base nacional: são subconjuntos, não datasets independentes.
- Não usar a expectativa salarial de 2026 como salário recebido ou compará-la diretamente ao CAGED de 2025 como erro individual de expectativa.
- Não concatenar Q10 do G12 com `planos_mudar_emprego_6m` do State of Data: um trata de emprego, área ou regime; o outro tem respostas e horizonte próprios.
- Não apresentar referências da matriz como dados já baixados, checados ou resultados da pesquisa com usuários.

O questionário próprio não informa cargo padronizado nem UF. Não permite o
pareamento necessário para uma comparação salarial equivalente. Esses campos
podem ser planejados para uma coleta futura, nunca inventados nesta base.

## Questionário próprio

Foram recebidas 35 respostas a 12 perguntas, coletadas de 31/08 a 04/09/2026.
O XLSX tem um carimbo de data/hora e uma coluna vazia adicional. O tratamento
reconhece os números das perguntas, inclusive Q02 que aparece no fim da planilha.
A coluna vazia é descartada; o original permanece intacto.

| Arquivo em `tratados/` | Linhas | Uso |
| --- | ---: | --- |
| `pesquisa_grupo12_respostas` | 35 | Uma linha por resposta, 31 campos originais/derivados e de procedência. |
| `pesquisa_grupo12_respostas_longas` | 420 | Uma linha por participante e pergunta; filtro por item. |
| `pesquisa_grupo12_prioridades` | 101 | Uma linha por opção selecionada em Q08. |
| `matriz_pesquisa_grupo12` | 21 | Achados declarados, links, confiança, CSD e alertas metodológicos. |

As tabelas têm versões CSV e Parquet. O
[mapa de perguntas](auxiliares/questionario_grupo12.csv) preserva os enunciados.
O [dicionário próprio](auxiliares/dicionario_pesquisa_grupo12.csv) explica cada campo.

### Regras de tratamento

- Q07: três respostas fora do domínio Sim/Não ficam preservadas e sinalizadas. O booleano é ausente nesses casos; o denominador de intenção válida é 32, não 35. Não deslocar as respostas para outra pergunta sem evidência do formulário.
- Q08: reconhecer alternativas completas. A opção de salário contém vírgulas internas; dividir o texto simplesmente em vírgulas corromperia as seleções. O denominador é o número de participantes que responderam ao item, não as 101 seleções.
- Q09: manter o número declarado. Um valor de R$5 requer confirmação e não é convertido para R$5.000. A faixa de revisão 300 a 200.000 é uma regra operacional, não uma definição universal de expectativa válida. Comparar resultados com e sem os sinalizados na análise interna.
- Q12: converter anos/meses apenas quando inequívoco. O intervalo de sete a oito meses fica com limites 7 e 8; o campo exato permanece ausente. Zero meses é válido.
- Q05: manter as notas 1 a 5. O arquivo não traz âncoras da escala; confirmar o formulário antes de interpretar direção ou satisfação.
- Valores ausentes não viram zero ou Não. Nenhuma resposta do G12 foi removida por deduplicação; IDs identificam linhas, não comprovam pessoas únicas.
- Método de recrutamento, consentimento para publicação e contexto de aplicação não estão comprovados no XLSX. Registrar esses itens antes de generalizar ou divulgar resultados.

## Matriz e fontes apenas referenciadas

A matriz contém 13 itens rotulados pelo grupo como certeza, 2 como suposição e
6 como dúvida. Os 10 hyperlinks foram preservados. Esses rótulos são declarações
do documento, não validação automática das fontes externas.

RAIS, PNAD Contínua, Censo Superior/INEP, Base dos Dados, Brasscom, Exame e os
similares citados não foram incorporados como novas bases de microdados.
Consulte [registro_fontes.csv](registro_fontes.csv) para a situação de cada fonte.

A sugestão da matriz de medir progressão salarial individual por CAGEDMOV não
é sustentada pelo pacote: não há ligação entre admissão e desligamento da mesma
pessoa nem tempo de vínculo disponível. O plano usa comparação de distribuições
de grupos distintos. Percentuais de fontes secundárias e conclusões sobre
concorrentes precisam de verificação própria antes de embasar resultados.

## Privacidade e versionamento

Originais e respostas individuais da pesquisa ficam locais e ignorados pelo Git,
incluindo eventual pasta de agregados próprios. O carimbo exato da coleta fica
somente no original; o dataset analítico guarda o mês. Pseudônimos de linha não
garantem anonimização de uma amostra pequena.

Antes de publicação, confirmar autorização/consentimento e revisar combinações
raras. Não publicar pontos individuais, textos brutos ou microdados. Preferir
agregados, suprimir células com menos de cinco respostas e avaliar supressão
complementar quando totais revelarem o valor omitido. Esse cuidado não elimina
todo risco de reidentificação. Comparações estatísticas de subgrupos com n<30
não serão usadas para conclusões; isso é estabilidade operacional, não prova de
representatividade quando n>=30.

## Reproduzir a importação

Na pasta `inteligencia_de_carreiras/datasets`, após instalar `scripts/requirements.txt`:

```powershell
python scripts/prepare_grupo12.py --responses brutos/pesquisa_grupo12/trajetoria_profissional_respostas.xlsx --matrix brutos/pesquisa_grupo12/matriz_pesquisa_g12.xlsx --output .
python scripts/validate_package.py --output .
python -m unittest discover -s scripts/tests -v
```

Em outra máquina, obter os dois XLSX do grupo por canal autorizado. Os arquivos
privados não serão baixados automaticamente nem distribuídos pelo Git.
O [manifesto próprio](fontes_pesquisa_grupo12.json) registra SHA-256 e volumes;
o [relatório de qualidade](qualidade/relatorio_pesquisa_grupo12.json) mantém os alertas.

Novos questionários com perguntas diferentes terão outro identificador de estudo,
versão e mapa de colunas. Só uma verificação documentada de equivalência permite
alinhar variáveis; perguntas parecidas não são automaticamente intercambiáveis.

# Atualização das bases públicas 2025–2026

Este lote amplia os dados sem sobrescrever os insumos das oito etapas já
entregues. A [entrega ampliada](../08_documentacao_final/atualizacao_2025_2026.md)
refaz as análises e os modelos e integra o lote ao dashboard. Os novos
microdados e resultados locais não entram no Git.

| Base | Cobertura | Unidade |
| --- | --- | --- |
| Novo CAGED MOV | Janeiro a dezembro de 2025 e janeiro a setembro de 2026 | Uma movimentação de emprego formal |
| State of Data Brazil 2024/2025 | Coleta entre outubro e dezembro de 2024; mantida no pacote original | Uma resposta ao questionário |
| State of Data Brazil 2025/2026 | Coleta entre outubro e dezembro de 2025; nova edição separada | Uma resposta ao questionário |

## Contagens verificadas

| Recorte | Registros |
| --- | ---: |
| CAGED TI 2025 inteiro | 483.006 |
| CAGED TI janeiro a setembro de 2025 | 370.147 |
| CAGED TI janeiro a setembro de 2026 | 359.725 |
| CAGED TI total dos 21 meses | 842.731 |
| State of Data 2024/2025 tratado | 5.215 (5.076 residentes no Brasil) |
| State of Data 2025/2026 tratado | 3.494 (3.372 residentes no Brasil) |

O CAGED teve 91.309.413 linhas brutas examinadas; os Parquets de movimentações
de TI ocupam cerca de 36 MB. Na pesquisa nova, há 3.495 respostas na fonte,
uma duplicata exata removida e uma faixa salarial inválida sinalizada, com a
resposta preservada.

## Arquivos locais

Em `brutos/atualizacao_2025_2026/` ficam os 21 arquivos CAGEDMOV, o CSV original
da pesquisa nova, o IPCA, os dicionários auxiliares e o manifesto de fontes com
tamanhos e hashes SHA-256.

Em `tratados/atualizacao_2025_2026/`:

- `caged_ti/`: um Parquet por competência, com o mesmo recorte de famílias CBO do projeto.
- `caged_indicadores/`: contagens e percentis salariais por competência, UF,
  área de TI e tipo de movimentação. Grupos com menos de 30 salários válidos não têm percentis.
- `controle_caged_mensal.parquet`: contagens brutas e tratadas, admissões,
  desligamentos e recortes de PE e Nordeste por mês.
- `state_of_data_2025_2026.parquet` e `state_of_data_brasil_2025_2026.parquet`:
  perfis tratados, com a edição explícita e um recorte por residência.
- `state_of_data_mapa_colunas.json`: correspondência dos campos de perfil com o questionário.
- `resumo.json`: contagens finais e referência ao manifesto dos originais.

## Como comparar

- Compare jan–set/2025 com jan–set/2026. O ano de 2025 inteiro é útil para ler a
  série histórica, mas não como denominador direto do acumulado parcial de 2026.
- Os salários do CAGED estão em preços de março de 2025, corrigidos pelo IPCA.
  O lote só usa MOV, sem CAGEDFOR/CAGEDEXC, e não reproduz o saldo oficial ajustado.
- Não some percentis de grupos ou meses. Para uma nova faixa de períodos,
  recalcule os percentis nos eventos tratados.
- State of Data é uma pesquisa voluntária. As edições não acompanham as mesmas
  pessoas. Compare só perguntas e categorias compatíveis, com denominadores
  por edição. A edição nova mantém ausências; remove duplicatas exatas conforme
  a regra do pacote inicial e sinaliza intervalos salariais invertidos sem
  inventar um valor. A nova avaliação treina em 2024/2025 e testa em 2025/2026.

## Reprodução

Na pasta `datasets/`, usando o ambiente de reprodução já configurado na etapa 02:

```powershell
python scripts/expand_public_sources.py
python scripts/prepare_expansion.py
```

O primeiro comando reaproveita os originais verificados do pacote inicial,
baixa os novos meses pelo FTP do MTE e guarda as fontes com seus hashes. O
segundo processa os arquivos mês a mês e escreve o resumo final somente
depois de conferir o manifesto completo.

Fontes: [Novo CAGED/MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged),
[divulgação de setembro de 2026](https://www.gov.br/trabalho-e-emprego/pt-br/noticias-e-conteudo/2026/novembro/pais-gerou-1-248-mil-empregos-formais-ate-setembro-de-2026),
[State of Data Brazil](https://github.com/data-hackers-br/state-of-data-brazil) e
[IPCA/IBGE](https://sidra.ibge.gov.br/tabela/1737).

# Dicionário de variáveis

> Fonte da verdade: `data/raw/Layout_Novo_Caged_Movimentacao.xlsx` (layout oficial do
> Novo CAGED — Base de Movimentações), conferido contra o dado real `CAGEDMOV202501.txt`.
> Este dicionário cobre **as colunas que o projeto usa** (brutas e derivadas). Os domínios
> abaixo foram extraídos das abas de domínio do próprio layout, não de suposição.

## Parte A — Colunas brutas do CAGEDMOV usadas no projeto

| Variável (original) | Tipo | Significado | Domínio / formato |
|---------------------|------|-------------|-------------------|
| `competênciamov` | texto `AAAAMM` | Competência (mês) da movimentação | ex.: `202501` |
| `região` | código `9` | Região geográfica (IBGE) | 1 Norte · 2 Nordeste · 3 Sudeste · 4 Sul · 5 Centro-Oeste · 9 Não ident. |
| `uf` | código `99` | Unidade da federação (IBGE) | 11–53 (ex.: 26 Pernambuco, 29 Bahia, 23 Ceará) |
| `município` | código `999999` | Município (IBGE, 6 dígitos sem dígito verificador) | ex.: `261160` = Recife |
| `cbo2002ocupação` | código `999999` | Ocupação do trabalhador (CBO-2002) | 6 dígitos; família = 4 primeiros |
| `saldomovimentação` | inteiro | Natureza do evento em saldo | **`+1` = admissão** · **`-1` = desligamento** |
| `tipomovimentação` | código `99` | Detalhe do evento | 10/20/25/35/70/97 admissões; 31/32/33/40/43/45/50/60/80/90/98 deslig.; 99 não ident. |
| `salário` | decimal BR `999999999,99` | **Salário mensal declarado** | vírgula decimal (ex.: `1800,00`) |
| `valorsaláriofixo` | decimal BR | Parte fixa da remuneração | vírgula decimal |
| `unidadesaláriocódigo` | código `99` | Unidade de pagamento da parte fixa | 1 Hora · 2 Dia · 3 Semana · 4 Quinzena · **5 Mês** · 6 Tarefa · 7 Variável · 99 n/ident. |
| `graudeinstrução` | código `99` | Escolaridade | 1 Analfabeto … 7 Médio Completo · 8 Superior Incompleto · 9 Superior Completo · 10 Mestrado · 11 Doutorado · 80 Pós · 99 n/ident. |
| `idade` | inteiro `999` | Idade do trabalhador (anos) | — |
| `horascontratuais` | decimal | Horas contratuais semanais | ex.: `44,00` |
| `sexo` | código `9` | Sexo | 1 Homem · 3 Mulher · 9 Não ident. |
| `categoria` | código `999` | Categoria do trabalhador | 101 Empregado CLT geral … 111 Intermitente · 999 n/ident. |
| `competênciadec` | texto `AAAAMM` | Competência da declaração | — |
| `indicadordeforadoprazo` | código `9` | Declaração feita fora do prazo | 0 / 1 |

> **Colunas do layout que NÃO existem no CAGEDMOV** (são da base de exclusões): `competênciaexc`,
> `indicadordeexclusão`. O arquivo real traz 28 das 30 variáveis do layout.
>
> **Não existe** no CAGEDMOV: tempo de emprego/vínculo, identificador de pessoa/vínculo,
> salário de admissão e de desligamento na mesma linha. Ver `00_verificacao_layout.md`.

## Parte B — Colunas derivadas na base tratada (`data/processed/caged_ti.parquet`)

| Coluna tratada | Tipo | Origem / regra |
|----------------|------|----------------|
| `competencia` | str `AAAAMM` | = `competênciamov` |
| `uf_codigo` / `uf_nome` | str | `uf` + tradução pela aba `uf` do layout |
| `regiao_nome` | str | tradução de `região` |
| `municipio_codigo` / `municipio_nome` | str | `município` + aba `município` (prefixo `XX-` removido) |
| `cbo_codigo` | str (6) | = `cbo2002ocupação` |
| `cbo_familia` | str (4) | 4 primeiros dígitos do CBO |
| `cbo_nome` | str | tradução via aba `cbo2002ocupação` |
| `saldo` | Int64 | = `saldomovimentação` (+1 / −1) |
| `movimento` | str | `+1`→"admissão", `−1`→"desligamento" |
| `tipo_movimentacao_cod` / `tipo_movimentacao` | str | `tipomovimentação` + tradução |
| `sexo` | str | tradução de `sexo` |
| `grau_instrucao` | str | tradução de `graudeinstrução` |
| `idade` | Int64 | = `idade` |
| `horas_contratuais` | float | `horascontratuais` (decimal BR → float) |
| `unidade_salario_cod` | str | = `unidadesaláriocódigo` |
| `salario_nominal` | float | `salário` convertido (ponto=milhar, vírgula=decimal) |
| `salario_real` | float | `salario_nominal` × fator IPCA (preços de `IPCA_MES_REFERENCIA`) |
| `salario_valido` | bool | `True` se `salario_nominal ∈ [300; 200000]` (fora disso = outlier sinalizado) |
| `fonte` | str | procedência (CAGED/PDET) carregada em cada linha |
| `mes_referencia_ipca` | str | mês de referência da deflação |

## Parte C — Famílias CBO-2002 de TI usadas (confirmadas no layout)

| Família | Nº ocupações | Observação |
|---------|--------------|------------|
| 1236 | 1 | Diretor de Serviços de Informática |
| **1425** | 7 | **Gerentes de TI** (adicionada — é a real "gerência de TI", não a 1236) |
| 2122 | 3 | Engenheiros de computação |
| 2123 | 4 | Administradores (BD, redes, SO, segurança) |
| 2124 | 6 | Analistas e arquitetos de TI |
| 3171 | 4 | Programadores (inclui 317115 CNC — ruído conhecido) |
| 3172 | 2 | Operador de computador; suporte/helpdesk |
| ~~3173~~ | 0 | **Removida — não existe na CBO-2002** |

Candidatas fora do recorte deste ciclo (registradas): 2031 (pesquisa acadêmica),
3132 (manutenção de equipamentos), 3133 (técnico de comunicação de dados).

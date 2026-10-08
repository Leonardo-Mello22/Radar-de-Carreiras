# Verificação crítica do layout — Novo CAGED (Base de Movimentações)

> **Etapa 2 / Seção 4 do briefing.** Esta verificação foi feita **antes** de escrever
> qualquer análise, lendo o layout oficial (`data/raw/Layout_Novo_Caged_Movimentacao.xlsx`,
> baixado do FTP do MTE) e **conferindo contra o dado real** (`CAGEDMOV202501.txt`).
> Resultado em uma frase: **a promessa vendida do produto NÃO se sustenta com o CAGED sozinho.**

---

## A promessa que foi vendida

> "O registro de desligamento do CAGED traz **salário de admissão, salário de desligamento
> e tempo de casa na mesma linha**, o que permite medir **crescimento salarial dentro do
> mesmo vínculo** e **rotatividade antes de 1 ano**."

Essa afirmação está **errada** para o Novo CAGED. Abaixo, as três perguntas obrigatórias,
respondidas com as colunas que realmente existem.

---

## Colunas que realmente existem na Base de Movimentações

O layout oficial descreve **30 variáveis**; o arquivo real de movimentações
(`CAGEDMOV202501.txt`) traz **28 colunas** (faltam `competênciaexc` e `indicadordeexclusão`,
que pertencem à base de exclusões `CAGEDEXC`). A lista real, na ordem do arquivo:

```
competênciamov; região; uf; município; seção; subclasse; saldomovimentação;
cbo2002ocupação; categoria; graudeinstrução; idade; horascontratuais; raçacor;
sexo; tipoempregador; tipoestabelecimento; tipomovimentação; tipodedeficiência;
indtrabintermitente; indtrabparcial; salário; tamestabjan; indicadoraprendiz;
origemdainformação; competênciadec; indicadordeforadoprazo; unidadesaláriocódigo;
valorsaláriofixo
```

Há **uma movimentação por linha** (uma admissão **ou** um desligamento), e **não há
identificador de pessoa nem de vínculo** — a base é explicitamente *Não-Identificada*.

---

## Pergunta 1 — Existe campo de tempo de emprego/vínculo? Qual o nome exato?

**Não existe.** Nenhuma das 28 colunas mede tempo de casa / tempo de vínculo.

O que pode ser confundido com isso, e por que não serve:

| Coluna | O que é de verdade | Serve como tempo de vínculo? |
|--------|--------------------|------------------------------|
| `idade` | Idade do **trabalhador** em anos | Não — é idade da pessoa |
| `tamestabjan` | **Faixa de nº de empregados** do estabelecimento em janeiro | Não — é porte da empresa |
| `competênciamov` | Mês da movimentação (AAAAMM) | Não — é só o mês do evento |
| `horascontratuais` | Horas semanais contratadas | Não |

Conclusão: **o tempo de emprego/vínculo não está no CAGED de movimentações.** Quem
tradicionalmente carrega tempo de vínculo é a **RAIS** (vínculo ativo em 31/12, com
`tempo_emprego` em meses).

## Pergunta 2 — Dá para distinguir salário de admissão de salário de desligamento?

**No nível agregado, sim. No nível do mesmo vínculo/pessoa, não.**

- Cada linha tem **um único** campo `salário` ("Salário mensal declarado") e um
  `valorsaláriofixo` (parte fixa da remuneração).
- A natureza do evento é dada por **`saldomovimentação`** (verificado no dado real:
  valores **`+1` = admissão** e **`-1` = desligamento**) e detalhada por
  **`tipomovimentação`** (10/20/25/35/70/97 = admissões; 31/32/40/43/45/50/60/80/90/98 =
  desligamentos).
- Logo, é possível medir a **faixa salarial das admissões** (linhas com saldo `+1`) e a
  **faixa salarial no momento dos desligamentos** (linhas com saldo `-1`) **em agregado**,
  por cargo/município/período.
- **Mas** admissão e desligamento são **linhas diferentes, de pessoas diferentes**. Como
  não há chave de pessoa/vínculo (PIS, CPF, matrícula), **é impossível ligar a admissão
  de alguém ao seu próprio desligamento**. Portanto **não dá para medir crescimento
  salarial dentro do mesmo vínculo**.

## Pergunta 3 — Se não houver, qual a alternativa e o que muda na promessa?

**O que o CAGED entrega (e sustenta a parte central do produto):**
- Faixa salarial **de entrada** (p10/p50/p90 das admissões) por cargo, município e período — ✅
- Volume de admissões e desligamentos, saldo de emprego, por cargo/UF/mês — ✅
- Comparação agregada entre salário de entrada (admissões) e de saída (desligamentos) — ✅

**O que o CAGED NÃO entrega (a parte "vendida" que precisa ser recortada ou terceirizada):**
- ❌ Crescimento salarial **dentro do mesmo vínculo** ("o que acontece depois da contratação")
- ❌ **Tempo de casa** e **rotatividade antes de 1 ano** no nível individual

**Alternativa proposta:**
1. **Manter o CAGED** como fonte da **faixa salarial de entrada** e dos **fluxos**
   (admissões/desligamentos) — é aqui que ele é forte e atual (mensal).
2. **Trazer a RAIS** (mesmo FTP, anual) para a parte de **trajetória**: a RAIS tem
   `tempo_emprego` do vínculo e salário em 31/12, permitindo aproximar tenure médio por
   cargo e faixa de permanência — porém **ainda em agregado**, não acompanhando a mesma
   pessoa ao longo do tempo (a RAIS não-identificada também não encadeia indivíduos).
3. **Reescrever a pergunta central do produto** de:
   > "faixa salarial real do cargo X, na cidade Y — e o que costuma acontecer *depois da
   > contratação*"

   para algo honesto e entregável neste ciclo:
   > "**Qual é a faixa salarial de entrada (p10/p50/p90) do cargo X, na cidade Y, hoje,
   > quanta gente está sendo admitida, e como o salário de entrada se compara ao de saída
   > nesse mesmo recorte** — tudo em agregado, no emprego formal."

**O que isso muda na promessa:** a dimensão de "trajetória individual pós-contratação"
sai do escopo do Ciclo 1 (vira trabalho futuro dependente da RAIS, e ainda assim só
agregado). A promessa de **faixa salarial de entrada confiável, atual e com procedência**
permanece totalmente de pé — e é a mais valiosa para o público-alvo (início de carreira).

---

## Outras divergências entre briefing e dado real (registradas por honestidade)

| Afirmação do briefing | O que o dado real mostra |
|-----------------------|--------------------------|
| "encoding **latin-1**" (Seção 3) | O `.txt` é **UTF-8** sem BOM. Lido como latin-1, "competência" vira "competÃªncia". O pipeline usa `utf-8`. |
| Famílias CBO de TI incluem **3173** | **3173 não existe** na CBO-2002 (0 ocupações na aba oficial). Removida. |
| **1236** = "gerência de TI" | 1236 = "Diretor de Serviços de Informática" (só 123605). A família de **gerentes de TI** é a **1425**. Adicionada ao recorte. |
| Nomes de arquivo no FTP em UTF-8 | Os **nomes de arquivo** no FTP estão em **latin-1** (`ã`→`%E3`). Só o conteúdo é UTF-8. |

Separador `;` e decimal com vírgula (`1800,00`): **confirmados** no dado real.

---

## Veredito

A verificação da Seção 4 **confirma a suspeita do briefing**: o Novo CAGED de
movimentações **não tem tempo de vínculo nem chave de pessoa**, então **crescimento
salarial intra-vínculo e rotatividade individual não são mensuráveis** com ele. Este é
um **resultado negativo valioso**: evita construir o produto sobre uma premissa falsa.
O produto segue viável com escopo ajustado (faixa de entrada + fluxos + comparação
agregada entrada/saída), e a trajetória fica como trabalho futuro ancorado na RAIS.

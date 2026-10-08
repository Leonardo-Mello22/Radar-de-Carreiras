# Plano de Análise de Dados — Entregável 1

> Radar de Carreira em TI · Ciclo 1 · Grupo 12 · Trilha Análise e Visualização de Dados.
> Este plano reflete o escopo **ajustado após a verificação do layout** (ver
> `00_verificacao_layout.md`) — não a promessa original, que não se sustentou.

## 1. Problema

Estudantes e profissionais em início de carreira em TI (foco Pernambuco/Nordeste) **não
têm uma referência salarial confiável, atual e localizada** para decidir carreira. As fontes
usuais (sites de vagas, "salário médio" de portais) são autodeclaradas, enviesadas,
desatualizadas e quase sempre reportam **média** — que engana num mercado assimétrico. A
pergunta prática é: *"Qual é a faixa salarial de entrada do cargo X, na cidade Y, hoje, e qual
o volume de contratações?"*

## 2. Pergunta central (ajustada)

> **Qual é a faixa salarial de entrada (p10/p50/p90) do cargo X, na cidade/UF Y, no
> emprego formal, quanta gente está sendo admitida, e como o salário de entrada se compara
> ao de saída nesse mesmo recorte — tudo em agregado.**

A dimensão "o que acontece *depois* da contratação" (trajetória intra-vínculo) **saiu do
escopo** porque o CAGED não a mede (sem tempo de vínculo nem chave de pessoa). Fica como
trabalho futuro ancorado na RAIS.

## 3. Hipóteses

| # | Hipótese | Como testar na EDA | Resultado preliminar (jan/2025) |
|---|----------|--------------------|---------------------------------|
| H1 | A distribuição salarial de TI é assimétrica à direita (média > mediana) → reportar faixa, não média | histograma + comparação média/mediana | **Confirmada**: cauda longa à direita |
| H2 | Há hierarquia salarial clara entre famílias CBO (gerência/engenharia > suporte/operação) | p10/p50/p90 por cargo | **Confirmada** |
| H3 | Escolaridade eleva o salário, mas com forte sobreposição | boxplot por grau + correlação | **Confirmada** (caixas se sobrepõem; r idade×sal ≈ 0,40) |
| H4 | Dentro do Nordeste há forte heterogeneidade entre UFs; PE entre os maiores volumes | faixa por UF do NE + amostra | **Confirmada** |
| H5 | Mercado aquecido: saldo de admissões − desligamentos positivo | volume por família + saldo | **Confirmada** (saldo +785 no mês) |
| H6 | Salário agregado de desligamento > de admissão (grupos distintos, não trajetória) | faixa por movimento | **Confirmada** (p50 4.310 vs 3.500) |

## 4. Fontes

**Principal (validada e em uso):** Novo CAGED — Base de Movimentações (PDET/MTE), microdados
mensais, UTF-8, `;`, decimal `,`. Já baixada e processada (jan/2025).

**Deflator (validado e em uso):** IPCA número-índice via API SIDRA/IBGE (tabela 1737, var 2266).

**Candidatas (registradas, não usadas neste ciclo):**
- **RAIS** (mesmo FTP) — traria tempo de vínculo e salário em 31/12 → reabilitaria (em
  agregado) a parte de trajetória/permanência.
- **PNAD Contínua (IBGE)** — incluiria informais, PJ e desemprego (o CAGED só vê emprego formal).
- **Censo da Educação Superior (INEP)** — cruzar formação em TI com o mercado.

## 5. Tipos de visualização previstos

| Objetivo | Visualização | Onde |
|----------|--------------|------|
| Faixa salarial por cargo | gráfico de faixa p10–p90 com marcador de mediana | EDA + dashboard |
| Dispersão por escolaridade | boxplot | EDA |
| Distribuição salarial | histograma (antes/depois de outliers) | EDA + dashboard |
| Comparação entre UFs do NE | faixa por UF com destaque PE | EDA |
| Volume de fluxo | barras admissões×desligamentos por família | EDA |
| Entrada × saída | faixa por tipo de movimento | EDA |
| Evolução no tempo | linha por competência | dashboard (completa com +meses) |
| Relação idade×salário + outliers | dispersão com outliers destacados | EDA |

## 6. Restrições de produto respeitadas (Seção 5)
Faixa p10/p50/p90 sempre (nunca média sozinha) · amostra mínima de 30 (constante
`MIN_AMOSTRA`) · deflação IPCA obrigatória · procedência visível em todo número · leitura
sempre agregada (nunca por pessoa) · limites da base declarados no dashboard e nos docs.

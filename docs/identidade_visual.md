# Identidade visual — Radar de Carreira em TI

> Fonte da verdade do visual. Tudo com interface (dashboard, gráficos da EDA, HTML, imagens
> de evidência) deve parecer a mesma coisa. **Não** usar a paleta padrão do Streamlit nem do
> matplotlib. **Não** escrever hexadecimal fora de `app/theme.py`.

## 1. Cores (em `app/theme.py`)

| Papel | Hex | Onde usa |
|-------|-----|----------|
| Laranja da marca | `#FF7200` | ação, destaque, número principal, série em evidência |
| Laranja pressionado | `#E05F00` | hover/estado ativo |
| Laranja claro (fundo) | `#FFF0E3` | caixas de destaque, chips ativos |
| Laranja escuro (texto) | `#B34F00` | texto sobre `#FFF0E3` (nunca `#FF7200` como texto em fundo claro) |
| Grafite | `#16181D` | painéis escuros, títulos, cabeçalho |
| Grafite elevado | `#22252B` | cards dentro de painel escuro |
| Borda escura | `#2C2F35` | divisórias em painel escuro |
| Cinza claro | `#F3F3F4` | fundo de card neutro |
| Borda clara | `#E6E7EA` | bordas em fundo branco |
| Trilho de gráfico | `#EDEEF0` | grade/track |
| Texto principal | `#1C1C1C` | corpo em fundo claro |
| Texto secundário | `#5A5E66` | descrições |
| Texto terciário | `#8A8E96` | legendas, fonte, amostra |
| Texto sobre escuro | `#C9CBD0` | corpo em painel escuro |
| Neutro de gráfico | `#B9BCC2` | séries sem destaque |
| Faixa salarial | `#FFC08F` | área piso–teto |

Gradientes: banner escuro `linear-gradient(100deg,#16181D,#1E1A16 55%,#33210F)`;
cabeçalho de card laranja `linear-gradient(90deg,#FF7200,#E05F00)`.

## 2. Tipografia
Barlow (fallback Arial, Helvetica, sans-serif). Pesos 400/600/700/800. Ritmo de toda seção:
**kicker → título → lead → conteúdo → linha de fonte**.
- Kicker 13px/700 `#FF7200`, caixa alta, `letter-spacing:2.5px`
- Título 24–38px/800 `#16181D`
- Lead 16.5px/400 `#4A4E55`, máx ~800px
- Número de destaque 38–64px/800 `#FF7200`
- Corpo 15–16px/400 `#1C1C1C`
- Legenda/fonte 12.5px/400 `#8A8E96`

## 3. Formas
Raio: 18px painéis, 14px cards, 12px botões, 20px pills, 6px barras. Painel escuro
`#16181D`, padding 38px 34px. Card claro `#F3F3F4`/branco + borda `1px #E6E7EA`. Botão
`2px solid #FF7200`, raio 12px, 700. Sombra só em painel-tela: `0 16px 38px rgba(0,0,0,.10)`.

## 4. Símbolo (aro de radar)
SVG fixo (não redesenhar): 4 círculos concêntricos laranja, o central preenchido. Em fundo
escuro vira marca d'água (300–500px, opacity .07–.13). Definido em `app/theme.py::aro_svg()`.

## 5. Regras de gráfico (`src/plotting.py`)
- **Uma cor de destaque por gráfico**: o que importa em `#FF7200`, resto em `#B9BCC2`. Sem arco-íris.
- **Faixa, não média**: p10/p50/p90; mediana = marca laranja, faixa = área `#FFC08F`.
- **Amostra sempre visível**: "n = X" + mês de referência em todo gráfico.
- Amostra < mínimo → aviso no lugar do gráfico.
- **Eixo único** (nunca dois eixos y).
- Texto em `#1C1C1C`/`#8A8E96`, nunca na cor da série.
- Grade só horizontal `#EDEEF0` 1px; sem moldura (remover spines de cima/direita).
- Até 8 categorias: rótulo direto na ponta, sem legenda.
- Toda figura tem linha de fonte: `Fonte: Novo CAGED · referência MM/AAAA · n = 1.284`.

## 6. Streamlit
`.streamlit/config.toml` com primaryColor `#FF7200`, background branco, secundário `#F3F3F4`,
texto `#1C1C1C`. CSS (Barlow + tipografia) injetado uma vez em `aplicar_tema()`.
Estrutura da página: **cabeçalho escuro** (aro + nome) → **filtros em uma linha** (nunca na
sidebar) → **número principal** (mediana laranja grande, faixa piso–teto, amostra ao lado) →
**dois gráficos** (distribuição + evolução) → **rodapé fixo** (fonte, mês, limites). Amostra
insuficiente → caixa `#FFF0E3` com orientação, sem número cinza nem gráfico vazio.

## 7. Escrita
Rótulos/botões em minúsculas, sem ponto final. Cargo pelo nome legível, nunca código CBO.
Reais como `R$ 3.240` (sem centavos). Sem "aproximadamente/cerca de/estimado" no número.
Em vez de "erro"/"sem dados": "poucos registros para este recorte — tente uma cidade maior ou
um período mais longo".

## 8. O que não fazer
Paleta padrão de Streamlit/matplotlib · emoji como ícone · azul · texto longo centralizado ·
hex fora de `app/theme.py` · número sem fonte e sem amostra.

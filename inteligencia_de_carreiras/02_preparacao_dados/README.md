# Preparação dos dados

Etapa 02: plano documental e pipeline executável para preparar as fontes das
perguntas P1-P12. As bases permanecem separadas, com filtros, tipos, categorias,
ausências e transformações justificados.

## Entrega

- [Plano em PDF](plano_de_preparacao.pdf).
- [Plano editável e versionável](plano_de_preparacao.md).
- [Matriz de decisões por coluna](matriz_preprocessamento.csv).
- [Conferência dos critérios CC02](verificacao_fase02.md).
- [Dependências da execução](requirements_reproducao.txt).
- [Relatório do pipeline completo](../datasets/qualidade/execucao_preparacao.json).

O plano descreve o que foi aplicado. Modelos e estratégias de treino/teste são
regras previstas para as etapas seguintes, não resultados já executados.
As escalas do pacote são exploratórias e não devem ser reaproveitadas como ajustes
de treino. Alertas do questionário continuam registrados, sem correções inventadas.

## Reproduzir

Na raiz do repositório, com os originais locais e os manifestos disponíveis:

```powershell
python -m pip install -r inteligencia_de_carreiras/02_preparacao_dados/requirements_reproducao.txt
python inteligencia_de_carreiras/datasets/scripts/run_preparation.py
```

O comando confere os nove brutos por SHA-256, prepara as fontes públicas,
prepara pesquisa e matriz G12, valida os exports em valores e executa os testes.
O relatório registra versões, fontes, código, etapas e hashes dos produtos.
Não há download automático. Cache usa código/fontes na chave e fica no temporário
do sistema, fora do OneDrive por padrão. `--temporary CAMINHO` escolhe outro local.

Para conferir apenas os produtos já preparados:

```powershell
python inteligencia_de_carreiras/datasets/scripts/run_preparation.py --mode validate
```

Isso grava `execucao_validacao.json` sem sobrescrever a evidência da preparação
completa. O diretório temporário deve ser gravável; em ambientes restritos, ajustar
`TEMP`/`TMP` para uma pasta autorizada antes dos testes. Reservar alguns GB em disco
para a extração dos arquivos CAGED.

Em outra máquina, baixar as fontes públicas com `datasets/scripts/download_sources.py`
e obter os XLSX do grupo por canal autorizado. Executar `prepare_grupo12.py` com
esses XLSX para registrar as fontes próprias; depois rodar o pipeline completo.
Os [detalhes de importação](../datasets/organizacao_e_integracao.md) preservam
privacidade e origens. Nunca substituir os arquivos privados por respostas simuladas.

## Regenerar a documentação

Depois de uma execução completa aprovada:

```powershell
python inteligencia_de_carreiras/02_preparacao_dados/gerar_preparacao.py --repo .
```

Isso atualiza plano, matriz e versões das dependências a partir do pacote local.
Uma mudança de dados confirmada exige nova versão de fonte/manifesto e revisão
dos critérios; não sobrescrever silenciosamente a origem para eliminar alertas.

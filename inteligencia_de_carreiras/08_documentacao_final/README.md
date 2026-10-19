# Documentação Final

Etapa 08, CC10. Dossiê final da solução analítica e visual do Radar de carreiras,
versão 1.1, referência 19/10/2026. Documentação concluída, com evidências técnicas
preservadas e pendências externas explícitas. Não significa aprovação docente,
teste estruturado com participantes ou hospedagem já realizada.

## Leitura e Entrega

1. [Documentação final em PDF](documentacao_final.pdf): dez páginas com processo,
   decisões, fontes, insights, modelos, quatro capturas e limites.
2. [Versão em Markdown](documentacao_final.md): mesmo conteúdo, com links de
   navegação para as evidências no repositório.
3. [Guia de entrega e revisão](guia_entrega.md): mapa CC01-CC10, execução do app e
   checklist para o grupo.
4. [Registro de conferência](registro_execucao.json) e
   [manifesto de documentação](manifesto_documentacao.json): fontes, código,
   produtos e evidências identificados por SHA-256.

O PDF/Markdown compartilham uma única fonte de conteúdo em `gerar_documentacao.py`.
Métricas dos modelos e controles centrais são lidos dos agregados públicos, não
ajustados para melhorar o resultado. Capturas são reutilizadas da etapa 07 e
incorporadas com seus hashes verificados, sem recriar telas fictícias.

## Reprodução

Na raiz do repositório, com Python 3.12 e ambiente virtual ativo:

```powershell
cd inteligencia_de_carreiras/08_documentacao_final
python -m pip install -r requirements.txt
python gerar_documentacao.py
python validar_documentacao.py
```

O gerador exige as evidências da etapa 07 e o pacote público intactos. Não precisa
das respostas G12 nem retreina modelos. A validação confere hashes, títulos,
paginação, imagens, links e coerência dos critérios. O estado inicial é
`VALIDADA_AGUARDANDO_REVISAO_VISUAL`, não aprovação visual automática.

Renderizar o PDF com Poppler (`pdftoppm -r 110 -png documentacao_final.pdf CAMINHO/pagina`),
inspecionar todas as páginas e só então confirmar:

```powershell
python validar_documentacao.py --renders CAMINHO --revisao-visual-confirmada
```

Renders temporários ficam fora dos arquivos de entrega; o registro mantém seus
hashes. Regenerar o documento exige repetir conferência e inspeção visual.

## Estado Consolidado

As oito etapas têm seus artefatos técnicos/documentais organizados. A revisão
estruturada pelos colegas, o commit/push quando solicitado e a implantação externa
com teste remoto ainda não ocorreram. A pesquisa G12 continua restrita.

Os relatórios e JSONs das etapas anteriores são registros históricos. Por exemplo,
a pendência de documentação 08 no registro da etapa 07 descreve aquele momento;
seu encerramento é registrado aqui, sem adulterar a evidência anterior. A matriz
de critérios e este índice mostram a situação atual. Não foram alterados dados,
modelos, código do dashboard ou arquivos históricos da aplicação nesta etapa.

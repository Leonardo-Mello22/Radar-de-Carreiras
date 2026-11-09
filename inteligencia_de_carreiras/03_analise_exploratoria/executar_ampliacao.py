"""Execute the expanded analysis notebook using only the public aggregates."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess
import sys

import nbformat
from nbclient import NotebookClient

AREA = Path(__file__).resolve().parent
KERNEL = "radar-ampliacao"
md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell


def notebook():
    return nbformat.v4.new_notebook(cells=[
        md("# Radar de Carreiras: análise ampliada 2025–2026\n"
           "Revisão pública das etapas 03–05. Cada base mantém sua população e período. "
           "As perguntas P9–P12 da pesquisa própria permanecem na análise original e na aba CESAR School."),
        code("""%matplotlib inline
from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd

dashboard = Path.cwd().parent / '06_dashboard_e_publicacao'
sys.path.insert(0, str(dashboard))
from dados import load_expansion
p = load_expansion(dashboard / 'dados_ampliados')
colors = ['#D25E00', '#303843', '#6D7B62']
assert p['metadata']['fontes']['caged_ti']['n'] == p['eda_movimentacoes'].movimentacoes.sum()"""),
        md("## P1–P3. Emprego formal em TI\n"
           "A série cobre 21 competências. Os períodos comparáveis são janeiro a setembro de ambos os anos. "
           "O intervalo p10–p90 não é mínimo–máximo; admissões e saídas não acompanham as mesmas pessoas."),
        code("""month = p['eda_movimentacoes'].set_index('competencia')
ax = month[['admissoes', 'desligamentos']].plot(figsize=(10, 3.5), color=colors[:2], marker='o')
ax.set(ylabel='Movimentações', xlabel='Competência')
plt.tight_layout()
plt.show()
display(p['eda_comparacao_anos'].round(2))
c = p['emprego']
display(c.loc[c.geo.isin(['BR','NE','UF_PE']) & c.periodo.eq('todos') & c.tipo.eq('total'),
    ['geo','admissoes_validos','admissoes_p10','admissoes_p50','admissoes_p90',
     'desligamentos_validos','desligamentos_p10','desligamentos_p50','desligamentos_p90']].round(2))"""),
        md("## P4. Salário, escolaridade, idade, jornada e ocupação\n"
           "As faixas descrevem relações marginais. Não controlam a composição dos cargos, "
           "a senioridade ou diferenças regionais; não identificam efeitos causais."),
        code("""f = p['eda_associacoes_salariais']
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for ax, field in zip(axes.flat, f.dimensao.unique()):
    s = f.loc[f.dimensao.eq(field)].sort_values('p50')
    ax.hlines(s.categoria, s.p10, s.p90, color='#AEB6C0', lw=4)
    ax.scatter(s.p50, s.categoria, color=colors[0], zorder=3)
    ax.set(title=field.replace('_', ' '), xlabel='Salário de admissão, R$ de março de 2025')
plt.tight_layout()
plt.show()"""),
        md("## P5–P8. Perfil e busca de emprego por edição\n"
           "As edições são amostras voluntárias diferentes. Iniciantes têm até dois anos de experiência "
           "ou declararam não ter experiência. As faixas salariais são respostas ordenadas, não valores exatos. "
           "Categorias com menos de cinco respostas não são mostradas nas tabelas detalhadas."),
        code("""display(p['eda_comparacao_pesquisas'].round(4))
beginner = p['eda_iniciantes'].query("dimensao == 'modelo_trabalho'").copy()
beginner['proporcao'] = beginner.n / beginner.denominador
beginner.pivot(index='categoria', columns='edicao', values='proporcao').plot.barh(figsize=(8,3), color=colors[:2])
plt.xlabel('Proporção das respostas válidas de iniciantes')
plt.tight_layout()
plt.show()
tech = p['tecnologias'].query("geo == 'BR' and senioridade == 'Todos' and modelo == 'Todos'")
tech.pivot(index='tecnologia', columns='edicao', values='proporcao').plot.barh(figsize=(8,4), color=colors[:2])
plt.xlabel('Proporção da base válida de cada tecnologia')
plt.tight_layout()
plt.show()
display(p['eda_faixas_por_perfil'].query("dimensao == 'senioridade_declarada'").head(12))
display(p['eda_busca_por_perfil'].query("dimensao == 'modelo_trabalho'").round(4))"""),
        md("## Etapa 04. Regressão salarial\n"
           "Seleção em out–dez/2025 e teste reservado em jan–set/2026. "
           "A referência é a mediana do treino. O gráfico de dispersão usa contagens agregadas; "
           "o corte visual não exclui eventos das métricas."),
        code("""display(p['regressao_validacao'][['modelo', 'n', 'mae']].round(3))
display(p['regressao'].round(3))
scatter = p['regressao_dispersao']
fig, ax = plt.subplots(figsize=(6,4))
ax.scatter(scatter.observado, scatter.previsto, s=scatter.n.clip(upper=400)/5, alpha=.55, color=colors[0])
ax.plot([0,30000], [0,30000], color=colors[1], ls=':')
ax.set(xlabel='Observado (R$)', ylabel='Estimado (R$)', title='Faixas de R$ 1 mil, n ≥ 30')
plt.tight_layout()
plt.show()
p['regressao_mensal'].set_index('competencia')[['observado','previsto']].plot(color=colors[:2], marker='o')
plt.ylabel('Mediana em R$')
plt.tight_layout()
plt.show()
p['regressao_residuos'].set_index('faixa').n.plot.barh(color=colors[0])
plt.xlabel('Admissões por faixa do resíduo')
plt.tight_layout()
plt.show()"""),
        md("## Etapa 05. Classificação entre edições\n"
           "O ajuste usa a edição 2024/2025; 2025/2026 é o teste. "
           "O alvo é a declaração de busca ativa, não uma saída futura. "
           "Acurácia isolada deve ser lida junto com recall e com a referência majoritária."),
        code("""display(p['classificacao_validacao'].round(4))
display(p['classificacao'].round(4))
key = p['metadata']['modelos']['classificacao']['selecionado']
m = p['classificacao'].set_index('modelo').loc[key]
display(pd.DataFrame([[m.tn,m.fp],[m.fn,m.tp]], index=['Real: não','Real: sim'], columns=['Estimado: não','Estimado: sim']).astype(int))
fig, axes = plt.subplots(1,2,figsize=(10,4))
for (name, f), color in zip(p['classificacao_curvas'].groupby('modelo'), colors):
    axes[0].plot(f.fpr, f.recall, label=name, color=color)
    axes[1].plot(f.recall, f.precisao, label=name, color=color)
axes[0].set(xlabel='Taxa de falsos positivos', ylabel='Recall', title='ROC')
axes[1].set(xlabel='Recall', ylabel='Precisão', title='Precisão × recall')
for ax in axes:
    ax.set(xlim=(0,1), ylim=(0,1))
    ax.legend()
plt.tight_layout()
plt.show()"""),
        md("## Leitura final\n"
           "As diferenças entre anos no CAGED comparam os mesmos nove meses. Mudanças na composição "
           "das respostas do State of Data não demonstram mudanças nas mesmas pessoas. "
           "O baixo recall e os erros salariais impedem o uso individual dos modelos."),
    ], metadata={"kernelspec": {"display_name": "Radar ampliado", "language": "python", "name": KERNEL}})


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    prefix = AREA / "resultados_locais/.jupyter_ampliacao"
    for name, path in {"MPLCONFIGDIR": prefix / "matplotlib", "IPYTHONDIR": prefix / "ipython",
                       "JUPYTER_RUNTIME_DIR": prefix / "runtime", "JUPYTER_CONFIG_DIR": prefix / "config"}.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(path)
    subprocess.run([sys.executable, "-m", "ipykernel", "install", "--prefix", str(prefix),
                    "--name", KERNEL, "--display-name", "Radar ampliado"], check=True)
    os.environ["JUPYTER_PATH"] = str(prefix / "share/jupyter")
    nb = notebook()
    executed = NotebookClient(nb, timeout=120, kernel_name=KERNEL, allow_errors=False,
                              resources={"metadata": {"path": str(AREA)}}).execute()
    nbformat.validate(executed)
    nbformat.write(executed, AREA / "analise_ampliada.ipynb")
    print("Notebook ampliado executado.", flush=True)


if __name__ == "__main__":
    main()

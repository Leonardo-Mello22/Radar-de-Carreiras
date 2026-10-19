"""Generate and execute the notebook, with restricted research outputs kept local."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter


AREA = Path(__file__).resolve().parent
TITLES = {
    "P1": "Salários de admissão: Pernambuco, Nordeste e Brasil",
    "P2": "Admissões e desligamentos no trimestre",
    "P3": "Comparação de grupos de admissão e desligamento",
    "P4": "Escolaridade, idade, jornada e salário",
    "M1": "Análise multivariada de perfis UF/área",
    "P5": "Perfis de início na área de dados",
    "P6": "Faixas de salário declaradas por perfil",
    "P7": "Tecnologias e denominadores por item",
    "P8": "Busca ativa declarada e associações por perfil",
    "P9": "Dificuldades de informação na pesquisa G12",
    "P10": "Prioridades e intenção de uso na pesquisa G12",
    "P11": "Expectativa salarial e experiência: análise restrita",
    "P12": "Intenções distintas de mudança na pesquisa G12",
}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def notebook():
    cells = [nbformat.v4.new_markdown_cell(
        "# Análise exploratória de carreiras\n\nRadar de Carreira em TI. Grupo 12. CESAR School.\n\n"
        "Etapa 03. Versão 1.0. 14 de outubro de 2026.\n\n"
        "**Uso local restrito:** este notebook reúne resultados da pesquisa própria, cujo consentimento para divulgação não foi confirmado. "
        "Não publicar a cópia executada ou seu HTML sem revisão. A versão de código sem saídas pode ser versionada.\n\n"
        "Novo CAGED, State of Data e pesquisa G12 são analisados separadamente. A matriz de desk research é contexto, não microdado."),
        nbformat.v4.new_markdown_cell(
        "## Método e leitura\n\n"
        "CAGED: MOV de jan-mar/2025, famílias CBO do projeto, salário mensal real a preços de mar/2025. "
        "Contagens mantêm salários sinalizados; estatísticas salariais usam somente válidos. Percentis por grupo exigem n>=30. "
        "Recortes PE/NE/Brasil se sobrepõem.\n\n"
        "State of Data: residentes no Brasil, com denominador específico por item. Faixas salariais não viram valores exatos; "
        "nulos de tecnologia não viram Não. Senioridade é declarada, não inferida.\n\n"
        "G12: 35 respostas; três Q07 fora de domínio, expectativa sinalizada e intervalo de experiência preservados. "
        "Notas Q05 sem âncoras não são interpretadas por direção. A dispersão de expectativa é interna.\n\n"
        "As associações e clusters são exploratórios. Não foram treinados regressores ou classificadores; essas avaliações pertencem às fases 04 e 05."),
        nbformat.v4.new_code_cell(
        "from pathlib import Path\nimport sys\nfrom IPython.display import display, Markdown, Image\n\n"
        "local = Path.cwd()\n"
        "EDA = local if (local / 'analise.py').exists() else local / 'inteligencia_de_carreiras/03_analise_exploratoria'\n"
        "if not (EDA / 'analise.py').exists():\n    raise FileNotFoundError('Execute na raiz do repositorio ou na pasta da etapa 03.')\n"
        "sys.path.insert(0, str(EDA))\nfrom analise import Exploracao\nanalise = Exploracao(EDA)\n"
        "display(Markdown('Fontes preparadas conferidas por SHA-256 antes da analise.'))")]
    for key, title in TITLES.items():
        source = "Pesquisa própria G12: seção restrita" if key in ("P9", "P10", "P11", "P12") else "Fonte pública; universo específico informado nos gráficos e tabelas"
        cells.append(nbformat.v4.new_markdown_cell(f"## {key}. {title}\n\n{source}."))
        cells.append(nbformat.v4.new_code_cell(
            f"resultado = analise.run('{key}')\n"
            "for nome, tabela in resultado['tabelas'].items():\n"
            "    display(Markdown('### ' + nome.replace('_', ' ').capitalize()))\n"
            "    display(tabela.round(4).head(16))\n"
            "    if len(tabela) > 16:\n"
            "        display(Markdown(f'Exibidas 16 de {len(tabela)} linhas; CSV completo na pasta de resultados correspondente.'))\n"
            "for grafico in resultado['graficos']:\n"
            "    display(Image(filename=str(grafico)))\n"
            "display(Markdown('### Interpretacao' + chr(10) * 2 + resultado['interpretacao']))"))
    cells += [nbformat.v4.new_markdown_cell(
        "## Encerramento e limites\n\n"
        "As perguntas P1-P12 têm análises e interpretações. P8 contém apenas distribuição do alvo e associações; métricas de classificadores "
        "serão produzidas na fase 05. M1 descreve grupos de agregados, não classes ou trajetórias individuais.\n\n"
        "A pesquisa própria não representa todo o mercado. Autorização, escala Q05 e respostas sinalizadas precisam de confirmação. "
        "Não divulgar células raras ou pontos individuais. A síntese versionável contém apenas as fontes públicas.\n\n"
        "Procedência, enunciados e regras constam nas fases 01/02 e nos manifestos em datasets/."),
        nbformat.v4.new_code_cell("analise.write_summary()\ndisplay(Markdown('Analise concluida; fontes e resultados permanecem separados.'))")]
    return nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                                       "language_info": {"name": "python", "version": platform.python_version()}})


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    local = AREA / "resultados_locais"
    local.mkdir(exist_ok=True)
    prefix = local / ".jupyter"
    for name, path in {"MPLCONFIGDIR": local / ".cache/matplotlib", "IPYTHONDIR": prefix / "ipython",
                       "JUPYTER_RUNTIME_DIR": prefix / "runtime", "JUPYTER_CONFIG_DIR": prefix / "config"}.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(path)
    subprocess.run([sys.executable, "-m", "ipykernel", "install", "--prefix", str(prefix), "--name", "radar-avd", "--display-name", "Radar AVD"], check=True)
    bundled_data = Path(nbformat.__file__).resolve().parent.parent / "share/jupyter"
    os.environ["JUPYTER_PATH"] = os.pathsep.join(str(path) for path in (prefix / "share/jupyter", bundled_data) if path.exists())
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    template = notebook()
    nbformat.validate(template)
    for index, cell in enumerate(template.cells):
        if cell.cell_type == "code":
            compile(cell.source, f"cell_{index}", "exec")
    nbformat.write(template, AREA / "analise_exploratoria.ipynb")
    started = datetime.now(timezone.utc).isoformat()
    initial = {"status": "EM_EXECUCAO", "inicio_utc": started,
               "codigo_sha256": {name: sha256(AREA / name) for name in ["analise.py", "executar_analise.py"]}}
    (AREA / "registro_execucao.json").write_text(json.dumps(initial, indent=2), encoding="utf-8")
    def progress(cell, cell_index, **kwargs):
        if cell.cell_type == "code":
            print(f"[notebook] Executando celula {cell_index + 1}/{len(template.cells)}", flush=True)
    client = NotebookClient(template, timeout=args.timeout, kernel_name="radar-avd", allow_errors=False,
                            resources={"metadata": {"path": str(AREA)}}, on_cell_start=progress)
    try:
        executed = client.execute()
    except Exception as error:
        initial.update(status="FALHOU", classe_erro=type(error).__name__)
        (AREA / "registro_execucao.json").write_text(json.dumps(initial, indent=2), encoding="utf-8")
        raise
    nbformat.validate(executed)
    errors = [out for cell in executed.cells if cell.cell_type == "code" for out in cell.outputs if out.output_type == "error"]
    if errors:
        raise ValueError("Notebook contains execution errors")
    nbformat.write(executed, local / "analise_exploratoria_executada.ipynb")
    exporter = HTMLExporter()
    exporter.exclude_input = True
    body, _ = exporter.from_notebook_node(executed)
    (local / "analise_exploratoria.html").write_text(body, encoding="utf-8")
    packages = ["numpy", "pandas", "pyarrow", "matplotlib", "scipy", "scikit-learn", "nbformat", "nbclient", "nbconvert", "ipykernel",
                "jupyter-core", "jupyter-client", "pyzmq", "ipython", "traitlets"]
    dependencies = {name: importlib.metadata.version(name) for name in packages}
    (AREA / "requirements.txt").write_text("\n".join(f"{name}=={version}" for name, version in dependencies.items()) + "\n", encoding="ascii")
    source_root = AREA.parent / "datasets/tratados"
    stems = ["caged_ti", "state_of_data_brasil", "pesquisa_grupo12_respostas", "pesquisa_grupo12_prioridades"]
    public_figures = sorted((AREA / "resultados_fontes_publicas/graficos").glob("*.png"))
    private_figures = sorted((local / "pesquisa_grupo12/graficos").glob("*.png"))
    images_in_notebook = sum("image/png" in out.get("data", {}) for cell in executed.cells if cell.cell_type == "code" for out in cell.outputs)
    report = {"status": "EXECUTADO_SEM_ERROS", "inicio_utc": started, "fim_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "dependencias": dependencies,
              "perguntas": list(TITLES), "celulas_executadas": sum(c.cell_type == "code" for c in executed.cells),
              "imagens_embutidas": images_in_notebook, "graficos_fontes_publicas": len(public_figures), "graficos_pesquisa_restritos": len(private_figures),
              "fontes_sha256": {stem: sha256(source_root / f"{stem}.parquet") for stem in stems},
              "codigo_sha256": {name: sha256(AREA / name) for name in ["analise.py", "executar_analise.py"]},
              "notebook_fonte_sha256": sha256(AREA / "analise_exploratoria.ipynb"),
              "privacidade": "Copia executada/HTML e P9-P12 locais, ignorados pelo Git; consentimento de divulgacao nao confirmado.",
              "limites": "Exploracao, sem causalidade, regressao ou classificacao supervisionada; fontes nao concatenadas."}
    (AREA / "registro_execucao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()

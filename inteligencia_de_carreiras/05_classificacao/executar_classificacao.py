"""Generate, execute and export the classification notebook with integrity records."""
from __future__ import annotations

import argparse
import asyncio
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

from classificacao import digest


AREA = Path(__file__).resolve().parent
TITLES = {
    "C0": "Alvo real, elegibilidade e particoes",
    "C1": "Validacao apenas no treino e modelos simples",
    "C2": "Acuracia, precisao, recall e F1",
    "C3": "Matrizes de confusao e tipos de erro",
    "C4": "Curvas ROC e ROC-AUC",
    "C5": "Curvas precision-recall e Average Precision",
    "C6": "Efeito do limiar: diagnostico interno do treino",
    "C7": "Calibracao descritiva dos escores",
    "C8": "Cobertura, elegibilidade e limites por recorte",
}
PACKAGES = ["numpy", "pandas", "pyarrow", "matplotlib", "scipy", "scikit-learn", "nbformat", "nbclient",
            "nbconvert", "ipykernel", "jupyter-core", "jupyter-client", "pyzmq", "ipython", "traitlets", "pillow"]


def notebook():
    cells = [nbformat.v4.new_markdown_cell(
        "# Classificação de busca ativa por emprego\n\n"
        "Radar de Carreira em TI. Grupo 12. CESAR School. Etapa 05. 19 de outubro de 2026.\n\n"
        "**Objetivo:** avaliar visualmente classificadores simples de busca ativa **declarada**, "
        "com dados reais da pesquisa State of Data Brazil 2024-2025 e teste separado.\n\n"
        "Não é previsão de desligamento futuro ou sistema para rotular empregados. O resultado serve ao estudo "
        "de avaliação de classificadores, não a decisões laborais individuais. CAGED e G12 não entram na tarefa."),
        nbformat.v4.new_markdown_cell(
        "## Protocolo anterior ao teste\n\n"
        "1. Residentes no Brasil; excluir alvo ausente, sem transformar em classe 0.\n"
        "2. Classe 1: busca de oportunidades dentro/fora do Brasil ou apenas fora. Classe 0: aberta a oportunidades "
        "sem busca ativa, ou sem busca e sem intenção de mudar nos próximos seis meses.\n"
        "3. Separação estratificada 80/20, semente 12, antes de ajustar pré-processamento.\n"
        "4. Cinco entradas nominais: senioridade declarada, formação, vínculo agrupado, modelo de trabalho e experiência em dados.\n"
        "5. Comparar classe majoritária, regressão logística e árvore simples. Seleção pela maior Average Precision média "
        "em cinco folds estratificados apenas do treino. Hiperparâmetros e limiar 0,5 fixos.\n"
        "6. Reajustar no treino completo e avaliar uma vez o protocolo no teste, sem reescolher modelo ou limiar.\n\n"
        "**Vazamento:** a pergunta-alvo, cópias, entrevistas recentes, oportunidade buscada, tempo de busca e objetivo "
        "de carreira não entram como preditores. O vínculo agrupado não mantém as menções de busca do texto bruto. "
        "Ausências de senioridade podem ser estruturais, não significam Júnior.\n\n"
        "As métricas de precisão, recall e F1 usam a classe positiva 1. AP é Average Precision, não área trapezoidal "
        "genérica. Precisão sem previsão positiva é registrada como 0 por convenção; isso é explicitado na interpretação."),
        nbformat.v4.new_code_cell(
        "from pathlib import Path\nimport sys\nimport inspect\n"
        "from IPython.display import display, Markdown, Image, Code\n\n"
        "local = Path.cwd()\n"
        "AREA = local if (local / 'classificacao.py').exists() else local / 'inteligencia_de_carreiras/05_classificacao'\n"
        "if not (AREA / 'classificacao.py').exists():\n    raise FileNotFoundError('Execute na raiz do repositorio ou na etapa 05.')\n"
        "sys.path.insert(0, str(AREA))\n"
        "from classificacao import Classificacao, active_target, features, make_model, metricas\n"
        "analise = Classificacao(AREA)\n"
        "display(Markdown('Fonte preparada conferida por SHA-256; treino e teste separados antes de ajustar os modelos.'))"),
        nbformat.v4.new_markdown_cell("## Código das regras e modelos\n\nAs funções abaixo são executadas nesta análise; o código completo está em `classificacao.py`."),
        nbformat.v4.new_code_cell("for funcao in (active_target, features, make_model, metricas):\n    display(Code(inspect.getsource(funcao), language='python'))")]
    for key, title in TITLES.items():
        cells.append(nbformat.v4.new_markdown_cell(f"## {key}. {title}"))
        cells.append(nbformat.v4.new_code_cell(
            f"resultado = analise.run('{key}')\n"
            "for nome, tabela in resultado['tabelas'].items():\n"
            "    display(Markdown('### ' + nome.replace('_', ' ').capitalize()))\n"
            "    display(tabela.round(4).head(18))\n"
            "    if len(tabela) > 18:\n"
            "        display(Markdown(f'Exibidas 18 de {len(tabela)} linhas; CSV completo em resultados/tabelas.'))\n"
            "for grafico in resultado['graficos']:\n"
            "    display(Image(filename=str(grafico)))\n"
            "display(Markdown('### Interpretacao' + chr(10)*2 + resultado['interpretacao']))"))
    cells += [nbformat.v4.new_markdown_cell(
        "## Conclusão e uso responsável\n\n"
        "A síntese é gerada a partir dos resultados, incluindo métricas desfavoráveis. A pesquisa é voluntária e "
        "o teste pertence à mesma coleta; não houve validação externa ou temporal. O alvo ausente está concentrado "
        "em ramos do questionário, o que limita a população elegível.\n\n"
        "Saídas versionáveis são agregadas. IDs e probabilidades por participante ficam em `resultados_locais/`, "
        "ignorada pelo Git. Não usar o classificador para monitorar trabalhadores ou decidir contratação/desligamento. "
        "Nada foi integrado automaticamente ao dashboard ou enviado ao GitHub."),
        nbformat.v4.new_code_cell(
        "analise.summary()\n"
        "display(Markdown((AREA / 'sintese_achados.md').read_text(encoding='utf-8')))\n"
        "display(Markdown('Analise concluida. Auditoria e tabelas completas em resultados/.'))")]
    return nbformat.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": platform.python_version()}})


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    local = AREA / "resultados_locais"
    prefix = local / ".jupyter"
    for name, path in {"MPLCONFIGDIR": local / ".cache/matplotlib", "IPYTHONDIR": prefix / "ipython",
                       "JUPYTER_RUNTIME_DIR": prefix / "runtime", "JUPYTER_CONFIG_DIR": prefix / "config",
                       "TEMP": local / ".tmp", "TMP": local / ".tmp"}.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(path)
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    bundled_data = Path(nbformat.__file__).resolve().parent.parent / "share/jupyter"
    os.environ["JUPYTER_PATH"] = os.pathsep.join(str(p) for p in [prefix / "share/jupyter", bundled_data])
    report = {"status": "EM_EXECUCAO", "inicio_utc": datetime.now(timezone.utc).isoformat(),
              "codigo_sha256": {name: digest(AREA / name) for name in ["classificacao.py", "executar_classificacao.py"]}}
    record = AREA / "registro_execucao.json"
    record.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        subprocess.run([sys.executable, "-m", "ipykernel", "install", "--prefix", str(prefix),
                        "--name", "radar-classificacao", "--display-name", "Radar Classificacao"], check=True)
        template = notebook()
        nbformat.validate(template)
        for index, cell in enumerate(template.cells):
            if cell.cell_type == "code":
                compile(cell.source, f"cell_{index}", "exec")
        nbformat.write(template, AREA / "classificacao_busca_ativa.ipynb")
        def progress(cell, cell_index, **kwargs):
            if cell.cell_type == "code":
                print(f"[notebook] Celula {cell_index+1}/{len(template.cells)}", flush=True)
        executed = NotebookClient(template, timeout=args.timeout, startup_timeout=90, kernel_name="radar-classificacao", allow_errors=False,
                                 resources={"metadata": {"path": str(AREA)}}, on_cell_start=progress).execute()
        nbformat.validate(executed)
        code = [c for c in executed.cells if c.cell_type == "code"]
        if any(c.execution_count is None for c in code) or any(o.output_type == "error" for c in code for o in c.outputs):
            raise ValueError("Notebook did not execute cleanly")
        output = AREA / "resultados"
        nbformat.write(executed, output / "classificacao_busca_ativa_executada.ipynb")
        exporter = HTMLExporter()
        exporter.exclude_input = True
        body, _ = exporter.from_notebook_node(executed)
        (output / "classificacao_busca_ativa.html").write_text(body, encoding="utf-8")
        versions = {name: importlib.metadata.version(name) for name in PACKAGES}
        (AREA / "requirements.txt").write_text("\n".join(f"{n}=={v}" for n, v in versions.items())+"\n", encoding="ascii")
        tables = sorted((output / "tabelas").glob("*.csv"))
        figures = sorted((output / "graficos").glob("*.png"))
        audit = json.loads((output / "auditoria_modelagem.json").read_text(encoding="utf-8"))
        products = [*figures, *tables, output / "auditoria_modelagem.json", output / "classificacao_busca_ativa_executada.ipynb",
                    output / "classificacao_busca_ativa.html", AREA / "sintese_achados.md"]
        report.update(status="EXECUTADO_SEM_ERROS", fim_utc=datetime.now(timezone.utc).isoformat(),
                      python=platform.python_version(), dependencias=versions, secoes=list(TITLES), celulas_executadas=len(code),
                      imagens_embutidas=sum("image/png" in o.get("data", {}) for c in code for o in c.outputs),
                      n_graficos=len(figures), n_tabelas=len(tables), fonte_sha256=audit["fonte_sha256"],
                      notebook_fonte_sha256=digest(AREA / "classificacao_busca_ativa.ipynb"),
                      modelo_escolhido_antes_do_teste=audit["modelo_escolhido_antes_do_teste"], limiar_fixo=audit["limiar_fixo"],
                      produtos_sha256={str(p.relative_to(AREA)).replace("\\", "/"): digest(p) for p in products},
                      limites="Intencao declarada, pesquisa voluntaria, vies de elegibilidade; sem validacao externa, uso laboral individual ou integracao automatica.")
        record.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as error:
        report.update(status="FALHOU", classe_erro=type(error).__name__)
        record.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    print(json.dumps({k: report[k] for k in ["status", "celulas_executadas", "n_graficos", "n_tabelas", "modelo_escolhido_antes_do_teste"]}), flush=True)


if __name__ == "__main__":
    main()

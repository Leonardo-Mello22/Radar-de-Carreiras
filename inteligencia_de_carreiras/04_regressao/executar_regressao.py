"""Build a clean notebook, execute it, and export self-contained public results."""
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

from regressao import digest


AREA = Path(__file__).resolve().parent
TITLES = {
    "R0": "Universo, alvo, entradas e separacao temporal",
    "R1": "Validacao interna, ajuste e avaliacao reservada",
    "R2": "Dispersao por idade e linha de tendencia",
    "R3": "Salarios observados versus previstos",
    "R4": "Residuos e variacao nao explicada",
    "R5": "Comparacao com a mediana do treino",
    "R6": "Desempenho por regiao, UF e area de TI",
    "R7": "Calibracao descritiva no teste",
    "R8": "Sensibilidade a cauda e categorias novas",
}
PACKAGES = ["numpy", "pandas", "pyarrow", "matplotlib", "scipy", "scikit-learn", "nbformat", "nbclient",
            "nbconvert", "ipykernel", "jupyter-core", "jupyter-client", "pyzmq", "ipython", "traitlets", "pillow"]


def notebook():
    cells = [nbformat.v4.new_markdown_cell(
        "# Regressão salarial: tendências e limites\n\n"
        "Radar de Carreira em TI. Grupo 12. CESAR School. Etapa 04. 19 de outubro de 2026.\n\n"
        "**Pergunta:** como o salário mensal real de admissão se relaciona com idade, jornada, cargo, UF e escolaridade, "
        "e quanto modelos lineares simples explicam em comparação com uma referência constante?\n\n"
        "Somente Novo CAGED MOV, jan-mar/2025; salários a preços de mar/2025. Não representa o mercado atual de 2026, "
        "salário júnior ou crescimento individual de carreira. Nenhuma resposta G12 é usada."),
        nbformat.v4.new_markdown_cell(
        "## Protocolo definido antes do teste\n\n"
        "1. Admissões com `salario_valido=True`, preservando todos os valores elegíveis, inclusive caudas.\n"
        "2. Validação interna: ajustar em janeiro e avaliar em fevereiro; escolher menor MAE, com preferência por simplicidade no empate.\n"
        "3. Reajustar os três modelos em janeiro-fevereiro. Março é reservado para avaliação final, sem nova escolha ou ajuste.\n"
        "4. Comparar mediana do treino, regressão linear de idade e regressão linear múltipla com Ridge (`alpha=10`, fixo).\n"
        "5. Imputação, escala, categorias e coeficientes aprendidos somente no treino. Nenhuma variável derivada do salário entra como preditor.\n\n"
        "**Resíduo = observado − previsto:** valores positivos indicam subestimação. MAE é erro absoluto médio; "
        "RMSE penaliza mais erros extremos. R² pode ser negativo. Métricas são descritivas de eventos, sem garantia de independência.\n\n"
        "A correção IPCA usa referência monetária comum de mar/2025 para a análise retrospectiva, não uma simulação de previsão "
        "em tempo real em janeiro. Idade não mede experiência; cargo/UF/escolaridade são categorias nominais."),
        nbformat.v4.new_code_cell(
        "from pathlib import Path\nimport sys\nimport inspect\n"
        "from IPython.display import display, Markdown, Image, Code\n\n"
        "local = Path.cwd()\n"
        "AREA = local if (local / 'regressao.py').exists() else local / 'inteligencia_de_carreiras/04_regressao'\n"
        "if not (AREA / 'regressao.py').exists():\n    raise FileNotFoundError('Execute na raiz do repositorio ou na pasta da etapa 04.')\n"
        "sys.path.insert(0, str(AREA))\n"
        "from regressao import Regressao, features, make_model, metricas\n"
        "analise = Regressao(AREA)\n"
        "display(Markdown('Fonte preparada conferida por SHA-256. O conjunto de teste e marco/2025.'))"),
        nbformat.v4.new_markdown_cell("## Código dos modelos e prevenção de vazamento\n\nO código completo está em `regressao.py`; abaixo, as funções centrais executadas nesta análise."),
        nbformat.v4.new_code_cell("for funcao in (features, make_model, metricas):\n    display(Code(inspect.getsource(funcao), language='python'))")]
    for key, title in TITLES.items():
        cells.append(nbformat.v4.new_markdown_cell(f"## {key}. {title}"))
        cells.append(nbformat.v4.new_code_cell(
            f"resultado = analise.run('{key}')\n"
            "for nome, tabela in resultado['tabelas'].items():\n"
            "    display(Markdown('### ' + nome.replace('_', ' ').capitalize()))\n"
            "    display(tabela.round(4).head(18))\n"
            "    if len(tabela) > 18:\n"
            "        display(Markdown(f'Exibidas 18 de {len(tabela)} linhas. CSV completo em resultados/tabelas.'))\n"
            "for grafico in resultado['graficos']:\n"
            "    display(Image(filename=str(grafico)))\n"
            "display(Markdown('### Interpretacao' + chr(10)*2 + resultado['interpretacao']))"))
    cells += [nbformat.v4.new_markdown_cell(
        "## Conclusão e uso responsável\n\n"
        "A síntese a seguir é calculada a partir desta execução. Não há inferência causal, intervalos individuais, "
        "acompanhamento de vínculos ou previsão de carreira. Os erros refletem apenas um mês de avaliação. "
        "Não foram retirados salários válidos para melhorar as métricas.\n\n"
        "Gráficos e tabelas agregados são versionáveis; o extrato linha a linha de previsões fica local, ignorado pelo Git. "
        "Os códigos da etapa 03, os datasets e o aplicativo existente não são modificados pelo runner. "
        "A classificação supervisionada pertence à etapa 05, ainda pendente."),
        nbformat.v4.new_code_cell(
        "analise.summary()\n"
        "display(Markdown((AREA / 'sintese_achados.md').read_text(encoding='utf-8')))\n"
        "display(Markdown('Execucao concluida. Tabelas completas e auditoria em resultados/.'))")]
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
    started = datetime.now(timezone.utc).isoformat()
    report = {"status": "EM_EXECUCAO", "inicio_utc": started,
              "codigo_sha256": {name: digest(AREA / name) for name in ["regressao.py", "executar_regressao.py"]}}
    record = AREA / "registro_execucao.json"
    record.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        subprocess.run([sys.executable, "-m", "ipykernel", "install", "--prefix", str(prefix),
                        "--name", "radar-regressao", "--display-name", "Radar Regressao"], check=True)
        bundled_data = Path(nbformat.__file__).resolve().parent.parent / "share/jupyter"
        os.environ["JUPYTER_PATH"] = os.pathsep.join(str(p) for p in (prefix / "share/jupyter", bundled_data) if p.exists())
        template = notebook()
        nbformat.validate(template)
        for index, cell in enumerate(template.cells):
            if cell.cell_type == "code":
                compile(cell.source, f"cell_{index}", "exec")
        nbformat.write(template, AREA / "regressao_salarial.ipynb")
        def progress(cell, cell_index, **kwargs):
            if cell.cell_type == "code":
                print(f"[notebook] Celula {cell_index+1}/{len(template.cells)}", flush=True)
        executed = NotebookClient(template, timeout=args.timeout, kernel_name="radar-regressao", allow_errors=False,
                                 resources={"metadata": {"path": str(AREA)}}, on_cell_start=progress).execute()
        nbformat.validate(executed)
        code = [c for c in executed.cells if c.cell_type == "code"]
        if any(c.execution_count is None for c in code) or any(o.output_type == "error" for c in code for o in c.outputs):
            raise ValueError("Notebook did not execute cleanly")
        output = AREA / "resultados"
        nbformat.write(executed, output / "regressao_salarial_executada.ipynb")
        exporter = HTMLExporter()
        exporter.exclude_input = True
        body, _ = exporter.from_notebook_node(executed)
        (output / "regressao_salarial.html").write_text(body, encoding="utf-8")
        versions = {name: importlib.metadata.version(name) for name in PACKAGES}
        (AREA / "requirements.txt").write_text("\n".join(f"{n}=={v}" for n, v in versions.items()) + "\n", encoding="ascii")
        tables = sorted((output / "tabelas").glob("*.csv"))
        figures = sorted((output / "graficos").glob("*.png"))
        audit = json.loads((output / "auditoria_modelagem.json").read_text(encoding="utf-8"))
        report.update(status="EXECUTADO_SEM_ERROS", fim_utc=datetime.now(timezone.utc).isoformat(),
                      python=platform.python_version(), dependencias=versions, secoes=list(TITLES), celulas_executadas=len(code),
                      imagens_embutidas=sum("image/png" in o.get("data", {}) for c in code for o in c.outputs),
                      n_graficos=len(figures), n_tabelas=len(tables), fonte_sha256=audit["sha256_fonte"],
                      notebook_fonte_sha256=digest(AREA / "regressao_salarial.ipynb"),
                      modelo_escolhido_antes_do_teste=audit["modelo_escolhido_antes_do_teste"],
                      produtos_sha256={str(p.relative_to(AREA)).replace("\\", "/"): digest(p) for p in [*figures, *tables, output / "auditoria_modelagem.json", output / "regressao_salarial_executada.ipynb", output / "regressao_salarial.html", AREA / "sintese_achados.md"]},
                      limites="Relacoes observacionais; um mes de teste; sem trajetoria individual ou causalidade. Previsoes por linha somente locais.")
        record.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as error:
        report.update(status="FALHOU", classe_erro=type(error).__name__)
        record.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    print(json.dumps({k: report[k] for k in ["status", "celulas_executadas", "n_graficos", "n_tabelas", "modelo_escolhido_antes_do_teste"]}), flush=True)


if __name__ == "__main__":
    main()

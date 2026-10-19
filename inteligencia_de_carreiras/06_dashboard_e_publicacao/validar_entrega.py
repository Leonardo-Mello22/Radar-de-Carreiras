"""Validate all delivered data stages and record real test/browser outcomes."""
from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import time
import unittest
from datetime import datetime, timezone

os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
from dados import load_package

AREA = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    package = load_package(AREA / "dados_publicos")
    browser = json.loads((AREA / "evidencias/verificacao_browser.json").read_text(encoding="utf-8"))
    if browser["status"] != "APROVADO" or browser["script_sha256"] != sha(AREA / "verificar_navegador.py") or any(sha(AREA / n) != h for n, h in browser["codigo_sha256"].items()):
        raise ValueError("Browser verification does not match current dashboard code")
    groups = []
    for folder in ["datasets/scripts/tests", "03_analise_exploratoria/tests", "04_regressao/tests", "05_classificacao/tests", "06_dashboard_e_publicacao/tests"]:
        started = time.perf_counter()
        suite = unittest.TestLoader().discover(str(AREA.parent / folder))
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
        groups.append({"pasta": folder, "testes": result.testsRun, "sucesso": result.wasSuccessful(),
                       "falhas": len(result.failures), "erros": len(result.errors), "segundos": round(time.perf_counter()-started, 2)})
        print(f"[testes] {folder}: {result.testsRun}; sucesso={result.wasSuccessful()}", flush=True)
        if not result.wasSuccessful():
            print(output.getvalue(), flush=True)
    success = all(g["sucesso"] for g in groups)
    report = {"status": "VALIDADO_LOCALMENTE" if success else "FALHOU", "executado_em": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "dependencias": {n: importlib.metadata.version(n) for n in ["streamlit", "altair", "pandas", "numpy", "pyarrow", "playwright"]},
              "suites": groups, "total_testes": sum(g["testes"] for g in groups), "checks_navegador": len(browser["checks"]),
              "codigo_sha256": {n: sha(AREA / n) for n in ["dashboard.py", "dados.py", "preparar_pacote.py", "verificar_navegador.py", "validar_entrega.py"]},
              "manifesto_sha256": sha(AREA / "dados_publicos/manifesto.json"),
              "pacote_bytes": sum(v["bytes"] for v in package["metadata"]["arquivos"].values()),
              "publicacao_externa": {"realizada": False, "estado": "Proposta pronta; falta autorizacao de envio ao GitHub e configuracao da conta Streamlit."},
              "limites": "QA local da base do dashboard; consolidacao ampliada registrada na etapa 07. Feedback estruturado de usuarios e validacao remota continuam pendentes."}
    (AREA / "registro_execucao.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not success:
        raise SystemExit(1)
    print(json.dumps({k: report[k] for k in ["status", "total_testes", "checks_navegador", "pacote_bytes"]}), flush=True)


if __name__ == "__main__":
    main()

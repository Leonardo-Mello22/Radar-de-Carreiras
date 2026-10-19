"""One-command technical acceptance gate, with fresh audit/browser/test evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
AREA = Path(__file__).resolve().parent
DASHBOARD = AREA.parent / "06_dashboard_e_publicacao"
sys.path.insert(0, str(AREA))
from auditar_numeros import sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8502")
    parser.add_argument("--browser-executable")
    args = parser.parse_args()
    record = AREA / "registro_execucao.json"
    report = {"status": "EM_EXECUCAO", "inicio": datetime.now(timezone.utc).isoformat()}
    record.write_text(json.dumps(report), encoding="utf-8")
    try:
        browser_args = ["--url", args.url]
        if args.browser_executable:
            browser_args += ["--browser-executable", args.browser_executable]
        for script, options in [(AREA / "auditar_numeros.py", []),
                                (DASHBOARD / "verificar_navegador.py", browser_args),
                                (AREA / "verificar_navegador.py", browser_args),
                                (DASHBOARD / "validar_entrega.py", [])]:
            subprocess.run([sys.executable, str(script), *options], check=True, timeout=900)
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output).run(unittest.TestLoader().discover(str(AREA / "tests")))
        print(output.getvalue(), flush=True)
        if not result.wasSuccessful() or result.testsRun == 0:
            raise ValueError("Falha na suite de consolidacao")
        audit = json.loads((AREA / "resultados/auditoria_numerica.json").read_text(encoding="utf-8"))
        browser = json.loads((AREA / "evidencias/verificacao_browser.json").read_text(encoding="utf-8"))
        previous = json.loads((DASHBOARD / "registro_execucao.json").read_text(encoding="utf-8"))
        if audit["status"] != "APROVADO" or browser["status"] != "APROVADO" or previous["status"] != "VALIDADO_LOCALMENTE":
            raise ValueError("Evidencias nao aprovadas")
        inputs = [DASHBOARD / name for name in ["dashboard.py", "dados.py", "dados_publicos/manifesto.json"]]
        inputs += [AREA / name for name in ["auditar_numeros.py", "verificar_navegador.py", "validar_consolidacao.py", "tests/test_consolidacao.py", "requirements_validacao.txt"]]
        evidence = [AREA / "resultados/auditoria_numerica.json", AREA / "evidencias/verificacao_browser.json", DASHBOARD / "registro_execucao.json"]
        evidence += list((AREA / "evidencias").glob("*.png"))
        report.update({"status": "VALIDADO_TECNICAMENTE_AGUARDANDO_REVISAO_DO_GRUPO", "executado_em": datetime.now(timezone.utc).isoformat(),
                       "versao_dashboard": "1.1", "testes_anteriores": previous["total_testes"], "testes_consolidacao": result.testsRun,
                       "total_testes": previous["total_testes"] + result.testsRun,
                       "checks_browser_inicial": previous["checks_navegador"], "checks_browser_ampliado": len(browser["checks"]),
                       "auditoria": {k: audit[k] for k in ["recortes_caged", "recortes_state_of_data", "total_comparacoes", "n_divergencias"]},
                       "codigo_sha256": {str(p.relative_to(AREA.parent)): sha(p) for p in inputs},
                       "evidencias_sha256": {str(p.relative_to(AREA.parent)): sha(p) for p in evidence},
                       "validacao_com_usuarios": {"realizada": False, "estado": "Pendente. O solicitante viu a previa e achou boa; revisao estruturada pelos amigos/grupo ainda nao realizada."},
                       "publicacao_externa": False, "commit_push_realizado_nesta_etapa": False,
                       "pendencias": ["Revisao estruturada do grupo e tratamento de feedback", "Documentacao final da etapa 08", "Commit/push e hospedagem externa, seguidos de teste remoto"]})
    except Exception as error:
        report.update({"status": "FALHOU", "erro": str(error), "executado_em": datetime.now(timezone.utc).isoformat()})
        raise
    finally:
        record.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["status", "total_testes", "checks_browser_ampliado", "auditoria"]}), flush=True)


if __name__ == "__main__":
    main()

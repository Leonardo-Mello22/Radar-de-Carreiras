"""Expanded functional and responsive QA; no real-user feedback is simulated."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
from playwright.sync_api import expect, sync_playwright
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg

AREA = Path(__file__).resolve().parent
DASHBOARD = AREA.parent / "06_dashboard_e_publicacao"
sys.path.insert(0, str(AREA))
sys.path.insert(0, str(DASHBOARD))
from auditar_numeros import sha
from dados import caged_query, export_csv, load_package, profile_query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8502")
    parser.add_argument("--browser-executable")
    args = parser.parse_args()
    out = AREA / "evidencias"
    out.mkdir(exist_ok=True)
    report_path = out / "verificacao_browser.json"
    report_path.write_text(json.dumps({"status": "EM_TESTE"}), encoding="utf-8")
    package = load_package(DASHBOARD / "dados_publicos")
    checks, errors, screenshots = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=args.browser_executable)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.on("pageerror", lambda error: errors.append(str(error)))

        def settled():
            page.wait_for_function("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'", timeout=40000)
            page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")

        def finished(payload):
            if not isinstance(payload, bytes):
                return False
            message = ForwardMsg.FromString(payload)
            return message.WhichOneof("type") == "script_finished" and message.script_finished == ForwardMsg.FINISHED_SUCCESSFULLY

        def perform(action):
            with connection.expect_event("framereceived", predicate=finished, timeout=40000):
                action()
            settled()

        def view(name, heading):
            perform(lambda: page.get_by_role("radio", name=name, exact=True).click())
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()
            settled()

        def filters():
            if not page.locator('[data-testid="stExpander"] details').first.evaluate("node=>node.open"):
                page.get_by_text("Filtros do recorte", exact=True).click()
            page.wait_for_function("document.querySelector('[data-testid=stExpander]').getBoundingClientRect().height > 200")

        def select(index, label):
            page.get_by_role("combobox").nth(index).fill(label)
            perform(lambda: page.get_by_role("option", name=label, exact=True).click())

        def capture(name):
            page.screenshot(path=str(out / name), full_page=True)
            screenshots.append(name)

        with page.expect_websocket() as opened:
            page.goto(args.url, wait_until="domcontentloaded")
        connection = opened.value
        expect(page.get_by_role("heading", name="Emprego formal em TI", exact=True)).to_be_visible(timeout=40000)
        settled()
        filters()
        select(0, "Brasil")
        select(1, "SP")
        select(2, "Fev/2025")
        occupation = next(p["rotulo"] for p in package["metadata"]["catalogo"] if p["tipo"] == "cargo" and p["categoria"] == "212405")
        select(4, occupation)
        expected = caged_query(package, "UF_SP", "202502", "cargo", "212405")
        n = f"{int(expected.iloc[0].admissoes):,}".replace(",", ".")
        expect(page.locator('[data-testid="stMetricValue"]').nth(1)).to_have_text(n)
        expect(page.get_by_text("SP · Fev/2025", exact=True)).to_be_visible()
        expect(page.get_by_text("CBO 212405", exact=False)).to_be_visible()
        checks.append("recorte_uf_mes_ocupacao_confere_com_pacote")
        assert page.get_by_text("Nenhum grupo com pelo menos 30 salários válidos.", exact=True).count() == 0
        page.locator("svg.marks").first.wait_for(state="visible", timeout=30000)
        checks.append("grafico_salarial_ocupacao_coerente_com_indicadores")
        download_key = "export_" + hashlib.sha256(export_csv(expected)).hexdigest()[:16]
        button = page.locator(".st-key-" + download_key).get_by_role("button", name="Baixar recorte agregado", exact=True)
        expect(button).to_be_enabled()
        with page.expect_download() as download:
            button.click()
        actual = pd.read_csv(download.value.path(), dtype={"periodo": str, "categoria": str})
        pd.testing.assert_frame_equal(actual, expected.reset_index(drop=True), check_dtype=False, atol=1e-7, rtol=1e-12)
        checks.append("csv_baixado_confere_com_recorte_visivel")
        view("Fontes", "Fontes e limites")
        view("Emprego formal", "Emprego formal em TI")
        expect(page.locator('[data-testid="stMetricValue"]').nth(1)).to_have_text(n)
        expect(page.get_by_text("SP · Fev/2025", exact=True)).to_be_visible()
        checks.append("filtros_caged_persistem_apos_navegar")
        capture("01_recorte_consolidado_desktop.png")
        view("Perfis em dados", "Perfis na área de dados")
        filters()
        select(2, "Júnior")
        select(3, "Remoto")
        expected_n = int(profile_query(package, "BR", "Junior", "Remoto")["perfis"].iloc[0].n_respostas)
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text(f"{expected_n:,}".replace(",", "."))
        view("Emprego formal", "Emprego formal em TI")
        view("Perfis em dados", "Perfis na área de dados")
        expect(page.get_by_text("Senioridade: Júnior · Trabalho: Remoto", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text(f"{expected_n:,}".replace(",", "."))
        checks.append("filtros_perfis_persistem_sem_contaminar_caged")
        filters()
        select(1, "AC")
        expect(page.get_by_text("Nenhuma resposta neste recorte.", exact=True)).to_be_visible()
        assert page.locator('[data-testid="stMetricValue"]').count() == 0
        checks.append("estado_sem_dados_sem_metricas_antigas")
        perform(lambda: page.get_by_role("button", name="Restaurar filtros", exact=True).click())
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("5.076")
        settled()
        expect(page.get_by_role("combobox").nth(2)).to_have_value("Todos")
        expect(page.get_by_role("combobox").nth(3)).to_have_value("Todos")
        checks.append("restauracao_perfis_recupera_base_brasil")
        view("Fontes", "Fontes e limites")
        view("Perfis em dados", "Perfis na área de dados")
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("5.076")
        expect(page.get_by_text("Senioridade: Todos · Trabalho: Todos", exact=True)).to_be_visible()
        checks.append("restauracao_de_filtros_persiste_apos_navegar")
        view("Modelos", "Avaliação dos modelos")
        perform(lambda: page.get_by_role("radio", name="Busca ativa", exact=True).click())
        select(0, "Classe majoritária")
        expect(page.locator('[data-testid="stMetricValue"]').nth(2)).to_have_text("0,0%")
        view("Fontes", "Fontes e limites")
        view("Modelos", "Avaliação dos modelos")
        expect(page.locator('[data-testid="stMetricValue"]').nth(2)).to_have_text("0,0%")
        expect(page.get_by_role("combobox")).to_have_value("Classe majoritária")
        checks.append("modelo_baseline_persiste_e_expoe_recall_zero")
        capture("02_modelo_referencia_desktop.png")
        # Check keyboard selection separately from mouse-driven workflows.
        page.get_by_role("combobox").fill("Regressão logística")
        page.get_by_role("combobox").press("ArrowDown")
        perform(lambda: page.get_by_role("combobox").press("Enter"))
        expect(page.locator('[data-testid="stMetricValue"]').nth(2)).to_have_text("12,9%")
        assert page.locator('[data-testid="stException"]').count() == 0
        checks.append("seletor_modelo_acessivel_por_teclado")
        print("[browser 07] Filtros, CSV, persistencia, vazio e modelos conferidos", flush=True)
        for width, height in [(360, 800), (768, 1024), (1440, 1000)]:
            page.set_viewport_size({"width": width, "height": height})
            for name, heading in [("Emprego formal", "Emprego formal em TI"), ("Perfis em dados", "Perfis na área de dados"), ("Modelos", "Avaliação dos modelos"), ("Fontes", "Fontes e limites")]:
                view(name, heading)
                if name == "Perfis em dados":
                    expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("5.076")
                if name in ["Emprego formal", "Perfis em dados"] and page.locator('[data-testid="stExpander"] details').first.evaluate("node=>node.open"):
                    page.get_by_text("Filtros do recorte", exact=True).click()
                    page.wait_for_function("document.querySelector('[data-testid=stExpander]').getBoundingClientRect().height < 80")
                dimensions = page.evaluate("({width:innerWidth,scroll:document.documentElement.scrollWidth})")
                assert dimensions["scroll"] <= width+1, (name, dimensions)
                assert page.locator('[data-testid="stException"]').count() == 0
                if name != "Fontes":
                    page.locator("svg.marks").first.wait_for(state="visible", timeout=30000)
                    graphics = page.locator("svg.marks").evaluate_all("nodes=>nodes.map(svg=>{const r=svg.getBoundingClientRect();return r.width>80&&r.height>80&&svg.querySelectorAll('path,line,rect,circle').length>2;})")
                    assert graphics and all(graphics), (width, name, "blank chart")
                if width == 360 and name in ["Emprego formal", "Perfis em dados"]:
                    capture("03_emprego_mobile.png" if name == "Emprego formal" else "04_perfis_mobile.png")
            checks.append(f"quatro_visoes_sem_overflow_ou_graficos_vazios_{width}px")
        assert not errors, errors
        browser.close()
    report = {"status": "APROVADO", "executado_em": datetime.now(timezone.utc).isoformat(), "url": args.url,
              "checks": checks, "erros_javascript": errors, "viewports": [[360, 800], [768, 1024], [1440, 1000]],
              "codigo_sha256": {name: sha(DASHBOARD / name) for name in ["dashboard.py", "dados.py"]},
              "manifesto_sha256": sha(DASHBOARD / "dados_publicos/manifesto.json"), "script_sha256": sha(Path(__file__)),
              "screenshots_sha256": {name: sha(out / name) for name in screenshots},
              "limite": "QA automatizado em Chromium; nao substitui teste com participantes, auditoria WCAG ou outros navegadores."}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks)}), flush=True)


if __name__ == "__main__":
    main()

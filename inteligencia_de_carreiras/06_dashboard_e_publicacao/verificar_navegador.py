"""Browser smoke tests and screenshots against an already-running local dashboard."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg

AREA = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8502")
    parser.add_argument("--browser-executable")
    args = parser.parse_args()
    out = AREA / "evidencias"
    out.mkdir(exist_ok=True)
    (out / "verificacao_browser.json").write_text(json.dumps({"status": "EM_TESTE", "inicio": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    errors = []
    checks = []
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
        with page.expect_websocket() as opened:
            page.goto(args.url, wait_until="domcontentloaded")
        connection = opened.value
        expect(page.get_by_text("Emprego formal em TI", exact=True)).to_be_visible(timeout=40000)
        expect(page.get_by_role("heading", name="Radar de carreiras", exact=True)).to_be_visible()
        assert page.get_by_role("heading", name="Radar de carreiras", exact=True).bounding_box()["y"] >= 0
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("R$ 3.165")
        settled()
        page.locator('svg.marks').first.wait_for(state="visible", timeout=30000)
        print("[browser] Emprego carregado", flush=True)
        page.screenshot(path=str(out / "01_emprego_desktop.png"), full_page=True)
        checks.append("default_pernambuco")
        page.get_by_text("Filtros do recorte", exact=True).click()
        page.wait_for_function("document.querySelector('[data-testid=stExpander]').getBoundingClientRect().height > 200")
        page.get_by_role("combobox").nth(0).fill("Brasil")
        perform(lambda: page.get_by_role("option", name="Brasil", exact=True).click())
        expect(page.locator('[data-testid="stMetricValue"]').nth(1)).to_have_text("61.047")
        settled()
        checks.append("filtro_regiao_atualiza_numeros")
        with page.expect_download() as download:
            page.get_by_role("button", name="Baixar recorte agregado", exact=True).click()
        assert download.value.suggested_filename == "emprego_recorte.csv"
        checks.append("download_agregado")
        perform(lambda: page.get_by_text("Perfis em dados", exact=True).click())
        expect(page.get_by_text("Perfis na área de dados", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("5.076")
        settled()
        page.screenshot(path=str(out / "02_perfis_desktop.png"), full_page=True)
        checks.append("perfis_fonte_separada")
        print("[browser] Filtros, download e perfis conferidos", flush=True)
        perform(lambda: page.get_by_text("Modelos", exact=True).click())
        expect(page.get_by_text("Avaliação dos modelos", exact=True)).to_be_visible()
        settled()
        page.locator('img').first.wait_for(state="visible")
        page.wait_for_function("document.images.length >= 2 && Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)", timeout=30000)
        images_ok = page.locator('img').evaluate_all("imgs => imgs.every(img => img.complete && img.naturalWidth > 0)")
        assert images_ok, "Broken regression images"
        checks.append("assets_regressao_carregados")
        perform(lambda: page.get_by_text("Busca ativa", exact=True).click())
        expect(page.get_by_text("Matriz de confusão", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stMetricValue"]').nth(2)).to_have_text("12,9%")
        settled()
        page.screenshot(path=str(out / "03_classificacao_desktop.png"), full_page=True)
        checks.append("classificacao_e_limites_visiveis")
        perform(lambda: page.get_by_text("Fontes", exact=True).click())
        expect(page.get_by_text("Fontes e limites", exact=True)).to_be_visible()
        settled()
        checks.append("fontes_e_privacidade")
        print("[browser] Modelos e fontes conferidos", flush=True)
        page.set_viewport_size({"width": 390, "height": 844})
        perform(lambda: page.get_by_role("radio", name="Emprego formal", exact=True).click())
        expect(page.get_by_text("Emprego formal em TI", exact=True)).to_be_visible()
        settled()
        if not page.locator('[data-testid="stExpander"] details').first.evaluate("node=>node.open"):
            page.get_by_text("Filtros do recorte", exact=True).click()
        perform(lambda: page.get_by_role("button", name="Restaurar filtros", exact=True).click())
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text("R$ 3.165")
        settled()
        page.get_by_text("Filtros do recorte", exact=True).click()
        page.wait_for_function("document.querySelector('[data-testid=stExpander]').getBoundingClientRect().height < 80")
        expect(page.get_by_text("Diferença MOV", exact=True)).to_be_in_viewport()
        page.screenshot(path=str(out / "04_emprego_mobile.png"), full_page=True)
        dimensions = page.evaluate("({width: innerWidth, scroll: document.documentElement.scrollWidth})")
        assert dimensions["scroll"] <= dimensions["width"]+1, dimensions
        checks.append("mobile_sem_overflow_horizontal")
        rendered = page.locator("svg.marks").evaluate_all("nodes => nodes.map(svg => {const r=svg.getBoundingClientRect();return r.width>100&&r.height>100&&svg.querySelectorAll('path,line,rect,circle').length>8;})")
        assert rendered and all(rendered), "Blank charts"
        checks.append("graficos_nao_vazios")
        assert page.locator('[data-testid="stException"]').count() == 0
        assert not errors, errors
        browser.close()
    report = {"status": "APROVADO", "executado_em": datetime.now(timezone.utc).isoformat(), "url": args.url,
              "checks": checks, "erros_javascript": errors, "desktop": [1440, 1000], "mobile": [390, 844],
              "codigo_sha256": {name: hashlib.sha256((AREA / name).read_bytes()).hexdigest() for name in ["dashboard.py", "dados.py"]},
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "screenshots": [p.name for p in sorted(out.glob("*.png"))]}
    (out / "verificacao_browser.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

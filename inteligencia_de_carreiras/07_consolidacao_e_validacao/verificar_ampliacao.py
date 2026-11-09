"""Browser validation for the expanded Streamlit dashboard."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def navigate(page, index, heading):
    page.locator(f".st-key-navtab_{index} button").click()
    expect(page.locator(".pintro h2")).to_contain_text(heading)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)


def choose(page, key, label):
    page.locator(f".st-key-{key} input").click()
    page.get_by_role("option", name=label, exact=True).click()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8502/")
    parser.add_argument("--evidencias", type=Path)
    parser.add_argument("--channel", help="Optional installed browser, e.g. msedge.")
    args = parser.parse_args()
    if args.evidencias:
        args.evidencias.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel)
        page = browser.new_page(viewport={"width": 1440, "height": 1040}, accept_downloads=True)
        page.goto(args.url, wait_until="domcontentloaded")
        expect(page.locator(".pintro h2")).to_contain_text("Quanto pagam")
        choose(page, "c_regiao", "Brasil")
        expect(page.locator(".st-key-c_uf input")).to_be_enabled()
        choose(page, "c_uf", "Todas")
        expect(page.get_by_text("Jan/2025 a Set/2026 · Brasil · TI em geral", exact=True)).to_be_visible()
        old_export = page.locator('div[class*="st-key-export_"]').get_attribute("class")
        old_key = next(name for name in old_export.split() if name.startswith("st-key-export_"))
        choose(page, "c_periodo", "Jan a Set/2026")
        expect(page.get_by_text("182.425", exact=True)).to_be_visible()
        expect(page.locator(f".{old_key}")).to_have_count(0)
        with page.expect_download() as export:
            page.get_by_role("button", name="Baixar dados desta tela (CSV)").click()
        assert export.value.suggested_filename == "salarios_e_vagas.csv"
        with export.value.path().open(encoding="utf-8-sig", newline="") as stream:
            data = list(csv.DictReader(stream))
        assert len(data) == 1 and "registro_id" not in data[0]
        assert (data[0]["geo"], data[0]["periodo"], data[0]["admissoes"]) == ("BR", "2026YTD", "182425"), data
        if args.evidencias:
            page.locator(".st-key-filtros").scroll_into_view_if_needed()
            page.screenshot(path=str(args.evidencias / "01_caged_desktop.png"))
        navigate(page, 1, "Como é o perfil")
        expect(page.get_by_text("3.372", exact=True)).to_be_visible()
        choose(page, "p_edicao", "2024/2025")
        expect(page.get_by_text("5.076", exact=True)).to_be_visible()
        navigate(page, 2, "O que dá para estimar")
        expect(page.get_by_text("Treino: 2025 inteiro", exact=False)).to_be_visible()
        page.get_by_text("Quem procura emprego", exact=True).click()
        expect(page.get_by_text("Recall de busca ativa", exact=True)).to_be_visible()
        page.get_by_text("Ver métricas e diagnóstico da classificação", exact=True).click()
        expect(page.get_by_text("Matriz de confusão do modelo selecionado", exact=True)).to_be_visible()
        navigate(page, 3, "O que a turma")
        expect(page.get_by_text("35 respostas", exact=True)).to_be_visible()
        navigate(page, 4, "De onde vêm os números")
        expect(page.get_by_text("842.731 movimentações", exact=False)).to_be_visible()
        navigate(page, 0, "Quanto pagam")
        expect(page.get_by_text("182.425", exact=True)).to_be_visible()
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        mobile.goto(args.url, wait_until="domcontentloaded")
        navigate(mobile, 1, "Como é o perfil")
        expect(mobile.get_by_text("3.372", exact=True)).to_be_visible()
        if args.evidencias:
            mobile.locator(".st-key-p_edicao").scroll_into_view_if_needed()
            mobile.screenshot(path=str(args.evidencias / "02_perfis_mobile.png"))
        browser.close()
    print("Desktop e mobile: abas, filtros, persistencia, CSV e diagnosticos verificados.")


if __name__ == "__main__":
    main()

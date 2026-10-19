"""Validate documentation integrity, coverage, links and optional visual-review evidence."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from gerar_documentacao import AREA, OUT, collect, read_json, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--renders", type=Path)
    parser.add_argument("--revisao-visual-confirmada", action="store_true")
    args = parser.parse_args()
    output = OUT / "registro_execucao.json"
    result = {"status": "EM_VALIDACAO", "inicio": datetime.now(timezone.utc).isoformat()}
    output.write_text(json.dumps(result), encoding="utf-8")
    checks = []

    def check(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)

    try:
        collect()
        checks.append("Evidencias da etapa 07 e pacote publico permanecem integros")
        manifest = read_json(OUT / "manifesto_documentacao.json")
        for key, root in [("fontes_sha256", AREA), ("codigo_sha256", OUT), ("produtos_sha256", OUT)]:
            check("Hashes: " + key, all(sha(root / name) == expected for name, expected in manifest[key].items()))
        reader = PdfReader(OUT / "documentacao_final.pdf")
        pages = [page.extract_text() or "" for page in reader.pages]
        check("Um capitulo por pagina sem paginas extras", len(pages) == len(manifest["capitulos"]))
        check("Todas as paginas contem texto", all(len(text.strip()) > 120 for text in pages))
        for index, title in enumerate(manifest["capitulos"]):
            check(f"Titulo da pagina {index + 1}", title in pages[index])
        full = "\n".join(pages)
        check("Caracteres sem glifos de substituicao", "\ufffd" not in full and "\u25a0" not in full)
        check("Numeros de validacao registrados no PDF", all(v in full for v in ["111", "22", "65.761", "4.408", "675"]))
        check("Feedback e publicacao explicitamente pendentes", "revisão estruturada" in full.lower() and "não houve teste formal" in full.lower() and "não foi realizada" in full.lower())
        check("Quatro capturas incorporadas ao PDF", sum(len(page.images) for page in reader.pages) == 4)
        local_links = [link for link in manifest["links"] if not link.startswith("https://")]
        for link in local_links:
            path = (OUT / link).resolve()
            check("Link local existente: " + link, path.is_relative_to(AREA) and path.is_file())
            check("Link sem dados individuais: " + link, not any(part in path.parts for part in ["brutos", "tratados", "resultados_locais"]))
        with (AREA / "00_referencias/matriz_criterios.csv").open(encoding="utf-8-sig", newline="") as stream:
            criteria = {r["id"]: r for r in csv.DictReader(stream)}
        check("Dez criterios de CC preservados", set(criteria) == {f"CC{i:02d}" for i in range(1, 11)})
        check("CC10 documentado como concluido", criteria["CC10"]["situacao"].startswith("Concluida"))
        check("Pendencias reais de CC08 e CC09 preservadas", "pendente" in criteria["CC08"]["situacao"].lower() and "pendentes" in criteria["CC09"]["situacao"].lower())
        check("Nenhum commit ou deploy atribuido a esta geracao", manifest["publicacao_externa"] is False and manifest["commit_push_realizado"] is False)
        renders = {}
        if args.revisao_visual_confirmada:
            check("Pasta de renders informada", args.renders is not None)
            images = sorted(args.renders.glob("pagina-*.png"))
            check("Uma imagem renderizada por pagina", len(images) == len(pages))
            for image in images:
                with Image.open(image) as asset:
                    check("Render legivel: " + image.name, asset.width >= 850 and asset.height >= 1100 and asset.convert("L").getextrema()[0] < 100)
                renders[image.name] = sha(image)
        result.update({"status": "DOCUMENTACAO_FINAL_VALIDADA" if args.revisao_visual_confirmada else "VALIDADA_AGUARDANDO_REVISAO_VISUAL",
                       "executado_em": datetime.now(timezone.utc).isoformat(), "paginas_pdf": len(pages),
                       "total_verificacoes_documentais": len(checks), "verificacoes": checks,
                       "manifesto_sha256": sha(OUT / "manifesto_documentacao.json"),
                       "produtos_sha256": manifest["produtos_sha256"],
                       "revisao_visual": {"confirmada": args.revisao_visual_confirmada, "renderizador": "Poppler", "renders_sha256": renders},
                       "validacao_aplicacao_referenciada": manifest["validacao_aplicacao_referenciada"],
                       "testes_aplicacao_reexecutados_nesta_etapa": False,
                       "pendencias_atuais": manifest["pendencias_atuais"], "commit_push_realizado": False, "publicacao_externa": False})
    except Exception as error:
        result.update({"status": "FALHOU", "erro": str(error), "verificacoes_aprovadas": checks})
        raise
    finally:
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["status", "paginas_pdf", "total_verificacoes_documentais"]}), flush=True)


if __name__ == "__main__":
    main()

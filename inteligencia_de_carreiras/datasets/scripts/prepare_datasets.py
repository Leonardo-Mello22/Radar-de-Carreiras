"""Prepare independent, traceable datasets for Radar de Carreiras."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import py7zr

MONTHS = ["202501", "202502", "202503"]
REF = "202503"
FAMILIES = ["1236", "1425", "2122", "2123", "2124", "3171", "3172"]
AREA = {
    "123605": "Gestao de TI", "142505": "Redes e infraestrutura",
    "142510": "Desenvolvimento de software", "142515": "Gestao de TI",
    "142520": "Gestao de TI", "142525": "Seguranca da informacao",
    "142530": "Suporte e operacoes", "142535": "Gestao de TI",
    "212205": "Desenvolvimento de software", "212210": "Hardware e sistemas",
    "212215": "Hardware e sistemas", "212305": "Dados e bancos de dados",
    "212310": "Redes e infraestrutura", "212315": "Redes e infraestrutura",
    "212320": "Seguranca da informacao", "212405": "Desenvolvimento de software",
    "212410": "Redes e infraestrutura", "212415": "Automacao industrial",
    "212420": "Suporte e operacoes", "212425": "Arquitetura de solucoes",
    "212430": "Qualidade e testes", "317105": "Desenvolvimento de software",
    "317110": "Desenvolvimento de software", "317115": "Automacao industrial",
    "317120": "Desenvolvimento de software", "317205": "Suporte e operacoes",
    "317210": "Suporte e operacoes",
}
EDUCATION = {
    "1": "Sem instrucao", "2": "Fundamental incompleto", "3": "Fundamental incompleto",
    "4": "Fundamental incompleto", "5": "Fundamental completo",
    "6": "Medio incompleto", "7": "Medio completo", "8": "Superior incompleto",
    "9": "Superior completo", "80": "Pos-graduacao", "10": "Mestrado",
    "11": "Doutorado", "99": "Nao informado",
}
UF_SIGLA = dict(zip(
    ["11", "12", "13", "14", "15", "16", "17", "21", "22", "23", "24", "25", "26", "27", "28", "29", "31", "32", "33", "35", "41", "42", "43", "50", "51", "52", "53"],
    ["RO", "AC", "AM", "RR", "PA", "AP", "TO", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA", "MG", "ES", "RJ", "SP", "PR", "SC", "RS", "MS", "MT", "GO", "DF"],
))
NE = {"MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}


def slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.normalize("NFC").str.replace(r"\s+", " ", regex=True).str.strip().replace("", pd.NA)


def nullable_boolean(series: pd.Series) -> pd.Series:
    values = clean_text(series).str.casefold()
    mapping = {"true": True, "false": False, "1": True, "0": False,
               "sim": True, "nao": False, "não": False}
    unknown = values.notna() & ~values.isin(mapping)
    if unknown.any():
        raise ValueError("Unexpected boolean domain; review the source instead of guessing.")
    return values.map(mapping).astype("boolean")


def cache_fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in [Path(__file__), *paths]:
        digest.update(path.name.encode("utf-8"))
        with path.open("rb") as stream:
            digest.update(hashlib.file_digest(stream, "sha256").digest())
    return digest.hexdigest()[:20]


def read_json(path: Path):
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def br_number(series: pd.Series) -> pd.Series:
    text = clean_text(series)
    comma = text.str.contains(",", na=False)
    text.loc[comma] = text.loc[comma].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(text, errors="coerce").astype("Float64")


def age_band(age: pd.Series) -> pd.Series:
    valid = age.between(14, 90)
    return pd.cut(age.where(valid).astype(float), [13, 17, 24, 34, 44, 54, 64, 90], labels=[
        "14-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65-90"
    ]).astype("string").fillna("Nao informado ou invalido")


def region_scope(uf: pd.Series) -> pd.Series:
    result = pd.Series("Demais UFs", index=uf.index, dtype="string")
    result.loc[uf.isna()] = "Nao informado"
    result.loc[uf.isin(NE)] = "Nordeste exceto PE"
    result.loc[uf.eq("PE").fillna(False)] = "Pernambuco"
    return result


def export_frame(frame: pd.DataFrame, directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(directory / f"{name}.parquet", index=False)
    frame.to_csv(directory / f"{name}.csv", index=False, encoding="utf-8-sig", na_rep="")
    print(f"[export] {name}: {len(frame):,} registros, {frame.shape[1]} colunas", flush=True)


def load_domains(raw: Path) -> dict[str, dict[str, str]]:
    book = pd.ExcelFile(raw / "layout_novo_caged.xlsx")
    domains = {}
    for sheet in book.sheet_names:
        if sheet == "Layout":
            continue
        table = pd.read_excel(book, sheet_name=sheet, dtype=str).iloc[:, :2].dropna()
        codes = table.iloc[:, 0].str.strip().str.replace(r"\.0$", "", regex=True)
        domains[slug(sheet)] = dict(zip(codes, clean_text(table.iloc[:, 1])))
    return domains


def municipality_table(raw: Path) -> pd.DataFrame:
    rows = []
    for item in read_json(raw / "municipios_ibge.json"):
        territorial = item.get("regiao-imediata")
        uf = territorial["regiao-intermediaria"]["UF"] if territorial else item["microrregiao"]["mesorregiao"]["UF"]
        rows.append({"municipio_ibge7": str(item["id"]), "municipio_codigo": str(item["id"])[:6],
                     "municipio_nome": item["nome"], "uf_sigla": uf["sigla"], "regiao_nome": uf["regiao"]["nome"]})
    table = pd.DataFrame(rows)
    if table["municipio_codigo"].duplicated().any():
        raise ValueError("IBGE municipality lookup is not unique")
    return table


def enrich_caged(frame: pd.DataFrame, month: str, offset: int, domains, municipalities, factors) -> pd.DataFrame:
    frame.columns = [slug(c) for c in frame.columns]
    codes = clean_text(frame["cbo2002ocupacao"]).str.zfill(6)
    selection = codes.str[:4].isin(FAMILIES)
    b = frame.loc[selection].copy()
    o = pd.DataFrame(index=b.index)
    o["registro_id"] = [f"CAGEDMOV{month}:{offset + int(i) + 2}" for i in b.index]
    o["competencia"] = clean_text(b["competenciamov"])
    o["ano"] = o["competencia"].str[:4].astype("Int64")
    o["mes"] = o["competencia"].str[4:].astype("Int64")
    o["trimestre"] = ((o["mes"] - 1) // 3 + 1).astype("Int64")
    o["data_competencia"] = pd.to_datetime(o["competencia"], format="%Y%m", errors="coerce")
    o["uf_codigo"] = clean_text(b["uf"])
    o["uf_sigla"] = o["uf_codigo"].map(UF_SIGLA).astype("string")
    o["uf_nome"] = o["uf_codigo"].map(domains["uf"]).astype("string")
    o["regiao_nome"] = clean_text(b["regiao"]).map(domains["regiao"]).astype("string")
    o["municipio_codigo"] = clean_text(b["municipio"]).str.zfill(6)
    lookup = municipalities.set_index("municipio_codigo")
    o["municipio_ibge7"] = o["municipio_codigo"].map(lookup["municipio_ibge7"]).astype("string")
    o["municipio_nome"] = o["municipio_codigo"].map(lookup["municipio_nome"]).astype("string")
    fallback = o["municipio_codigo"].map(domains["municipio"]).str.replace(r"^[A-Za-z]{2}-", "", regex=True)
    o["municipio_nome"] = o["municipio_nome"].fillna(fallback)
    o["recorte_regional"] = region_scope(o["uf_sigla"])
    o["cbo_codigo"] = clean_text(b["cbo2002ocupacao"]).str.zfill(6)
    o["cbo_familia"] = o["cbo_codigo"].str[:4]
    o["cbo_nome"] = o["cbo_codigo"].map(domains["cbo2002ocupacao"]).astype("string")
    o["area_ti"] = o["cbo_codigo"].map(AREA).astype("string").fillna("TI - a classificar")
    o["funcao_gestao"] = o["cbo_familia"].isin(["1236", "1425"])
    o["saldo"] = pd.to_numeric(b["saldomovimentacao"], errors="coerce").astype("Int64")
    o["movimento"] = o["saldo"].map({1: "admiss\u00e3o", -1: "desligamento"}).astype("string")
    for source, target in {"tipomovimentacao": "tipo_movimentacao", "categoria": "categoria_trabalhador",
                           "graudeinstrucao": "grau_instrucao", "sexo": "sexo", "racacor": "raca_cor",
                           "tamestabjan": "tamanho_estabelecimento", "secao": "setor_cnae",
                           "unidadesalariocodigo": "unidade_salario_fixo"}.items():
        o[f"{target}_cod"] = clean_text(b[source])
        o[target] = o[f"{target}_cod"].map(domains[source]).astype("string")
    o["unidade_salario_cod"] = o["unidade_salario_fixo_cod"]
    o["cnae_subclasse_codigo"] = clean_text(b["subclasse"]).str.zfill(7)
    o["escolaridade_grupo"] = o["grau_instrucao_cod"].map(EDUCATION).fillna("Nao informado")
    o["idade"] = pd.to_numeric(b["idade"], errors="coerce").astype("Int64")
    o["idade_valida"] = o["idade"].between(14, 90).fillna(False)
    o["faixa_etaria"] = age_band(o["idade"])
    o["horas_contratuais"] = br_number(b["horascontratuais"])
    o["horas_validas"] = o["horas_contratuais"].between(1, 48).fillna(False)
    o["jornada_grupo"] = pd.cut(o["horas_contratuais"].where(o["horas_validas"]).astype(float),
        [0, 20, 30, 40, 44, 48], labels=["Ate 20h", "21-30h", "31-40h", "41-44h", "45-48h"]).astype("string").fillna("Nao informado ou invalido")
    o["primeiro_emprego_formal"] = o["tipo_movimentacao_cod"].eq("10").fillna(False)
    o["indicador_aprendiz"] = clean_text(b["indicadoraprendiz"]).map({"1": True, "0": False}).astype("boolean")
    o["trabalho_intermitente"] = clean_text(b["indtrabintermitente"]).map({"1": True, "0": False}).astype("boolean")
    o["trabalho_parcial"] = clean_text(b["indtrabparcial"]).map({"1": True, "0": False}).astype("boolean")
    o["salario_nominal"] = br_number(b["salario"])
    o["salario_fixo_declarado"] = br_number(b["valorsalariofixo"])
    o["salario_real"] = o["salario_nominal"] * o["competencia"].map(factors).astype("Float64")
    o["salario_valido"] = o["salario_nominal"].between(300, 200000).fillna(False)
    o["salario_status"] = "Plausivel"
    o.loc[~o["salario_valido"], "salario_status"] = "Fora do intervalo 300-200000"
    o.loc[o["salario_nominal"].isna(), "salario_status"] = "Ausente ou invalido"
    o["faixa_salario_real"] = pd.cut(o["salario_real"].where(o["salario_valido"]).astype(float),
        [0, 2000, 4000, 6000, 10000, 15000, np.inf],
        labels=["Ate 2000", "2000-4000", "4000-6000", "6000-10000", "10000-15000", "Acima de 15000"],
        right=False).astype("string").fillna("Nao calculado")
    o["mes_referencia_ipca"] = REF
    o["competencia_declaracao"] = clean_text(b["competenciadec"])
    o["declaracao_fora_prazo"] = clean_text(b["indicadordeforadoprazo"]).map({"1": True, "0": False}).astype("boolean")
    o["origem_informacao_cod"] = clean_text(b["origemdainformacao"])
    o["fonte"] = "Novo CAGED (PDET/Ministerio do Trabalho) - microdados de movimentacoes"
    o["arquivo_origem"] = f"CAGEDMOV{month}.7z"
    return o.reset_index(drop=True)


def prepare_caged(root: Path, temporary: Path, reports: dict) -> pd.DataFrame:
    raw, processed = root / "brutos", root / "tratados"
    auxiliary = root / "auxiliares"
    domains = load_domains(raw)
    municipalities = municipality_table(raw)
    export_frame(municipalities, auxiliary, "municipios_ibge")
    ipca_rows = read_json(raw / "ipca_2025_01_03.json")[1:]
    ipca = pd.DataFrame({"competencia": [r["D3C"] for r in ipca_rows], "indice_ipca": [float(r["V"]) for r in ipca_rows]})
    reference = ipca.loc[ipca.competencia.eq(REF), "indice_ipca"].item()
    ipca["fator_marco_2025"] = reference / ipca["indice_ipca"]
    export_frame(ipca, auxiliary, "ipca_deflatores")
    factors = dict(zip(ipca["competencia"], ipca["fator_marco_2025"]))
    occupation = pd.DataFrame(domains["cbo2002ocupacao"].items(), columns=["cbo_codigo", "cbo_nome"])
    occupation = occupation[occupation.cbo_codigo.str[:4].isin(FAMILIES)].copy()
    occupation["area_ti"] = occupation.cbo_codigo.map(AREA)
    occupation["familia"] = occupation.cbo_codigo.str[:4]
    export_frame(occupation, auxiliary, "cbo_ti_categorias")
    monthly, controls = [], []
    temporary.mkdir(parents=True, exist_ok=True)
    for month in MONTHS:
        key = cache_fingerprint([raw / f"CAGEDMOV{month}.7z", raw / "layout_novo_caged.xlsx",
                                 raw / "municipios_ibge.json", raw / "ipca_2025_01_03.json"])
        stage = temporary / f"{month}_{key}"
        stage.mkdir(exist_ok=True)
        cache, control_path = stage / "ti.parquet", stage / "controle.json"
        if cache.exists() and control_path.exists():
            part = pd.read_parquet(cache)
            control = read_json(control_path)
        else:
            with py7zr.SevenZipFile(raw / f"CAGEDMOV{month}.7z", "r") as archive:
                names = archive.getnames()
                selected = [n for n in names if n.lower().endswith(".txt")]
                if len(selected) != 1:
                    raise ValueError(f"Unexpected archive members: {names}")
                if Path(selected[0]).name != selected[0] or ":" in selected[0] or "\\" in selected[0]:
                    raise ValueError("Unexpected archive path")
                txt = stage / selected[0]
                if not txt.exists():
                    print(f"[extract] {month}", flush=True)
                    archive.extract(path=stage, targets=selected)
            pieces, total = [], 0
            for chunk in pd.read_csv(txt, sep=";", dtype=str, encoding="utf-8-sig", chunksize=200000, keep_default_na=False):
                # Chunk indices already carry the absolute source row offset.
                chunk = chunk.reset_index(drop=True)
                pieces.append(enrich_caged(chunk, month, total, domains, municipalities, factors))
                total += len(chunk)
                if total % 1000000 == 0:
                    print(f"[filter] {month}: {total:,} linhas verificadas", flush=True)
            part = pd.concat(pieces, ignore_index=True)
            part.to_parquet(cache, index=False)
            control = {"competencia": month, "linhas_brutas": total, "movimentacoes_ti": len(part),
                       "admissoes_ti": int(part.saldo.eq(1).sum()), "desligamentos_ti": int(part.saldo.eq(-1).sum())}
            control_path.write_text(json.dumps(control), encoding="utf-8")
        monthly.append(part)
        controls.append(control)
        print(f"[caged] {month}: {len(part):,} movimentacoes TI", flush=True)
    result = pd.concat(monthly, ignore_index=True)
    export_frame(result, processed, "caged_ti")
    export_frame(result[result.uf_sigla.isin(NE)], processed, "caged_ti_nordeste")
    export_frame(result[result.uf_sigla.eq("PE")], processed, "caged_ti_pernambuco")
    export_frame(pd.DataFrame(controls), root / "qualidade", "controle_caged_mensal")
    salary = result["salario_real"].where(result["salario_valido"]).astype(float)
    scaled = result[["registro_id", "competencia", "idade", "horas_contratuais"]].copy()
    scaled["salario_real"] = salary
    scaled.loc[~result.idade_valida, "idade"] = pd.NA
    scaled.loc[~result.horas_validas, "horas_contratuais"] = pd.NA
    parameters = {}
    for col in ("salario_real", "idade", "horas_contratuais"):
        mean, std = scaled[col].mean(), scaled[col].std(ddof=0)
        low, high = scaled[col].min(), scaled[col].max()
        parameters[col] = {"media": float(mean), "desvio_populacional": float(std), "minimo": float(low), "maximo": float(high)}
        scaled[f"{col}_zscore"] = (scaled[col] - mean) / std if std else scaled[col] * 0
        scaled[f"{col}_minmax"] = (scaled[col] - low) / (high - low) if high > low else scaled[col] * 0
    scaled["salario_log1p"] = np.log1p(salary)
    export_frame(scaled, root / "modelagem", "caged_features_numericas")
    (root / "modelagem" / "parametros_normalizacao.json").write_text(json.dumps({
        "uso": "Exploracao. Para avaliar modelos preditivos, refazer o ajuste somente no treino.",
        "base": "CAGED TI Brasil 2025-01 a 2025-03", "colunas": parameters}, indent=2), encoding="utf-8")
    grouped = result.groupby(["competencia", "uf_sigla", "uf_nome", "regiao_nome", "area_ti", "movimento"], dropna=False)
    rows = []
    for keys, group in grouped:
        valid = group.loc[group.salario_valido, "salario_real"]
        row = dict(zip(["competencia", "uf_sigla", "uf_nome", "regiao_nome", "area_ti", "movimento"], keys))
        row.update(movimentacoes=len(group), registros_salario_valido=len(valid), amostra_salarial_suficiente=len(valid) >= 30)
        for percentile in (10, 50, 90):
            row[f"salario_real_p{percentile}"] = float(valid.quantile(percentile / 100)) if len(valid) >= 30 else np.nan
        row["mes_referencia_ipca"] = REF
        rows.append(row)
    export_frame(pd.DataFrame(rows), root / "agregados", "caged_indicadores_uf_area_mes")
    (auxiliary / "dominios_caged.json").write_text(json.dumps(domains, ensure_ascii=False, indent=2), encoding="utf-8")
    reports["caged"] = {
        "controles_mensais": controls, "registros_ti": len(result), "colunas": result.shape[1],
        "registros_pe": int(result.uf_sigla.eq("PE").sum()), "registros_nordeste": int(result.uf_sigla.isin(NE).sum()),
        "salarios_sinalizados": int((~result.salario_valido).sum()),
        "municipios_sem_traducao": int(result.municipio_nome.isna().sum()),
        "cbo_sem_traducao": int(result.cbo_nome.isna().sum()),
        "duplicatas_sem_registro_id": int(result.drop(columns="registro_id").duplicated().sum()),
        "nulos_por_coluna": {k: int(v) for k, v in result.isna().sum().items() if v},
    }
    return result


def survey_salary_bounds(value) -> tuple:
    if pd.isna(value):
        return (np.nan, np.nan, pd.NA)
    text = str(value)
    values = [float(n.replace(".", "")) for n in re.findall(r"R\$\s*([\d.]+)", text)]
    if text.startswith("Menos"):
        return (0.0, values[0], True)
    if text.startswith("Acima"):
        return (values[0], np.nan, False)
    if len(values) == 2:
        return (values[0], values[1], False)
    raise ValueError(f"Unmapped salary interval: {value}")


def prepare_survey(root: Path, reports: dict) -> pd.DataFrame:
    with zipfile.ZipFile(root / "brutos" / "state_of_data_2024_2025.zip") as archive:
        csvs = [n for n in archive.namelist() if n.endswith(".csv")]
        original_all = pd.read_csv(archive.open(csvs[0]))
    original = original_all.drop_duplicates().copy()
    prepared_columns = {}
    mapping, normalized_names = [], set()
    for source in original.columns:
        name = "q_" + slug(source)
        if name in normalized_names:
            raise ValueError(f"Duplicated normalized column: {name}")
        normalized_names.add(name)
        s = original[source]
        if pd.api.types.is_bool_dtype(s):
            prepared_columns[name] = s.astype("boolean")
        elif pd.api.types.is_numeric_dtype(s):
            present = s.dropna()
            if len(present) and present.isin([0, 1]).all() and re.match(r"\d+\.[a-z]\.\d+[ _]", source):
                prepared_columns[name] = s.astype("boolean")
            else:
                prepared_columns[name] = s.astype("Int64") if present.mod(1).eq(0).all() else s.astype("Float64")
        else:
            prepared_columns[name] = clean_text(s)
        mapping.append({"coluna_original": source, "coluna_normalizada": name, "tipo": str(prepared_columns[name].dtype)})
    full = pd.DataFrame(prepared_columns)
    full.insert(0, "respondente_id", [f"SOD2024:{i + 2}" for i in original.index])
    full["fonte"] = "State of Data Brazil 2024-2025 (Data Hackers)"
    export_frame(full, root / "tratados", "state_of_data_completo_normalizado")
    export_frame(pd.DataFrame(mapping), root / "auxiliares", "mapa_colunas_state_of_data")
    aliases = {
        "1.a_idade": "idade", "1.b_genero": "genero", "1.c_cor/raca/etnia": "raca_cor",
        "1.g_vive_no_brasil": "vive_no_brasil", "1.h_pais_onde_mora": "pais_residencia",
        "1.i.1_uf_onde_mora": "uf_sigla", "1.i.2_regiao_onde_mora": "regiao_nome",
        "1.l_nivel_de_ensino": "nivel_ensino", "1.m_\u00e1rea_de_forma\u00e7\u00e3o": "area_formacao",
        "2.a_situa\u00e7\u00e3o_de_trabalho": "situacao_trabalho", "2.b_setor": "setor",
        "2.c_numero_de_funcionarios": "tamanho_empresa", "2.d_atua_como_gestor": "atua_como_gestor",
        "2.e_cargo_como_gestor": "cargo_gestao", "2.f_cargo_atual": "cargo_atual",
        "2.g_nivel": "senioridade_declarada", "2.h_faixa_salarial": "faixa_salarial_declarada",
        "2.i_tempo_de_experiencia_em_dados": "experiencia_dados_faixa",
        "2.j_tempo_de_experiencia_em_ti": "experiencia_ti_anterior_faixa",
        "2.k_satisfeito_atualmente": "satisfeito_trabalho",
        "2.m_participou_de_entrevistas_ultimos_6m": "participou_entrevistas_6m",
        "2.n_planos_de_mudar_de_emprego_6m": "planos_mudar_emprego_6m",
        "2.q_empresa_passou_por_layoff_em_2024": "empresa_layoff_2024",
        "2.r_modelo_de_trabalho_atual": "modelo_trabalho_declarado",
        "2.s_modelo_de_trabalho_ideal": "modelo_trabalho_ideal",
        "4.e_linguagem_mais_usada": "linguagem_mais_usada",
        "5.a_objetivo_na_area_de_dados": "objetivo_carreira",
        "5.b_oportunidade_buscada": "oportunidade_buscada",
        "5.c_tempo_em_busca_de_oportunidade": "tempo_busca_oportunidade",
    }
    # Resolve accented source headers by their normalized spelling.
    by_slug = {slug(c): c for c in original.columns}
    result = full[["respondente_id"]].copy()
    for source, target in aliases.items():
        actual = by_slug.get(slug(source))
        if actual is None:
            raise ValueError(f"Missing source field: {source}")
        result[target] = full["q_" + slug(actual)]
    result["atua_como_gestor"] = nullable_boolean(result["atua_como_gestor"])
    result["uf_sigla"] = result.uf_sigla.str.upper()
    result["regiao_nome"] = result.regiao_nome.replace({"Centro-oeste": "Centro-Oeste"})
    result.loc[result.vive_no_brasil.eq(True).fillna(False) & result.pais_residencia.isna(), "pais_residencia"] = "Brasil"
    result.loc[result.vive_no_brasil.eq(False).fillna(False), "regiao_nome"] = "Exterior"
    result["recorte_regional"] = region_scope(result.uf_sigla)
    result.loc[result.vive_no_brasil.eq(False).fillna(False), "recorte_regional"] = "Exterior"
    result["faixa_etaria"] = age_band(result.idade)
    result["idade_valida"] = result.idade.between(14, 90).fillna(False)
    result["senioridade_declarada"] = result.senioridade_declarada.map({"J\u00fanior": "Junior", "Pleno": "Pleno", "S\u00eanior": "Senior"}).astype("string")
    result["escolaridade_grupo"] = result.nivel_ensino.map(slug).map({
        "pos_graduacao": "Pos-graduacao", "graduacao_bacharelado": "Superior completo",
        "mestrado": "Mestrado", "estudante_de_graduacao": "Superior em andamento",
        "doutorado_ou_phd": "Doutorado", "nao_tenho_graduacao_formal": "Sem graduacao formal",
        "prefiro_nao_informar": "Nao informado",
    }).astype("string").fillna("Nao informado")
    result["area_profissional"] = result.cargo_atual.map(slug).map({
        "analista_de_dados_data_analyst": "Dados e BI", "analista_de_bi_bi_analyst": "Dados e BI",
        "analista_de_negocios_business_analyst": "Analise de negocios",
        "cientista_de_dados_data_scientist": "Ciencia de dados e IA",
        "engenheiro_de_machine_learning_ml_engineer_ai_engineer": "Ciencia de dados e IA",
        "engenheiro_de_dados_data_engineer_data_architect": "Engenharia e arquitetura de dados",
        "arquiteto_de_dados_data_architect": "Engenharia e arquitetura de dados",
        "analytics_engineer": "Engenharia e arquitetura de dados",
        "desenvolvedor_engenheiro_de_software_analista_de_sistemas": "Desenvolvimento de software",
        "data_product_manager_product_manager_pm_apm_dpm_gpm_po": "Produto de dados",
        "analista_de_suporte_analista_tecnico": "Suporte e operacoes",
        "professor_pesquisador": "Academico ou pesquisador", "estatistico": "Estatistica",
    }).astype("string")
    result.loc[result.cargo_atual.isna() & result.atua_como_gestor.eq(True).fillna(False), "area_profissional"] = "Gestao"
    result["area_profissional"] = result.area_profissional.fillna("Outra area ou nao informado")
    employment = result.situacao_trabalho.map(slug)
    result["vinculo_grupo"] = employment.map({
        "empregado_clt": "CLT", "empreendedor_ou_empregado_cnpj": "PJ ou empreendedor",
        "estagiario": "Estagio", "servidor_publico": "Servidor publico", "freelancer": "Freelancer",
        "somente_estudante_graduacao": "Estudante", "somente_estudante_pos_graduacao": "Estudante",
        "desempregado_buscando_recolocacao": "Desempregado", "desempregado_e_nao_estou_buscando_recolocacao": "Desempregado",
        "trabalho_na_area_academica_pesquisador": "Academico ou pesquisador",
        "vivo_no_brasil_e_trabalho_remoto_para_empresa_de_fora_do_brasil": "Trabalho internacional",
        "vivo_fora_do_brasil_e_trabalho_para_empresa_de_fora_do_brasil": "Trabalho internacional",
        "prefiro_nao_informar": "Nao informado",
    }).astype("string").fillna("Outro ou nao informado")
    model = result.modelo_trabalho_declarado.fillna("").map(slug)
    result["modelo_trabalho"] = model.map({"modelo_100_remoto": "Remoto", "modelo_100_presencial": "Presencial"}).astype("string")
    result.loc[model.str.contains("hibrido"), "modelo_trabalho"] = "Hibrido"
    result["modelo_trabalho"] = result.modelo_trabalho.fillna("Nao informado")
    result["inicio_carreira_dados_ate_2_anos"] = result.experiencia_dados_faixa.map({
        "Menos de 1 ano": True, "de 1 a 2 anos": True,
        "N\u00e3o tenho experi\u00eancia na \u00e1rea de dados": True,
        "de 3 a 4 anos": False, "de 5 a 6 anos": False, "de 7 a 10 anos": False, "Mais de 10 anos": False,
    }).astype("boolean")
    bounds = pd.DataFrame(result.faixa_salarial_declarada.map(survey_salary_bounds).tolist(),
        columns=["faixa_salario_limite_inferior", "faixa_salario_limite_superior", "faixa_limite_superior_exclusivo"], index=result.index)
    result = pd.concat([result, bounds], axis=1)
    result["faixa_limite_superior_exclusivo"] = result.faixa_limite_superior_exclusivo.astype("boolean")
    result["faixa_limite_inferior_exclusivo"] = result.faixa_salarial_declarada.str.startswith("Acima").astype("boolean")
    result["remuneracao_medida"] = "Faixa autodeclarada mensal em BRL - nao e salario exato"
    for prefix, target in {"4.d.1_": "usa_sql", "4.d.3_": "usa_python", "4.d.2_": "usa_r",
                           "4.j.1_": "usa_power_bi", "4.h.1_": "usa_aws", "4.h.2_": "usa_gcp",
                           "4.h.3_": "usa_azure"}.items():
        source = next(c for c in original.columns if c.startswith(prefix))
        result[target] = full["q_" + slug(source)].astype("boolean")
    result["fonte"] = full.fonte
    export_frame(result, root / "tratados", "state_of_data_carreiras")
    export_frame(result[result.vive_no_brasil.eq(True).fillna(False)], root / "tratados", "state_of_data_brasil")
    export_frame(result[result.uf_sigla.eq("PE")], root / "tratados", "state_of_data_pernambuco")
    export_frame(result[result.uf_sigla.isin(NE)], root / "tratados", "state_of_data_nordeste")
    tech_rows = []
    for source in original.columns:
        match = re.match(r"4\.([dghj])\.\d+_(.+)", source)
        if not match:
            continue
        group = {"d": "Linguagem", "g": "Banco de dados", "h": "Cloud", "j": "BI"}[match[1]]
        for respondent in full.loc[full["q_" + slug(source)].eq(True).fillna(False), "respondente_id"]:
            tech_rows.append({"respondente_id": respondent, "grupo": group, "tecnologia_ou_opcao": match[2], "coluna_origem": source})
    export_frame(pd.DataFrame(tech_rows), root / "tratados", "state_of_data_tecnologias")
    reports["state_of_data"] = {"respostas_originais": len(original_all), "respondentes": len(result), "colunas_originais": original.shape[1],
        "colunas_carreiras": result.shape[1], "respondentes_pe": int(result.uf_sigla.eq("PE").sum()),
        "respondentes_nordeste": int(result.uf_sigla.isin(NE).sum()),
        "senioridade_nao_informada": int(result.senioridade_declarada.isna().sum()),
        "duplicatas_exatas_removidas": int(original_all.duplicated().sum()),
        "gestores_declarados": int(result.atua_como_gestor.eq(True).sum()),
        "area_gestao": int(result.area_profissional.eq("Gestao").sum()),
        "nulos_por_coluna": {k: int(v) for k, v in result.isna().sum().items() if v}}
    return result


def dictionary(frame: pd.DataFrame, descriptions: dict[str, str], dataset: str) -> pd.DataFrame:
    rows = []
    for name in frame.columns:
        s = frame[name]
        examples = " | ".join(str(v) for v in s.dropna().unique()[:4])
        rows.append({"dataset": dataset, "coluna": name, "tipo": str(s.dtype),
                     "descricao": descriptions.get(name, name.replace("_", " ")),
                     "nulos": int(s.isna().sum()), "exemplos": examples})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--temporary", type=Path, required=True)
    args = parser.parse_args()
    reports = {}
    survey = prepare_survey(args.output, reports)
    caged = prepare_caged(args.output, args.temporary, reports)
    descriptions = {
        "registro_id": "Arquivo e numero da linha de origem. Nao identifica pessoa ou vinculo.",
        "salario_nominal": "Salario mensal declarado (BRL), conforme layout oficial.",
        "salario_real": "Salario mensal em BRL a precos de marco/2025: nominal * IPCA_ref / IPCA_mes.",
        "area_ti": "Agrupamento analitico por CBO exata, documentado em cbo_ti_categorias.csv.",
        "primeiro_emprego_formal": "Tipo de movimentacao 10: admissao por primeiro emprego. Nao equivale a Junior.",
        "salario_valido": "Salario nominal entre 300 e 200000, limites inclusivos; regra do projeto.",
        "faixa_salario_real": "Intervalos [0,2000), [2000,4000), [4000,6000), [6000,10000), [10000,15000), [15000,+infinito).",
        "senioridade_declarada": "Junior, Pleno ou Senior declarado pelo respondente. Nulo nao equivale a Junior.",
        "inicio_carreira_dados_ate_2_anos": "Sem experiencia, menos de 1 ano ou 1-2 anos na area de dados. Nao e carreira total.",
        "faixa_salario_limite_superior": "Limite superior da faixa autodeclarada. Nulo para faixa aberta acima de 40001.",
        "experiencia_ti_anterior_faixa": "Experiencia em TI antes de trabalhar com dados; nao representa experiencia total atual em TI.",
        "unidade_salario_fixo": "Unidade de pagamento da parte fixa. Nao altera salario_nominal, que ja e mensal.",
        "atua_como_gestor": "Booleano declarado pelo participante, com ausentes preservados; nao e inferido pelo salario.",
        "area_profissional": "Agrupamento analitico de cargo; Gestao para gestor declarado sem cargo tecnico respondido.",
    }
    export_frame(pd.concat([dictionary(caged, descriptions, "caged_ti"), dictionary(survey, descriptions, "state_of_data_carreiras")]),
                 args.output / "auxiliares", "dicionario_dados")
    quality = args.output / "qualidade"
    quality.mkdir(exist_ok=True)
    (quality / "relatorio_qualidade.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    assert caged.registro_id.is_unique
    assert set(caged.competencia) == set(MONTHS)
    assert caged.cbo_nome.notna().all()
    assert set(caged.saldo) == {-1, 1}
    assert np.isclose(caged.salario_real[caged.competencia.eq(REF)].astype(float),
                      caged.salario_nominal[caged.competencia.eq(REF)].astype(float), equal_nan=True).all()
    assert len(survey) == 5215
    assert survey.respondente_id.is_unique
    assert not (survey.faixa_salario_limite_superior < survey.faixa_salario_limite_inferior).any()
    print(json.dumps(reports, ensure_ascii=True, indent=2), flush=True)
    print("[done] Data prepared and basic invariants verified.", flush=True)


if __name__ == "__main__":
    main()

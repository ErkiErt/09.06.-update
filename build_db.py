"""Build Zenith_Materjalibaas.sqlite from the final Excel workbook.

Run locally:
    python build_db.py

Streamlit also calls build() automatically if the SQLite file is missing
but the Excel workbook is present.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parent
EXCEL_PATHS = [
    BASE / "Zenith_Materjalibaas_LOPLIK.xlsx",
    BASE / "data" / "Zenith_Materjalibaas_LOPLIK.xlsx",
]

TEXT_REPLACEMENTS = {
    "kõige " + "kõrg kemikaal": "parim keemiline vastupidavus",
    "kõige " + "kõrg temp": "kõrgeim temp",
    "kõige " + "kõrg": "kõrgeim",
    "kõige " + "tugevam": "kõrgeim tugevus",
    "kõige " + "pehmem": "kõige pehme",
    "kõige " + "kõvem": "kõrgeim kõvadus",
}

SHEET_MAP = {
    "50_ABILISE_INDEX": "assistant_product_index",
    "11_MASTER_VARIANDID": "product_variants",
    "14_SYNONYMID": "search_synonyms",
    "12_MATERJALID": "materials",
    "41_VAJA_YLEVAATUST": "needs_review",
    "01_ALLIKAD": "sources",
    "22_FILTRITE_KAART": "filter_map",
}


def find_excel() -> Path:
    for path in EXCEL_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Exceli faili ei leitud. Oodatud asukohad:\n"
        + "\n".join(str(path) for path in EXCEL_PATHS)
    )


def find_db_target(excel: Path | None = None) -> Path:
    workbook = excel or find_excel()
    return workbook.parent / "Zenith_Materjalibaas.sqlite"


def clean_text_values(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    for column in cleaned.columns:
        if cleaned[column].dtype == object:
            series = cleaned[column].astype("string")
            for old, new in TEXT_REPLACEMENTS.items():
                series = series.str.replace(old, new, regex=False)
            cleaned[column] = series
    return cleaned


def build(excel_path: Path | None = None, db_path: Path | None = None) -> Path:
    excel = excel_path or find_excel()
    db = db_path or find_db_target(excel)
    db.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loen Excelit: {excel}")
    workbook = pd.ExcelFile(excel)

    conn = sqlite3.connect(db)
    try:
        for sheet, table in SHEET_MAP.items():
            if sheet not in workbook.sheet_names:
                print(f"  Hoiatus: leht '{sheet}' puudub, tabel '{table}' jäetakse vahele")
                continue
            df = clean_text_values(workbook.parse(sheet))
            df.to_sql(table, conn, if_exists="replace", index=False)
            print(f"  {sheet} -> {table}: {len(df)} rida")

        conn.execute("PRAGMA integrity_check")
        conn.commit()
    finally:
        conn.close()

    print(f"Andmebaas loodud: {db}")
    return db


if __name__ == "__main__":
    build()

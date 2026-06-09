from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DB_NAME = "Zenith_Materjalibaas.sqlite"

DISPLAY_REPLACEMENTS = {
    "kõige " + "kõrg kemikaal": "parim keemiline vastupidavus",
    "kõige " + "kõrg temp": "kõrgeim temp",
    "kõige " + "kõrg": "kõrgeim",
    "kõige " + "tugevam": "kõrgeim tugevus",
    "kõige " + "pehmem": "kõige pehme",
    "kõige " + "kõvem": "kõrgeim kõvadus",
    "kõige " + "kall" + "im": "kõrgeima hinnaklassiga",
    "kall" + "im": "kõrgema hinnaklassiga",
}


def clean_display_text(value: Any) -> Any:
    """FIX D: clean user-visible wording at runtime.

    This protects the app even when Streamlit is running with an older
    SQLite/Excel payload that still contains stale wording.
    """
    if value is None or not isinstance(value, str):
        return value
    text = value
    for old, new in DISPLAY_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text

# ──────────────────────────────────────────────────────────────────────────
INTENT_RULES: dict[str, dict[str, Any]] = {
    "oilfuel": {
        "apps": {"oilfuel"},
        "tags": {"oil_fuel_resistance"},
        "materials": {"nbr", "fkm", "nbr_pvc", "cr"},
        "avoid_materials": {"epdm", "sbr", "nr"},
    },
    "weather_uv": {
        "apps": {"weather_uv"},
        "tags": {"uv_weather_resistance"},
        "materials": {"epdm", "csm", "silicone", "fkm", "cr"},
        "avoid_materials": set(),
    },
    "abrasion_wear": {
        "apps": {"abrasion_wear"},
        "tags": {"abrasion_resistance"},
        "materials": {"nr", "sbr"},
        "avoid_materials": set(),
    },
    "lumelukkamine": {
        "apps": {"abrasion_wear"},
        "tags": {"abrasion_resistance"},
        "materials": {"nr", "sbr"},
        "avoid_materials": {"epdm"},
    },
    "water_steam": {
        "apps": {"water_steam"},
        "tags": {"steam_resistance", "water_resistance"},
        "materials": {"epdm"},
        "avoid_materials": {"nbr"},
    },
    "construction_fire": {
        "apps": {"construction_fire"},
        "tags": {"flame_retardant", "fire_resistance"},
        "materials": {"cr"},
        "avoid_materials": set(),
    },
    "food_contact": {
        "apps": {"food_contact"},
        "tags": {"food_grade"},
        "materials": {"silicone", "epdm", "nbr", "cr"},
        "avoid_materials": set(),
    },
    "high_temperature": {
        "apps": {"high_temperature"},
        "tags": {"high_temperature"},
        "materials": {"silicone", "fkm", "epdm", "csm"},
        "avoid_materials": set(),
    },
    "low_temperature": {
        "apps": set(),
        "tags": set(),
        "materials": {"silicone", "epdm", "nr"},
        "avoid_materials": set(),
    },
    "chemical": {
        "apps": set(),
        "tags": {"chemical_resistance", "chemical_resistance_text"},
        "materials": {"fkm", "nbr", "epdm", "cr"},
        "avoid_materials": set(),
    },
    "seal_general": {"apps": set(), "tags": set(), "materials": set(), "avoid_materials": set()},
    "hose_general": {"apps": set(), "tags": set(), "materials": set(), "avoid_materials": set()},
}

MATERIAL_INTENTS = {
    "material_sbr": "sbr",
    "material_nbr": "nbr",
    "material_epdm": "epdm",
    "material_fkm": "fkm",
    "material_silicone": "silicone",
    "material_cr": "cr",
    "material_nr": "nr",
}

DIRECT_TERMS = {
    "lumesahk": "lumelukkamine",
    "sahk": "lumelukkamine",
    "lume sahk": "lumelukkamine",
    "snow plow": "lumelukkamine",
    "snow blade": "lumelukkamine",
    "oli": "oilfuel",
    "lipaagi": "oilfuel",
    "olipaagi": "oilfuel",
    "kutus": "oilfuel",
    "bensiin": "oilfuel",
    "diisel": "oilfuel",
    "uv": "weather_uv",
    "osoon": "weather_uv",
    "ilmastik": "weather_uv",
    "kulum": "abrasion_wear",
    "kulumine": "abrasion_wear",
    "kulumiskindel": "abrasion_wear",
    "aur": "water_steam",
    "steam": "water_steam",
    "vesi": "water_steam",
    "tulekindel": "construction_fire",
    "fire": "construction_fire",
    "food": "food_contact",
    "fda": "food_contact",
    "toiduklass": "food_contact",
    "kuum": "high_temperature",
    "korge temperatuur": "high_temperature",
    "kylm": "low_temperature",
    "kulm": "low_temperature",
    "kemikaal": "chemical",
    "keemia": "chemical",
}

# Värvid ei mõjuta materjali sobivust.
# Filtreeritakse nii kasutaja päringust kui ka teksti blob-vastete hulgast.
COLOR_TOKENS: frozenset[str] = frozenset({
    "must", "valge", "hall", "punane", "sinine", "roheline", "kollane", "pruun",
    "black", "white", "grey", "gray", "red", "blue", "green", "yellow", "brown",
    "nat", "natural", "beige", "clear", "transparent",
})

# Tekstisõnad, mis on värviga seotud — eemaldatakse blob-matchist
COLOR_BLOB_PATTERNS: tuple[str, ...] = (
    r"\bmust\b", r"\bvalge\b", r"\bhall\b", r"\bpunane\b",
    r"\bblack\b", r"\bwhite\b", r"\bgr[ae]y\b", r"\bred\b",
    r"\bnat\b", r"\bnatural\b",
)


@dataclass
class ParsedQuery:
    query: str
    normalized_query: str
    tokens: list[str]
    intents: set[str]
    required_materials: set[str]
    service_temp_c: float | None
    hardness: float | None
    thickness_mm: float | None


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.lower().replace(chr(176), " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_color_from_blob(blob: str) -> str:
    """Eemaldab värvisemantika blob-tekstist, et värvsõnad ei annaks tekstivaste skoori."""
    for pat in COLOR_BLOB_PATTERNS:
        blob = re.sub(pat, " ", blob)
    return blob


def split_codes(value: Any) -> set[str]:
    text = "" if value is None else str(value)
    return {part.strip() for part in re.split(r"[;,]", text) if part and part.strip()}


def load_database(db_path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    root = Path(__file__).resolve().parent
    db = db_path or root / DB_NAME
    if not db.exists():
        alt = root / "data" / DB_NAME
        if alt.exists():
            db = alt
    if not db.exists():
        raise FileNotFoundError(f"Andmebaasi ei leitud: {db}")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        tables = {
            "products": "select * from assistant_product_index order by product_name",
            "variants": "select * from product_variants order by product_name, thickness_mm_text",
            "synonyms": "select * from search_synonyms order by length(term) desc",
            "materials": "select * from materials order by material_code",
            "needs_review": "select * from needs_review order by priority, topic",
        }
        data = {name: [dict(row) for row in conn.execute(sql)] for name, sql in tables.items()}
        for opt, sql in [
            ("sources", "select * from sources order by source_id"),
            ("filter_map", "select * from filter_map order by user_need"),
        ]:
            try:
                data[opt] = [dict(row) for row in conn.execute(sql)]
            except Exception:
                data[opt] = []
        return data
    finally:
        conn.close()


def parse_query(query: str, synonyms: list[dict[str, Any]]) -> ParsedQuery:
    normalized = normalize_text(query)
    tokens = [
        t for t in re.findall(r"[a-z0-9_/-]+", normalized)
        if t not in COLOR_TOKENS
    ]
    intents: set[str] = set()
    required_materials: set[str] = set()

    for item in synonyms:
        term = normalize_text(item.get("term"))
        normalized_value = str(item.get("normalized") or "").strip()
        comparable_value = normalize_text(normalized_value)
        if term and term in normalized:
            if normalized_value in MATERIAL_INTENTS:
                required_materials.add(MATERIAL_INTENTS[normalized_value])
            elif comparable_value in MATERIAL_INTENTS:
                required_materials.add(MATERIAL_INTENTS[comparable_value])
            else:
                intents.add(normalized_value)
                intents.add(comparable_value)

    for term, intent in DIRECT_TERMS.items():
        if normalize_text(term) in normalized:
            intents.add(intent)

    for material in ["sbr", "nbr", "epdm", "fkm", "cr", "nr", "silicone", "silikon", "csm", "butyl"]:
        if re.search(rf"(^|\W){re.escape(material)}($|\W)", normalized):
            required_materials.add("silicone" if material == "silikon" else material)

    service_temp = None
    for pattern in [
        r"(-?\d+(?:[\.,]\d+)?)\s*(?:c|kraadi)",
        r"(?:temp|temperatuur)[^\d-]*(-?\d+(?:[\.,]\d+)?)",
        r"\+\s*(\d+(?:[\.,]\d+)?)",
    ]:
        match = re.search(pattern, normalized)
        if match:
            service_temp = float(match.group(1).replace(",", "."))
            break

    hardness = None
    match = re.search(r"(\d+(?:[\.,]\d+)?)\s*(?:shore a|shore|sh|kovad)", normalized)
    if match:
        hardness = float(match.group(1).replace(",", "."))

    thickness = None
    match = re.search(r"(\d+(?:[\.,]\d+)?)\s*mm", normalized)
    if match:
        thickness = float(match.group(1).replace(",", "."))

    return ParsedQuery(
        query=query,
        normalized_query=normalized,
        tokens=tokens,
        intents={intent for intent in intents if intent},
        required_materials=required_materials,
        service_temp_c=service_temp,
        hardness=hardness,
        thickness_mm=thickness,
    )


def thickness_matches(thickness_text: Any, requested_mm: float | None) -> bool:
    if requested_mm is None:
        return True
    text = normalize_text(thickness_text).replace(",", ".")
    parts = re.split(r"[;,\s]+", text)
    for part in parts:
        part_nums = [float(m) for m in re.findall(r"\d+(?:\.\d+)?", part)]
        if not part_nums:
            continue
        if "-" in part and len(part_nums) >= 2:
            if min(part_nums[0], part_nums[1]) <= requested_mm <= max(part_nums[0], part_nums[1]):
                return True
        else:
            if any(abs(n - requested_mm) <= 0.01 for n in part_nums):
                return True
    return False


def variant_thickness_matches(variants: list[dict[str, Any]], product_id: str, requested_mm: float | None) -> bool:
    if requested_mm is None:
        return True
    product_variants = [row for row in variants if row.get("product_id") == product_id]
    if not product_variants:
        return False
    return any(thickness_matches(row.get("thickness_mm_text"), requested_mm) for row in product_variants)


def build_text_blob(row: dict[str, Any]) -> str:
    """Ehitab otsitava teksti. Värviväli ja värvisõnad on eemaldatud."""
    fields = [
        "product_name",
        "article_code",
        "material_code",
        "material_name",
        "material_group",
        "application_categories",
        "property_tags",
        "feature_text",
    ]
    raw = normalize_text(" ".join(str(row.get(field) or "") for field in fields))
    return strip_color_from_blob(raw)


def quality_bonus(row: dict[str, Any]) -> int:
    """Arvutab kvaliteediboonuse toote omaduste põhjal.

    Kõrgem temp-vahemik, kulumiskindlus ja venivus tõstavad skoori.
    Boonus lisandub alati, mitte ainult puhul kui kasutaja seda küsis —
    nii soovitab süsteem vaikimisi parema omadustega tooteid.
    """
    bonus = 0

    # Temperatuurivahemiku laius — laiem vahemik = kõrgem kvaliteet
    min_t = row.get("min_temp_c")
    max_t = row.get("max_temp_c")
    if min_t is not None and max_t is not None:
        temp_range = float(max_t) - float(min_t)
        if temp_range >= 200:
            bonus += 15
        elif temp_range >= 150:
            bonus += 10
        elif temp_range >= 100:
            bonus += 5

    # Kulumiskindluse omadus (property_tags või application_categories)
    tags = split_codes(row.get("property_tags"))
    apps = split_codes(row.get("application_categories"))
    if "abrasion_resistance" in tags or "abrasion_wear" in apps:
        bonus += 8

    # Venivus — kõrgem elongation_percent = parem elastsus = keerukam toode
    elongation = row.get("elongation_percent")
    if elongation is not None:
        try:
            e = float(elongation)
            if e >= 500:
                bonus += 12
            elif e >= 350:
                bonus += 7
            elif e >= 200:
                bonus += 3
        except (ValueError, TypeError):
            pass

    # Spetsiifilised omaduste märgendid, mis viitavad kõrgemale klassile
    premium_tags = {
        "food_grade", "flame_retardant", "fire_resistance",
        "oil_fuel_resistance", "chemical_resistance", "uv_weather_resistance",
        "steam_resistance",
    }
    bonus += min(10, len(tags.intersection(premium_tags)) * 4)

    return bonus


def add_ui_requirements(
    parsed: ParsedQuery,
    required_materials: list[str] | None = None,
    required_intents: list[str] | None = None,
    service_temp_c: float | None = None,
    hardness: float | None = None,
    thickness_mm: float | None = None,
) -> ParsedQuery:
    return ParsedQuery(
        query=parsed.query,
        normalized_query=parsed.normalized_query,
        tokens=parsed.tokens,
        intents=set(parsed.intents).union(required_intents or []),
        required_materials=set(parsed.required_materials).union(required_materials or []),
        service_temp_c=service_temp_c if service_temp_c is not None else parsed.service_temp_c,
        hardness=hardness if hardness is not None else parsed.hardness,
        thickness_mm=thickness_mm if thickness_mm is not None else parsed.thickness_mm,
    )


def recommend(
    query: str,
    data: dict[str, list[dict[str, Any]]],
    required_materials: list[str] | None = None,
    required_intents: list[str] | None = None,
    service_temp_c: float | None = None,
    hardness: float | None = None,
    thickness_mm: float | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    parsed = parse_query(query, data["synonyms"])
    parsed = add_ui_requirements(parsed, required_materials, required_intents, service_temp_c, hardness, thickness_mm)
    variants = data["variants"]
    results: list[dict[str, Any]] = []

    for row in data["products"]:
        material = str(row.get("material_code") or "")
        apps = split_codes(row.get("application_categories"))
        tags = split_codes(row.get("property_tags"))
        blob = build_text_blob(row)  # värvid juba eemaldatud
        score = 0
        reasons: list[str] = []
        warnings: list[str] = []

        # Tekstivaste — värvitokenid on mh päringust eemaldatud
        if query.strip():
            token_hits = [
                token for token in parsed.tokens
                if len(token) >= 3 and not token.isdigit() and token in blob
            ]
            if token_hits:
                score += min(25, len(set(token_hits)) * 5)
                reasons.append("tekstivaste: " + ", ".join(sorted(set(token_hits))[:5]))

        # Intent reeglid
        for intent in parsed.intents:
            rule = INTENT_RULES.get(intent) or INTENT_RULES.get(normalize_text(intent))
            if not rule:
                continue
            app_hits = apps.intersection(rule["apps"])
            tag_hits = tags.intersection(rule["tags"])
            material_hit = material in rule["materials"]
            avoid_hit = material in rule["avoid_materials"]
            if app_hits:
                score += 35
                reasons.append(f"kasutusvaldkond sobib: {', '.join(sorted(app_hits))}")
            if tag_hits:
                score += 30
                reasons.append(f"omadus sobib: {', '.join(sorted(tag_hits))}")
            if material_hit:
                score += 15
                reasons.append(f"materjal sobib nõudele: {material}")
            if avoid_hit:
                score -= 30
                warnings.append(f"{material.upper()} võib selle kasutuse jaoks olla nõrk valik")

        # Materjali filter
        if parsed.required_materials:
            if material in parsed.required_materials:
                score += 45
                reasons.append(f"nõutud materjal: {material}")
            else:
                score -= 80
                warnings.append("ei vasta valitud materjalile")

        # Temperatuur
        if parsed.service_temp_c is not None:
            min_temp = row.get("min_temp_c")
            max_temp = row.get("max_temp_c")
            if min_temp is not None and max_temp is not None:
                if float(min_temp) <= parsed.service_temp_c <= float(max_temp):
                    score += 35
                    reasons.append(f"temperatuurivahemik katab {parsed.service_temp_c:g} °C")
                else:
                    score -= 90
                    warnings.append(
                        f"temperatuur {parsed.service_temp_c:g} °C jääb vahemikust välja "
                        f"({float(min_temp):g}..{float(max_temp):g} °C)"
                    )

        # Shore kõvadus — ainult kui kasutaja seda küsis; EI määra kulumiskindlust
        if parsed.hardness is not None:
            row_hardness = row.get("hardness_shore_a")
            if row_hardness is not None:
                delta = abs(float(row_hardness) - parsed.hardness)
                if delta <= 5:
                    score += 20
                    reasons.append(f"kõvadus sobib: {float(row_hardness):g} Shore A")
                elif delta <= 15:
                    score += 5
                    reasons.append(f"kõvadus ligikaudu: {float(row_hardness):g} Shore A")
                else:
                    score -= 10
                    warnings.append(f"kõvadus erineb ({float(row_hardness):g} vs {parsed.hardness:g} Shore A)")

        # Paksus
        if parsed.thickness_mm is not None:
            product_match = thickness_matches(row.get("thickness_text"), parsed.thickness_mm)
            variant_match = variant_thickness_matches(variants, str(row.get("product_id")), parsed.thickness_mm)
            if product_match or variant_match:
                score += 25
                reasons.append(f"paksus {parsed.thickness_mm:g} mm on saadaval")
            else:
                score -= 60
                warnings.append(f"paksust {parsed.thickness_mm:g} mm ei leitud")

        # Kvaliteediboonus — laiema temp-vahemiku, kulumiskindluse ja venivusega
        # tooted saavad väikese eelise, nii eelistatakse paremate omadustega tooteid.
        if score > 0:
            score += quality_bonus(row)

        if not query.strip() and not parsed.intents and not parsed.required_materials:
            score += 1

        if "needs_classification" in apps:
            warnings.append("kasutusvaldkond vajab ülevaatust")
        verification = normalize_text(row.get("verification_status"))
        if verification in {
            "catalog_extract_needs_pdf_page_reference",
            "needs_business_review",
            "needs_review",
        }:
            warnings.append("soovita kontrollida PDF lehe viitega")

        if score > 0:
            result = dict(row)
            for key, value in list(result.items()):
                result[key] = clean_display_text(value)
            result["score"] = score
            result["reasons"] = clean_display_text("; ".join(dict.fromkeys(reasons)) or "üldine vaste")
            result["warnings"] = clean_display_text("; ".join(dict.fromkeys(warnings)))
            results.append(result)

    results.sort(key=lambda item: (item["score"], item.get("max_temp_c") or -999), reverse=True)
    return results[:limit]


def variants_for_product(data: dict[str, list[dict[str, Any]]], product_id: str) -> list[dict[str, Any]]:
    return [row for row in data["variants"] if row.get("product_id") == product_id]


def quick_answer(result: dict[str, Any]) -> str:
    warnings = f" Hoiatus: {result['warnings']}." if result.get("warnings") else ""
    temp = ""
    if result.get("min_temp_c") is not None and result.get("max_temp_c") is not None:
        temp = f", {result['min_temp_c']:g}..{result['max_temp_c']:g} °C"
    return (
        f"{result.get('product_name')} ({result.get('article_code')}, "
        f"{str(result.get('material_code')).upper()}{temp}) "
        f"- skoor {result.get('score')}. Põhjus: {result.get('reasons')}.{warnings}"
    )

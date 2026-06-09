from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
from recommendation_engine import load_database, recommend, variants_for_product

BASE = Path(__file__).resolve().parent

def _find_file(name: str) -> Path | None:
    for candidate in [BASE / name, BASE / "data" / name]:
        if candidate.exists():
            return candidate
    return None

DB_PATH = _find_file("Zenith_Materjalibaas.sqlite")
EXCEL_PATH = _find_file("Zenith_Materjalibaas_LOPLIK.xlsx")

st.set_page_config(page_title="Zenith materjalisoovitaja", page_icon="Z", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1.2rem;}
.hero {
    padding: 1rem 1rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(124,92,255,0.22), rgba(19,24,37,0.95));
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 0.9rem;
}
.hero h1 {margin: 0; font-size: 1.9rem;}
.hero p {margin: 0.35rem 0 0 0; opacity: 0.9;}
.card {
    padding: 0.85rem 0.95rem;
    border-radius: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 0.75rem;
}
.badge {
    display: inline-block; padding: 0.18rem 0.48rem; border-radius: 999px;
    background: rgba(124,92,255,0.22); border: 1px solid rgba(124,92,255,0.35);
    margin-right: 0.3rem; margin-bottom: 0.22rem; font-size: 0.78rem;
}
.matinfo {
    background: rgba(255,255,255,0.04);
    border-left: 3px solid rgba(124,92,255,0.6);
    border-radius: 0 10px 10px 0;
    padding: 0.55rem 0.8rem;
    margin: 0.4rem 0 0.2rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
}
.small {opacity: 0.78; font-size: 0.92rem;}
@media (max-width: 700px) {
    .hero h1 {font-size: 1.45rem;}
}
</style>
""", unsafe_allow_html=True)

if DB_PATH is None and EXCEL_PATH is not None:
    with st.spinner("Andmebaas puudub - genereerin Excelist..."):
        from build_db import build
        DB_PATH = build(excel_path=EXCEL_PATH)
elif DB_PATH is None:
    st.error("Ei leia andmebaasi ega Exceli faili.")
    st.stop()

@st.cache_data(show_spinner=False)
def get_data(db_mtime: float):
    return load_database(DB_PATH)

def as_df(rows):
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ── Tõlkekaardid ──────────────────────────────────────────────────────────

BADGE_LABELS: dict[str, str] = {
    "oilfuel":               "Õli / kütus",
    "weather_uv":            "UV / ilmastik",
    "abrasion_wear":         "Kulumiskindlus",
    "water_steam":           "Vesi / aur",
    "construction_fire":     "Tulekindlus",
    "food_contact":          "Food Grade",
    "high_temperature":      "Kõrge temperatuur",
    "low_temperature":       "Madal temperatuur",
    "chemical":              "Keemiline vastupidavus",
    "abrasion_resistance":   "Kulumiskindel",
    "oil_fuel_resistance":   "Õlikindel",
    "uv_weather_resistance": "UV / ilmastikukindel",
    "flame_retardant":       "Tulekindel",
    "fire_resistance":       "Tulekindel",
    "food_grade":            "Food Grade",
    "high_temperature":      "Kõrgtemperatuur",
    "soft_flexible":         "Pehme / painduv",
    "water_steam_resistance":"Vesi / aurupidav",
    "steam_resistance":      "Aurupidav",
    "water_resistance":      "Veekindel",
    "premium_strength":      "Premium",
    "chemical_resistance":   "Keemiline vastupidavus",
    "elasticity":            "Kõrge elastsus",
    "needs_classification":  "",
}

STATUS_LABELS: dict[str, str] = {
    "catalog_extract_needs_pdf_page_reference": "Kinnitamata – PDF viide puudub",
    "catalogextractneedspdfpagereference":       "Kinnitamata – PDF viide puudub",
    "kinnitatud osaliselt":                      "Kinnitatud osaliselt",
    "zenithcatalogextract":                      "Zenithi kataloog (väljavõte)",
    "zenith_catalog_extract":                    "Zenithi kataloog (väljavõte)",
    "inferredfromfeaturetext":                   "Tuletatud tekstist",
    "inferred_from_feature_text":                "Tuletatud tekstist",
    "partialauditexample":                       "Osalise auditi näide",
    "partial_audit_example":                     "Osalise auditi näide",
    "prototypeguidance":                         "Prototüübi juhis",
    "prototype_guidance":                        "Prototüübi juhis",
    "needszenithorsupplierconfirmation":         "Vajab tarnija kinnitust",
    "needs_zenith_or_supplier_confirmation":     "Vajab tarnija kinnitust",
    "materialgroupfromzenithextract":            "Materjaligrupist tuletatud",
    "resistancefieldsneedreviewifpresent":       "Vajab ülevaatust",
    "structured_from_zenith_materials":          "Zenithi materjaliloend",
    "structuredfromzenithmaterials":             "Zenithi materjaliloend",
    "primary_reference_available":              "Primaarne allikas saadaval",
    "primaryreferenceavailable":                "Primaarne allikas saadaval",
    "partial_examples_only":                    "Osalised näited",
    "partialexamplesonly":                      "Osalised näited",
    "initialimport":                            "Esialgne import",
    "initial_import":                           "Esialgne import",
    "catalogextractneedspdfpagereference 1":    "Kinnitamata – PDF viide puudub",
}

MATERIAL_INFO: dict[str, dict] = {
    "sbr": {
        "nimi": "SBR — Stüreen-butadieen",
        "tugevus": "🔨 Hea kulumiskindlus ja rebenemiskindlus",
        "piir": "⚠️ Ei sobi õli, kütuse ega UV-kiirguse kätte",
        "temp": "−30 °C kuni +70 °C",
        "kasutus": "Üldkasutatav tihend, sahkterad, abrasiivne keskkond",
        "värv": "Must",
    },
    "nbr": {
        "nimi": "NBR — Nitriilkumm",
        "tugevus": "🛢️ Parim õli- ja kütusekindlus standardkummide seas",
        "piir": "⚠️ Ei sobi UV-kiirguse ja osooniga kokku; välitingimustesse mitte",
        "temp": "−30 °C kuni +90–110 °C (sõltub klassist)",
        "kasutus": "Masinate tihendid, hüdraulika, õlipaagid, kütuseliinid",
        "värv": "Must (FG-versioon: off-white)",
    },
    "epdm": {
        "nimi": "EPDM — Etüleen-propüleen",
        "tugevus": "☀️ Parim UV-, osoon- ja ilmastikukindlus; sobib veega",
        "piir": "⚠️ EI SOBI õli ega kütusega — keemiline ühildumatus",
        "temp": "−40 °C kuni +130–140 °C (Peroxid klass)",
        "kasutus": "Katused, välitihendid, joogivesi (WRAS), UV-keskkond",
        "värv": "Must (FG-versioon: off-white)",
    },
    "cr": {
        "nimi": "CR — Neopreen (kloropreen)",
        "tugevus": "🔥 Tulekindel; talub mõõdukat õli, UV-i ja ilmastikku",
        "piir": "⚠️ Mõõdukas temperatuuritaluvus; tugeva õlikeskkonna jaoks NBR parem",
        "temp": "−30 °C kuni +90–120 °C",
        "kasutus": "Ehituse tihendid, tulekindlad rakendused, laevaehitus",
        "värv": "Must (FG-versioon: off-white)",
    },
    "silicone": {
        "nimi": "Silikoon",
        "tugevus": "🌡️ Äärmuslik temperatuuritaluvus; Food Grade; UV-kindel",
        "piir": "⚠️ Madal mehaaniline tugevus; kallis; ei sobi tugeva õliga",
        "temp": "−60 °C kuni +200 °C (FG-versioon kuni +230 °C)",
        "kasutus": "Toiduainetööstus, meditsiin, ekstreemne temperatuur",
        "värv": "Punane / valge / läbipaistev / sinine",
    },
    "nr": {
        "nimi": "NR — Looduslik kautšuk",
        "tugevus": "💪 Erakordselt kõrge kulumiskindlus ja elastsus (kuni 900% venitus)",
        "piir": "⚠️ Ei sobi õli, UV ega osooniga; max +70 °C",
        "temp": "−40 °C kuni +70 °C",
        "kasutus": "Kaevandus, sahkterad, abrasiivne materjal, transportlindid",
        "värv": "Must / punane",
    },
    "fkm": {
        "nimi": "FKM — Viton (fluoroelastomeer)",
        "tugevus": "⚗️ Parim keemiline vastupidavus; kõrgeim temperatuuritaluvus",
        "piir": "⚠️ Kõrgeima hinnaklassiga; jäik madalatel temperatuuridel",
        "temp": "−30 °C kuni +250 °C",
        "kasutus": "Keemiatööstus, ekstreemne kemikaalikeskkond, kõrgtemperatuur",
        "värv": "Must/pruun",
    },
    "csm": {
        "nimi": "CSM — Hypalon",
        "tugevus": "🌤️ Väga hea UV-, kemikaal- ja osoonikindlus; tulekindel",
        "piir": "⚠️ Piiratud kättesaadavus; kõrgem hind",
        "temp": "−30 °C kuni +140 °C",
        "kasutus": "Keemiatanklad, veekindlad pinnakatted, UV-välistingimused",
        "värv": "Must",
    },
    "nbrpvc": {
        "nimi": "NBR/PVC — Nitriil-PVC segu",
        "tugevus": "🔥🛢️ Ühendab NBR õlikindluse ja CR tulekindluse",
        "piir": "⚠️ Kompromissmaterjal — ei ole kumbas otsaotsa parim",
        "temp": "−25 °C kuni +100 °C",
        "kasutus": "Kaablitihendid, tulekindlad + õlikindlad rakendused",
        "värv": "Must",
    },
    "butyl": {
        "nimi": "Butüülkumm (IIR)",
        "tugevus": "💨 Parim gaasipidavus; väga hea kemikaal- ja aurukindlus",
        "piir": "⚠️ Ei sobi õli ega kütusega; madal mehaaniline tugevus",
        "temp": "−40 °C kuni +125 °C",
        "kasutus": "Gaasitihendid, autokummid, kemikaalimahutid, aurutihendid",
        "värv": "Must",
    },
}


def translate_badge(raw: str) -> str:
    key = raw.strip().lower().replace("-", "_").replace(" ", "_")
    key = key.replace("generalsheet", "").replace("general_sheet", "").strip("_")
    if key in BADGE_LABELS:
        return BADGE_LABELS[key]
    if key and key not in ("", "needs_classification"):
        return key.replace("_", " ").capitalize()
    return ""


def translate_status(raw: str | None) -> str:
    if not raw:
        return "—"
    key = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    return STATUS_LABELS.get(str(raw).strip(), STATUS_LABELS.get(key, str(raw).strip()))


def badge_line(values):
    labels = []
    for v in values:
        if v and str(v).strip():
            translated = translate_badge(str(v).strip())
            if translated:
                labels.append(translated)
    unique = list(dict.fromkeys(labels))
    return " ".join(f'<span class="badge">{lbl}</span>' for lbl in unique) if unique else ""


def material_info_box(material_code: str) -> None:
    info = MATERIAL_INFO.get(str(material_code).lower().replace("/", "").replace("-", "").replace("_", ""))
    if not info:
        info = MATERIAL_INFO.get(str(material_code).lower().replace("_", "").replace("-", "").replace("/", ""))
    if not info:
        return
    st.markdown(
        f'<div class="matinfo">'
        f'<strong>{info["nimi"]}</strong><br>'
        f'{info["tugevus"]}<br>'
        f'{info["piir"]}<br>'
        f'🌡️ <em>Temperatuur:</em> {info["temp"]}<br>'
        f'🔧 <em>Tüüpiline kasutus:</em> {info["kasutus"]}'
        f'</div>',
        unsafe_allow_html=True,
    )


data = get_data(DB_PATH.stat().st_mtime)
materials = sorted({row["material_code"] for row in data["products"] if row.get("material_code")})
intent_options = {
    "Õli / kütus":            "oilfuel",
    "UV / ilmastik":          "weather_uv",
    "Kulumine / sahk":        "abrasion_wear",
    "Vesi / aur":             "water_steam",
    "Tulekindlus":            "construction_fire",
    "Food Grade":             "food_contact",
    "Kõrge temperatuur":      "high_temperature",
    "Madal temperatuur":      "low_temperature",
    "Keemiline vastupidavus": "chemical",
}

nav = st.radio("", ["Soovitus", "Andmed", "Kontroll"], horizontal=True, label_visibility="collapsed")

st.markdown('<div class="hero"><h1>🧩 Zenith materjalisoovitaja</h1><p>Kiire otsing, selged soovitused ja nähtavad kontrollimärgid.</p></div>', unsafe_allow_html=True)

# FIX #4: Mobiilisõbralik sidebar – väikestel ekraanidel kuvatakse filtrid
# kokkupandava expander'ina peamisel alal, mitte sidebaril.
def render_filters():
    query = st.text_input("Kirjelda vajadust", placeholder="nt õlipaagi tihend 100 kraadi 70 Shore")
    example = st.selectbox("Kiirpäring", ["", "Õlipaagi tihend", "Lumesahk", "Food Grade", "UV EPDM", "CR tulekindel"])
    if example and not query:
        query = {
            "Õlipaagi tihend": "õlipaagi tihend 100 kraadi",
            "Lumesahk":        "lumesahk kulumiskindel 10 mm",
            "Food Grade":      "food grade 120 kraadi",
            "UV EPDM":         "UV ilmastik EPDM",
            "CR tulekindel":   "tulekindel CR ehitus",
        }[example]

    required_materials = st.multiselect("Materjal", materials)
    selected_intent_labels = st.multiselect("Kasutus / omadus", list(intent_options.keys()))
    required_intents = [intent_options[x] for x in selected_intent_labels]

    st.markdown("### Täpsed filtrid")
    use_temp = st.checkbox("Töötemperatuur")
    service_temp = st.number_input("°C", value=100.0, step=5.0) if use_temp else None
    use_hardness = st.checkbox("Kõvadus")
    hardness = st.number_input("Shore A", value=70.0, step=5.0) if use_hardness else None
    use_thickness = st.checkbox("Paksus")
    thickness = st.number_input("mm", value=5.0, step=0.5) if use_thickness else None
    limit = st.slider("Tulemusi", 3, 20, 8)
    return query, required_materials, required_intents, service_temp, hardness, thickness, limit


with st.sidebar:
    st.markdown("### 🔍 Filtrid")
    query, required_materials, required_intents, service_temp, hardness, thickness, limit = render_filters()

results = recommend(query, data, required_materials, required_intents, service_temp, hardness, thickness, limit)

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 Tooteid", len(data['products']))
c2.metric("📏 Variante", len(data['variants']))
c3.metric("✅ Vasteid", len(results))
c4.metric("💬 Sünonüüme", len(data['synonyms']))

# ── SOOVITUS ──────────────────────────────────────────────────────────────
if nav == "Soovitus":
    if results:
        best = results[0]
        with st.container(border=True):
            st.subheader("⭐ Parim soovitus")
            st.markdown(f"**{best.get('product_name')}**")
            st.markdown(f"`{best.get('article_code')}` · {str(best.get('material_code')).upper()} · skoor {best.get('score')}")
            if best.get('min_temp_c') is not None and best.get('max_temp_c') is not None:
                st.caption(f"🌡️ Temperatuur: {best['min_temp_c']:g}..{best['max_temp_c']:g} °C")
            material_info_box(best.get('material_code', ''))
            if best.get('reasons'):
                st.success(best['reasons'])
            if best.get('warnings'):
                st.warning(best['warnings'])

        st.markdown("---")
        for i, row in enumerate(results, 1):
            with st.container(border=True):
                col1, col2, col3 = st.columns([2.2, 1, 1])
                with col1:
                    st.markdown(f"### {i}. {row['product_name']}")
                    st.markdown(f"`{row['article_code']}` · **{str(row['material_code']).upper()}** · skoor {row['score']}")
                    vals = []
                    if row.get('application_categories'):
                        vals += str(row['application_categories']).split(';')
                    if row.get('property_tags'):
                        vals += str(row['property_tags']).split(';')
                    if vals:
                        st.markdown(badge_line(vals), unsafe_allow_html=True)
                    material_info_box(row.get('material_code', ''))
                with col2:
                    st.metric("Min °C", row.get('min_temp_c'))
                    st.metric("Max °C", row.get('max_temp_c'))
                with col3:
                    st.metric("Shore A", row.get('hardness_shore_a'))
                    st.metric("Paksus", row.get('thickness_text'))

                if row.get('feature_text'):
                    st.write(row['feature_text'])
                if row.get('warnings'):
                    st.info("⚠️ " + row['warnings'])
                if row.get('source_status') or row.get('verification_status'):
                    st.caption(
                        f"📎 Allikas: {translate_status(row.get('source_status'))} · "
                        f"Kontroll: {translate_status(row.get('verification_status'))} · "
                        f"Lukus: {row.get('locked_zenith')}"
                    )
                variants = variants_for_product(data, row['product_id'])
                if variants:
                    with st.expander(f"📌 Variandid ({len(variants)})"):
                        vdf = as_df(variants)
                        cols = [c for c in ["thickness_mm_text","width_m_text","length_m_text","color","hardness_text","properties_text"] if c in vdf.columns]
                        st.dataframe(vdf[cols], use_container_width=True, hide_index=True)
    else:
        st.info("🔍 Sisesta vajadus või vali kiirpäring. Näide: õlipaagi tihend 100 kraadi.")

# ── ANDMED ────────────────────────────────────────────────────────────────
elif nav == "Andmed":
    st.subheader("📊 Andmed ja sõnastik")
    t1, t2, t3 = st.tabs(["Materjalid", "Sünonüümid", "Filtrikaart"])
    with t1:
        st.dataframe(as_df(data['materials']), use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(as_df(data['synonyms']), use_container_width=True, hide_index=True)
    with t3:
        st.dataframe(as_df(data.get('filter_map', [])), use_container_width=True, hide_index=True)

# ── KONTROLL ──────────────────────────────────────────────────────────────
else:
    st.subheader("🔍 Kontroll ja lähteinfo")
    st.caption("Tehnilised andmed, mis vajavad ülevaatust või kinnitust.")
    with st.expander("⚠️ Vaja ülevaatust", expanded=True):
        needs_df = as_df(data['needs_review'])
        st.dataframe(needs_df, use_container_width=True, hide_index=True)
    with st.expander("📋 Materjalide kokkuvõte"):
        mat_df = as_df(data['materials'])
        st.dataframe(mat_df, use_container_width=True, hide_index=True)
    with st.expander("📖 Allikad"):
        src_df = as_df(data.get('sources', []))
        if not src_df.empty:
            for col in ["source_status", "verification_status"]:
                if col in src_df.columns:
                    src_df[col] = src_df[col].apply(translate_status)
        st.dataframe(src_df, use_container_width=True, hide_index=True)

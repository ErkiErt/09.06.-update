
# Zenith materjalisoovitaja

Streamlit app kasutab `Zenith_Materjalibaas.sqlite` andmebaasi ja soovitab tooteid vaba teksti ning filtrite järgi.

## GitHub / Streamlit Cloud

Laadi üles kogu repo sisu, kindlasti koos `data/` kaustaga:

- `streamlit_app.py`
- `recommendation_engine.py`
- `build_db.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `data/Zenith_Materjalibaas.sqlite`
- `data/Zenith_Materjalibaas_LOPLIK.xlsx`

Kui SQLite puudub, ehitab app selle automaatselt Excelist uuesti.

## Käivitamine

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Näidispäringud

- `õlipaagi tihend 100 kraadi`
- `lumesahk kulumiskindel 10 mm`
- `food grade 120 kraadi`
- `UV ilmastik EPDM`
- `FKM 200 kraadi kemikaal`

Zenithi lukustatud tehnilisi andmeid ei muudeta ilma uuema allika või dokumenteeritud tõenduseta.

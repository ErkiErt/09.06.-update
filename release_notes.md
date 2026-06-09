# Zenith materjalisoovitaja – uuendus

## Tehtud
- Mobiilisõbralik navigeerimine: Soovitus / Andmed / Kontroll
- Sidebar ainult filtrite jaoks
- Puhas tume UI koos hero-ploki, kaartide ja badge'dega
- Tõendatud materjalireeglid: EPDM (vesi/aur/UV), CR (tulekindlus), NBR (õli/kütus), NBR/PVC
- Automaatne SQLite loomine Excelist, kui DB puudub
- Kontroll-vaade: allikad, ülevaatuse nimekiri, materjalide kokkuvõte

## Järgmine kontroll
- Testida Streamlit Cloudis
- Kontrollida mobiilis navigeerimise selgust
- Kinnitada materjalireeglid Zenithi tarnijaga
## FIX D - runtime sõnastuse puhastus

- Lisatud `clean_display_text()` soovitusmootorisse.
- Vanad fraasid puhastatakse ka siis, kui Streamlit kasutab vanemat SQLite/Excel payloadi.
- Eemaldatud kasutajale nähtavast tekstist varasemad vigased ülivõrde ja hinnaklassi sõnastused.

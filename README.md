# 📊 Aktieägaranalys Dashboard - I Love Lund AB

En Streamlit-dashboard för att analysera aktieägardata för I Love Lund AB.

## 🚀 Funktioner

- **Översikt & Trender** - Följ utvecklingen av antalet aktieägare över tid
- **Distribution** - Se ägarstruktur uppdelat på storleksklasser
- **Geografi** - Analysera var aktieägarna bor (fokus på Lund)
- **Ägartyper** - Fysiska vs juridiska personer, köns- och åldersfördelning
- **Cap Table** - Topp 50 största ägare med historisk jämförelse

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Starta lokalt

```bash
streamlit run src/app.py
```

## 🔐 Miljövariabler

Skapa en fil `.streamlit/secrets.toml` med:

```toml
DATA_ACCESS_PASSWORD = "ditt-lösenord"
```

## 📁 Projektstruktur

```
vantage_dashboard/
├── src/                 # Källkod
│   ├── app.py          # Huvudapplikation
│   ├── api.py          # API-klient
│   ├── config.py       # Konfiguration
│   └── data_manager.py # Datahantering
├── data/               # Datalagring
├── Dokumentation/      # Guider
└── requirements.txt    # Beroenden
```

## 👥 Kontakt

**Axel Lundberg** - 0705227904

---
*Byggt med ❤️ för I Love Lund AB*


# 📊 Aktieägaranalys Dashboard - I Love Lund AB

En Streamlit-dashboard för att analysera aktieägardata för I Love Lund AB.

## 🌐 Live Dashboard

**URL:** https://vantage-dashboard.streamlit.app *(uppdatera med din faktiska URL)*

Dashboarden körs på Streamlit Community Cloud och är tillgänglig för alla med länken.

---

## 🚀 Funktioner

- **Översikt & Trender** - Följ utvecklingen av antalet aktieägare över tid
- **Distribution** - Se ägarstruktur uppdelat på storleksklasser
- **Geografi** - Analysera var aktieägarna bor (fokus på Lund)
- **Ägartyper** - Fysiska vs juridiska personer, köns- och åldersfördelning
- **Cap Table** - Topp 50 största ägare med historisk jämförelse (lösenordsskyddad)

---

## 🏗️ Arkitektur

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   GitHub        │      │  Streamlit      │      │   Användare     │
│   Repository    │ ───► │  Cloud          │ ───► │   (webbläsare)  │
│                 │      │                 │      │                 │
│ - Källkod       │      │ - Kör appen     │      │ - Ser dashboard │
│ - Data (CSV)    │      │ - Auto-deploy   │      │ - Genererar     │
│                 │      │                 │      │   rapporter     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        ▲
        │
┌───────┴─────────┐
│   Lokal dator   │
│                 │
│ - Hämta ny data │
│ - Göra ändringar│
│ - Push till Git │
└─────────────────┘
```

### Så fungerar uppdateringar:
1. **Data hämtas lokalt** via Euroclear API (kräver certifikat)
2. **Ändringar pushas** till GitHub via GitHub Desktop
3. **Streamlit Cloud uppdateras automatiskt** inom ~1 minut

---

## 📁 Projektstruktur

```
vantage_dashboard/
├── src/                      # 🔧 KÄLLKOD (ändra här!)
│   ├── app.py               # Huvudapplikation
│   ├── api.py               # API-klient för Euroclear
│   ├── config.py            # Inställningar (ISIN, färger)
│   ├── data_manager.py      # Datahantering
│   └── tabs/                # Flikarna i dashboarden
│
├── data/                     # 📊 DATA
│   └── shareholders_history.csv  # Historisk ägardata
│
├── certs/                    # 🔐 CERTIFIKAT (ej på GitHub)
│
├── Dokumentation/            # 📚 GUIDER
│   ├── ÖVERLÄMNING.md       # För efterträdare
│   └── GDPR_GUIDE.md        # Dataskydd
│
├── Bilder/                   # 🖼️ Logotyper
├── Rapporter/                # 📄 Genererade rapporter
├── Scripts/                  # 🛠️ Hjälpskript
│
├── .streamlit/               # ⚙️ Streamlit-config
│   └── config.toml          # Tema och inställningar
│
├── .gitignore               # Filer som EJ laddas upp
├── requirements.txt         # Python-beroenden
├── Användarmanual_Dashboard.docx  # Manual för användare
└── README.md                # Denna fil
```

---

## 💻 Lokal utveckling

### Installation
```bash
cd vantage_dashboard
pip install -r requirements.txt
```

### Starta lokalt
```bash
streamlit run src/app.py
```

### Hämta ny data
1. Kör dashboarden lokalt
2. Välj datum i sidomenyn
3. Klicka "Hämta Data"
4. Committa och pusha via GitHub Desktop

---

## 🔐 Konfiguration

### Streamlit Cloud Secrets
Konfigureras på https://share.streamlit.io → App → Settings → Secrets:

```toml
DATA_ACCESS_PASSWORD = "ditt-lösenord"
```

### Lokal utveckling
Skapa `.streamlit/secrets.toml` (ignoreras av Git):

```toml
DATA_ACCESS_PASSWORD = "ditt-lösenord"
```

---

## 🔄 Uppdatera dashboarden

### Via GitHub Desktop (rekommenderat)
1. Gör ändringar i filerna
2. Öppna GitHub Desktop
3. Skriv en sammanfattning av ändringen
4. Klicka "Commit to main"
5. Klicka "Push origin"
6. ✅ Streamlit Cloud uppdateras automatiskt

### Via Cursor AI
1. Öppna projektet i Cursor
2. Beskriv vad du vill ändra
3. AI:n gör ändringarna
4. Testa lokalt
5. Pusha via GitHub Desktop

---

## 📚 Dokumentation

| Dokument | Beskrivning |
|----------|-------------|
| `Användarmanual_Dashboard.docx` | Guide för vanliga användare |
| `Dokumentation/ÖVERLÄMNING.md` | Komplett guide för efterträdare |
| `Dokumentation/GDPR_GUIDE.md` | Dataskydd och säkerhet |

---

## 👥 Kontakt

**Axel Lundberg** - 0705227904

---

*Byggt med ❤️ för I Love Lund AB*

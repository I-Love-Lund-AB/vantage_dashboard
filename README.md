# 📊 Aktieägaranalys Dashboard - I Love Lund AB

En Streamlit-dashboard för att analysera aktieägardata för I Love Lund AB.

## 🌐 Live Dashboard

**URL:** https://ilovelund-aktie.streamlit.app/

Dashboarden körs på Streamlit Community Cloud och är tillgänglig för alla med länken.

---

## 🚀 Funktioner

- **Översikt & Trender** - Följ utvecklingen av antalet aktieägare över tid
- **Distribution** - Se ägarstruktur uppdelat på storleksklasser
- **Geografi** - Analysera var aktieägarna bor (fokus på Lund)
- **Ägartyper** - Fysiska vs juridiska personer, köns- och åldersfördelning
- **Cap Table** - Topp 50 största ägare med historisk jämförelse (lösenordsskyddad)
- **Komplett Ägarlista** - Fullständig lista med alla aktieägare och deras innehav (lösenordsskyddad)

---

## 🏗️ Arkitektur

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   GitHub        │      │  Streamlit      │      │   Användare     │
│   Repository    │ ───► │  Cloud          │ ───► │   (webbläsare)  │
│                 │      │                 │      │                 │
│ - Källkod       │      │ - Kör appen     │      │ - Ser dashboard │
│ - Data (CSV)    │      │ - Auto-deploy   │      │ - Genererar     │
│                 │      │ - Hämtar data   │      │   rapporter     │
└─────────────────┘      │   via API       │      └─────────────────┘
        ▲                └─────────────────┘
        │                        │
        │                        │ Sparar CSV via
        └────────────────────────┘ GitHub API
```

### Så fungerar uppdateringar:
1. **Data hämtas direkt i dashboarden** via Euroclear API (knappen "Hämta Data" i sidomenyn)
2. **CSV-filen sparas automatiskt** till GitHub via GitHub Contents API
3. **Streamlit Cloud uppdateras automatiskt** med den nya datan

Kodändringar görs lokalt och pushas till GitHub — Streamlit Cloud hämtar dem automatiskt.

---

## 📁 Projektstruktur

```
vantage_dashboard/
├── src/                      # 🔧 KÄLLKOD (ändra här!)
│   ├── app.py               # Huvudapplikation
│   ├── api.py               # API-klient för Euroclear
│   ├── auth.py              # Autentisering mot Azure AD
│   ├── config.py            # Inställningar (ISIN, färger)
│   ├── data_manager.py      # Datahantering + GitHub-push
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
1. Öppna dashboarden (lokalt eller på https://ilovelund-aktie.streamlit.app/)
2. Välj datum i sidomenyn (sista helgfria vardagen föregående månad)
3. Klicka "Hämta Data"
4. Data sparas automatiskt till GitHub

---

## 🔐 Konfiguration

### Streamlit Cloud Secrets
Konfigureras på https://share.streamlit.io → App → Settings → Secrets:

```toml
# === GDPR / Dashboard-lösenord ===
DATA_ACCESS_PASSWORD = "ditt-lösenord"

# === Euroclear Vantage API ===
VANTAGE_API_URL = "https://api.euroclear.com/vantage/v1"
CLIENT_ID = "din-client-id"
TENANT_ID = "din-tenant-id"
APPLICATION_ID = "din-application-id"
CERTIFICATE_PASSWORD = "certifikat-lösenord"
CERTIFICATE_BASE64 = "base64-kodad-pfx-sträng"

# === GitHub (för att spara hämtad data permanent) ===
GITHUB_TOKEN = "ghp_din-token"
GITHUB_REPO = "I-Love-Lund-AB/vantage_dashboard"
GITHUB_CSV_PATH = "data/shareholders_history.csv"
```

### Lokal utveckling
Skapa `.env` i projektmappen (ignoreras av Git):

```
DATA_ACCESS_PASSWORD=xxx
VANTAGE_API_URL=https://api.euroclear.com/vantage/v1
CLIENT_ID=din-client-id
TENANT_ID=din-tenant-id
APPLICATION_ID=din-application-id
CERTIFICATE_PATH=certs/client_cert.pfx
CERTIFICATE_PASSWORD=certifikat-lösenord
```

---

## 🔄 Uppdatera dashboarden

### Hämta ny månadsdata
1. Gå till https://ilovelund-aktie.streamlit.app/
2. Klicka "Hämta Data" i sidomenyn
3. Klart — datan sparas automatiskt till GitHub

### Göra kodändringar
1. Gör ändringar i filerna under `src/`
2. Testa lokalt: `streamlit run src/app.py`
3. Committa och pusha via GitHub Desktop
4. Streamlit Cloud uppdateras automatiskt

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

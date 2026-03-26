# 📋 Överlämningsguide - Aktieägaranalys Dashboard

## Översikt

Detta dokument beskriver allt som behövs för att ta över förvaltningen av Aktieägaranalys Dashboard för I Love Lund AB.

---

## 🔑 Konton och Access

### 1. GitHub (Kodförvaring)
- **URL:** https://github.com/I-Love-Lund-AB/vantage_dashboard
- **Organisation:** I-Love-Lund-AB
- **Syfte:** Här ligger all källkod och data. Ändringar här uppdaterar automatiskt dashboarden.
- **Överlämning:** 
  1. Gå till repot på GitHub
  2. Settings → Collaborators → Add people
  3. Lägg till efterträdarens GitHub-användarnamn
  4. Alternativt: Ge admin-rättigheter via organisationens inställningar

### 2. Streamlit Cloud (Hosting)
- **URL:** https://share.streamlit.io
- **App-URL:** https://ilovelund-aktie.streamlit.app/
- **Syfte:** Här körs dashboarden live på internet
- **Överlämning:**
  1. Logga in på share.streamlit.io
  2. Gå till appen → Settings → Sharing
  3. Under "Who can manage this app" - lägg till efterträdarens email
  4. De får en inbjudan och blir admin för appen

### 3. Euroclear Vantage API
- **Syfte:** Hämtar aktieägardata
- **Certifikat:** Lagrat som base64-sträng i Streamlit Secrets (lokalt: `certs/`-mappen)
- **Överlämning:** Kopiera certifikat-mappen manuellt till efterträdaren om lokal utveckling behövs
- **Kontakt för nya certifikat:** Euroclear Sweden AB

---

## 📁 Projektstruktur

```
vantage_dashboard/
├── src/                      # KÄLLKOD (här gör man ändringar)
│   ├── app.py               # Huvudapplikationen
│   ├── api.py               # API-koppling till Euroclear
│   ├── auth.py              # Autentisering mot Azure AD
│   ├── config.py            # Inställningar (ISIN, färger, etc.)
│   ├── data_manager.py      # Hanterar datalagring + GitHub-push
│   └── tabs/                # Flikarna i dashboarden
│
├── data/                     # DATA
│   └── shareholders_history.csv  # All historisk ägardata
│
├── certs/                    # CERTIFIKAT (hemliga, ej på GitHub)
│
├── Dokumentation/            # GUIDER
├── Bilder/                   # Logotyper
├── Rapporter/                # Genererade HTML-rapporter
├── Scripts/                  # Hjälpskript
│
├── .streamlit/               # Streamlit-konfiguration
├── requirements.txt          # Python-beroenden
└── Användarmanual_Dashboard.docx  # Manual för användare
```

---

## 🔄 Vanliga arbetsflöden

### Hämta ny månadsdata
Datahämtning fungerar direkt i den publika dashboarden — det krävs ingen lokal installation.

1. Gå till https://ilovelund-aktie.streamlit.app/
2. Välj rätt datum i sidomenyn (sista helgfria vardagen i föregående månad)
3. Klicka "Hämta Data"
4. Datan hämtas från Euroclear API och sparas automatiskt till GitHub
5. Dashboarden uppdateras med den nya datan

**Så fungerar det tekniskt:**
- API-credentials (certifikat, klient-ID etc.) lagras i Streamlit Secrets
- Certifikatet lagras som en base64-kodad sträng (ej som fil)
- Efter lyckad hämtning pushas CSV-filen till GitHub via GitHub Contents API
- Streamlit Cloud laddar om med den nya datan

### Göra kodändringar
1. Öppna projektet i **Cursor** (eller annan editor)
2. Gör dina ändringar i filerna under `src/`
3. Testa lokalt: `streamlit run src/app.py`
4. När det fungerar: Committa och pusha via GitHub Desktop
5. Ändringar går live automatiskt på https://ilovelund-aktie.streamlit.app/

### Använda AI (Cursor) för ändringar
1. Öppna projektet i Cursor
2. Tryck Ctrl+L för att öppna chatten
3. Beskriv vad du vill ändra på svenska
4. AI:n föreslår och kan göra ändringar
5. Granska, testa lokalt, committa och pusha

---

## 🔐 Hemligheter och Lösenord

### Streamlit Cloud Secrets
- **Plats:** Streamlit Cloud → App → Settings → Secrets
- **Format:** TOML
- **Fullständig konfiguration:**
  ```toml
  # === GDPR / Dashboard-lösenord ===
  DATA_ACCESS_PASSWORD = "ditt-lösenord-här"

  # === Euroclear Vantage API ===
  VANTAGE_API_URL = "https://api.euroclear.com/vantage/v1"
  CLIENT_ID = "din-client-id"
  TENANT_ID = "din-tenant-id"
  APPLICATION_ID = "din-application-id"
  CERTIFICATE_PASSWORD = "certifikat-lösenord"

  # Certifikatet som base64 (genereras en gång, se instruktion nedan)
  CERTIFICATE_BASE64 = "MIIJ...lång-sträng..."

  # === GitHub (för att spara hämtad data permanent) ===
  GITHUB_TOKEN = "ghp_din-token"
  GITHUB_REPO = "I-Love-Lund-AB/vantage_dashboard"
  GITHUB_CSV_PATH = "data/shareholders_history.csv"
  ```

#### Engångsinställning: Generera CERTIFICATE_BASE64
Kör detta på din lokala dator (i projektmappen):
```bash
python -c "import base64; print(base64.b64encode(open('certs/client_cert.pfx','rb').read()).decode())"
```
Kopiera hela den utskrivna strängen och klistra in som värde för `CERTIFICATE_BASE64` i Streamlit Secrets.

#### Engångsinställning: Skapa GITHUB_TOKEN
1. Gå till https://github.com/settings/tokens (eller organisationens inställningar)
2. Klicka "Generate new token (classic)"
3. Ge den ett namn (t.ex. "Vantage Dashboard")
4. Välj scope: `repo` (full kontroll av repositories)
5. Klicka "Generate token" och kopiera värdet
6. Klistra in som `GITHUB_TOKEN` i Streamlit Secrets

#### Engångsinställning: GITHUB_REPO
Sätt `GITHUB_REPO` till `I-Love-Lund-AB/vantage_dashboard`.

### Lokala miljövariabler (för utveckling)
- **Fil:** `.env` i projektmappen (skapas manuellt, finns ej på GitHub)
- **Innehåll:**
  ```
  DATA_ACCESS_PASSWORD=xxx
  VANTAGE_API_URL=https://api.euroclear.com/vantage/v1
  CLIENT_ID=din-client-id
  TENANT_ID=din-tenant-id
  APPLICATION_ID=din-application-id
  CERTIFICATE_PATH=certs/client_cert.pfx
  CERTIFICATE_PASSWORD=certifikat-lösenord
  ```
- **OBS:** Lokalt behövs varken `CERTIFICATE_BASE64`, `GITHUB_TOKEN` eller `GITHUB_REPO` — de används bara på Streamlit Cloud.

---

## 🛠️ Teknisk information

### Språk och ramverk
- **Python 3.11+**
- **Streamlit** - Webbramverk för dashboards
- **Pandas** - Datahantering
- **Plotly** - Interaktiva grafer
- **MSAL** - Microsoft Authentication Library (Azure AD)

### Nyckelmoduler
| Modul | Syfte |
|-------|-------|
| `auth.py` | Autentisering mot Azure AD med certifikat. Laddar credentials från `.env` (lokalt) eller `st.secrets` (Cloud). Stöder certifikat från fil eller base64. |
| `api.py` | API-klient mot Euroclear Vantage. Hämtar aktieägardata. |
| `data_manager.py` | Sparar och laddar CSV-data. Metoden `push_csv_to_github()` pushar data till GitHub via Contents API. |
| `app.py` | Huvudapplikation med alla flikar, diagram och UI-logik. |

### Installera lokalt
```bash
cd vantage_dashboard
pip install -r requirements.txt
streamlit run src/app.py
```

### Beroenden
Se `requirements.txt` för alla Python-paket.

---

## 📞 Support och kontakt

### Ursprunglig utvecklare
- **Axel Lundberg**
- **Telefon:** 0705227904

### Vid tekniska problem
1. Kolla Streamlit Cloud logs: App → Manage app → Logs
2. Testa lokalt för att se felmeddelanden
3. Använd Cursor AI för hjälp med buggar

### Euroclear API-problem
- Kontakta Euroclear Sweden AB för certifikat och API-frågor

---

## ✅ Checklista vid överlämning

- [ ] Efterträdare har GitHub-konto
- [ ] Efterträdare tillagd som collaborator på GitHub-repot (I-Love-Lund-AB)
- [ ] Efterträdare har Streamlit Cloud-konto
- [ ] Efterträdare tillagd som admin på Streamlit-appen
- [ ] Certifikat-mappen (certs/) kopierad till efterträdaren (för lokal utveckling)
- [ ] Lösenord för GDPR-data delat
- [ ] Streamlit Secrets konfigurerade med alla API-credentials
- [ ] GITHUB_TOKEN skapad och tillagd i Secrets
- [ ] Efterträdare har testat att hämta data via dashboarden
- [ ] Efterträdare har testat att göra en kodändring och pusha

---

*Senast uppdaterad: Mars 2026*

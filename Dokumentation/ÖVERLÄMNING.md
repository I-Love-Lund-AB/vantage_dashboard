# 📋 Överlämningsguide - Aktieägaranalys Dashboard

## Översikt

Detta dokument beskriver allt som behövs för att ta över förvaltningen av Aktieägaranalys Dashboard för I Love Lund AB.

---

## 🔑 Konton och Access

### 1. GitHub (Kodförvaring)
- **URL:** https://github.com/axelILL/vantage_dashboard
- **Syfte:** Här ligger all källkod. Ändringar här uppdaterar automatiskt dashboarden.
- **Överlämning:** 
  1. Gå till repot på GitHub
  2. Settings → Collaborators → Add people
  3. Lägg till efterträdarens GitHub-användarnamn
  4. Alternativt: Överför ägarskap via Settings → Transfer ownership

### 2. Streamlit Cloud (Hosting)
- **URL:** https://share.streamlit.io
- **App-URL:** https://ilovelund-dashboard.streamlit.app/
- **Syfte:** Här körs dashboarden live på internet
- **Överlämning:**
  1. Logga in på share.streamlit.io
  2. Gå till appen → Settings → Sharing
  3. Under "Who can manage this app" - lägg till efterträdarens email
  4. De får en inbjudan och blir admin för appen

### 3. Euroclear Vantage API
- **Syfte:** Hämtar aktieägardata
- **Certifikat:** Finns i `certs/`-mappen (LADDAS INTE UPP TILL GITHUB)
- **Överlämning:** Kopiera certifikat-mappen manuellt till efterträdaren
- **Kontakt för nya certifikat:** Euroclear Sweden AB

---

## 📁 Projektstruktur

```
vantage_dashboard/
├── src/                      # KÄLLKOD (här gör man ändringar)
│   ├── app.py               # Huvudapplikationen
│   ├── api.py               # API-koppling till Euroclear
│   ├── config.py            # Inställningar (ISIN, färger, etc.)
│   ├── data_manager.py      # Hanterar datalagring
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
1. Öppna dashboarden **lokalt** (inte på Streamlit Cloud)
2. Kör: `streamlit run src/app.py`
3. Välj rätt datum i sidomenyn och klicka "Hämta Data"
4. Öppna GitHub Desktop
5. Committa ändringarna med meddelande: "Data uppdaterad YYYY-MM"
6. Klicka "Push origin"
7. Streamlit Cloud uppdateras automatiskt inom 1 minut

### Göra kodändringar
1. Öppna projektet i **Cursor** (eller annan editor)
2. Gör dina ändringar i filerna under `src/`
3. Testa lokalt: `streamlit run src/app.py`
4. När det fungerar: Committa och pusha via GitHub Desktop
5. Ändringar går live automatiskt

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
  GITHUB_REPO = "organisation/repo-namn"
  GITHUB_CSV_PATH = "data/shareholders_history.csv"
  ```

#### Engångsinställning: Generera CERTIFICATE_BASE64
Kör detta på din lokala dator (i projektmappen):
```bash
python -c "import base64; print(base64.b64encode(open('certs/cert.pfx','rb').read()).decode())"
```
Kopiera hela den utskrivna strängen och klistra in som värde för `CERTIFICATE_BASE64` i Streamlit secrets.

#### Engångsinställning: Skapa GITHUB_TOKEN
1. Gå till https://github.com/settings/tokens
2. Klicka "Generate new token (classic)"
3. Ge den ett namn (t.ex. "Vantage Dashboard")
4. Välj scope: `repo` (full kontroll av repositories)
5. Klicka "Generate token" och kopiera värdet
6. Klistra in som `GITHUB_TOKEN` i Streamlit secrets

#### Engångsinställning: GITHUB_REPO
Sätt `GITHUB_REPO` till `ägare/repo-namn` (t.ex. `ilovelund/vantage_dashboard`).

### Lokala miljövariabler (för utveckling)
- **Fil:** `.env` i projektmappen (skapas manuellt, finns ej på GitHub)
- **Innehåll:**
  ```
  DATA_ACCESS_PASSWORD=xxx
  VANTAGE_API_URL=https://api.euroclear.com/vantage/v1
  CLIENT_ID=din-client-id
  TENANT_ID=din-tenant-id
  APPLICATION_ID=din-application-id
  CERTIFICATE_PATH=certs/cert.pfx
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
- [ ] Efterträdare tillagd som collaborator på GitHub-repot
- [ ] Efterträdare har Streamlit Cloud-konto
- [ ] Efterträdare tillagd som admin på Streamlit-appen
- [ ] Certifikat-mappen (certs/) kopierad till efterträdaren
- [ ] Lösenord för GDPR-data delat
- [ ] Cursor installerat på efterträdarens dator
- [ ] GitHub Desktop installerat
- [ ] Efterträdare har testat att hämta data lokalt
- [ ] Efterträdare har testat att göra en ändring och pusha

---

*Senast uppdaterad: Februari 2026*


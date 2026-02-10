# GDPR-guide för Aktieägar Dashboard

## ⚠️ Viktigt: Personuppgiftshantering

Denna dashboard hanterar känsliga personuppgifter enligt GDPR. Följ dessa riktlinjer för att säkerställa compliance.

## Identifierade Känsliga Personuppgifter

Följande fält i datan innehåller personuppgifter:
- **`pnrOrgnr`**: Personnummer eller organisationsnummer (mycket känsligt)
- **`name`**: Namn på aktieägare
- **`streetAddress`**: Gatuadress
- **`coAdress`**: C/O-adress
- **`postalCode`**: Postnummer
- **`city`**: Stad
- **`holdingsQuantity`**: Ekonomisk information (innehav)

## Implementerade Säkerhetsåtgärder

### ✅ Anonymisering i Rådata-visning
- Personnummer maskeras: `XX***XX` (visar bara första och sista 2 siffrorna)
- Namn maskeras: `A***` (visar bara första bokstaven)
- Adresser maskeras: `Gatan***`
- Känsliga fält döljs i standardvisningen

### ✅ Lösenordsskydd för Avanonymisering
- **Standardlösenord:** `admin123` (⚠️ ÄNDRA DETTA I PRODUKTION!)
- **Konfigurera via miljövariabel:** Sätt `DATA_ACCESS_PASSWORD` i `.env`-filen
- Lösenordet hashas med SHA-256 för säker lagring
- Säker jämförelse med `hmac.compare_digest()` för att förhindra timing attacks
- Sessionen sparas tills användaren loggar ut eller laddar om sidan

**Hur man använder:**
1. Öppna "Visa Rådata" i dashboarden
2. Ange lösenord i fältet
3. Klicka på "🔓 Avanonymisera"
4. Fullständig data visas när autentiserad
5. Klicka på "🔒 Anonymisera igen" för att logga ut

**Konfigurera eget lösenord:**

*På Streamlit Cloud (produktion):*
1. Gå till https://share.streamlit.io
2. Välj din app → Settings → Secrets
3. Lägg till:
```toml
DATA_ACCESS_PASSWORD = "ditt_säkra_lösenord_här"
```

*Lokalt (utveckling):*
Skapa `.streamlit/secrets.toml`:
```toml
DATA_ACCESS_PASSWORD = "ditt_säkra_lösenord_här"
```

## Rekommenderade Åtgärder för GDPR-Compliance

### 1. **Åtkomstkontroll** 🔐
**Kritiskt:** Dashboarden har för närvarande INGEN användarautentisering.

**Rekommendationer:**
- Implementera Streamlit-autentisering (t.ex. `streamlit-authenticator`)
- Använd Azure AD-integration (ni har redan auth.py)
- Begränsa åtkomst till behöriga användare endast
- Logga alla åtkomster till systemet

**Exempel på implementering:**
```python
# Lägg till i app.py
import streamlit_authenticator as stauth
# eller använd Azure AD via auth.py
```

### 2. **Dataminimering** 📉
- **Nuvarande status:** All data sparas i CSV-fil lokalt
- **Rekommendation:** 
  - Överväg att endast spara aggregerad data (inte individuella personuppgifter)
  - Ta bort personuppgifter som inte behövs för analys
  - Implementera automatisk radering av gamla data (t.ex. efter 2 år)

### 3. **Kryptering** 🔒
- **Nuvarande status:** Data sparas i klartext CSV
- **Rekommendation:**
  - Kryptera CSV-filen på disk
  - Använd krypterad databas istället för CSV
  - Säkerställ att backups är krypterade

### 4. **Datalagring och Säkerhetskopiering** 💾
- **Rekommendation:**
  - Dokumentera var data lagras
  - Säkerställ att backups är säkra och krypterade
  - Implementera automatisk radering enligt bevarandeprincipen

### 5. **Loggning och Övervakning** 📊
- **Rekommendation:**
  - Logga alla åtkomster till personuppgifter
  - Logga vem som hämtat data, när och varför
  - Implementera varningar för misstänkt aktivitet

### 6. **Informationssäkerhet** 🛡️
- **Nuvarande status:** Dashboard körs på Streamlit Community Cloud
- **Implementerat:**
  - ✅ HTTPS används automatiskt (Streamlit Cloud)
  - ✅ Servern hanteras och uppdateras av Streamlit
  - ✅ Environment variables via Streamlit Secrets
  - ✅ Lösenordsskydd för känslig data (Cap Table, rådata)
- **Rekommendation:**
  - Granska regelbundet vem som har access till appen
  - Uppdatera lösenord regelbundet

### 7. **Dokumentation** 📝
- **Rekommendation:**
  - Skapa en register över personuppgiftsbehandlingar (GDPR art. 30)
  - Dokumentera syfte med databehandlingen
  - Dokumentera laglig grund för behandlingen
  - Skapa integritetspolicy för användare

### 8. **Användarrättigheter** 👤
- **Rekommendation:**
  - Implementera funktion för att hantera begäran om radering (GDPR art. 17)
  - Implementera funktion för att exportera data (GDPR art. 20)
  - Informera användare om deras rättigheter

## Ytterligare Säkerhetsförbättringar

### Förbättring av Rådata-visning
✅ **Implementerat:** Anonymisering av känsliga fält

**Ytterligare förbättringar:**
- Lägg till lösenordsskydd för att visa fullständig data
- Implementera rollbaserad åtkomst (t.ex. "viewer" vs "admin")
- Logga när fullständig data visas

### Dataexport
- **Nuvarande status:** HTML-rapport exporteras utan personuppgifter (endast aggregerad data)
- **Rekommendation:** 
  - Säkerställ att exporterade filer inte innehåller personuppgifter
  - Implementera spårning av exporterade filer

## Checklista för GDPR-Compliance

- [x] ~~Implementera användarautentisering~~ → Lösenordsskydd för känslig data
- [x] ~~HTTPS~~ → Streamlit Cloud använder HTTPS automatiskt
- [ ] Kryptera lagrad data
- [ ] Implementera åtkomstloggning
- [ ] Skapa register över personuppgiftsbehandlingar
- [ ] Dokumentera syfte och laglig grund
- [ ] Implementera automatisk radering av gamla data
- [x] ~~Säkerställ säker datalagring~~ → Streamlit Cloud + GitHub Private repo
- [ ] Informera användare om databehandling
- [ ] Implementera funktioner för användarrättigheter
- [ ] Genomför säkerhetsaudit

## Kontakt

Vid frågor om GDPR-compliance, kontakta:
- Er dataskyddsombud (DSO)
- Juridisk avdelning
- IT-säkerhetsavdelning

## Ytterligare Resurser

- [Integritetsskyddsmyndigheten (IMY)](https://www.imy.se/)
- [GDPR Text (EU)](https://gdpr-info.eu/)
- [Streamlit Security Best Practices](https://docs.streamlit.io/knowledge-base/deploy/deploy-securely)

---

**Senast uppdaterad:** 2026-02-10
**Version:** 1.1 (Uppdaterad för Streamlit Cloud)


import os
import msal
import base64
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization, hashes

from secrets_util import get_secret

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class AuthHandler:
    """
    Hanterar autentisering mot Azure Active Directory (AAD) för att erhålla en JWT access token.
    Använder 'Confidential Client' flödet med certifikat.
    """
    def __init__(self):
        # Hämtar konfiguration från .env eller Streamlit Secrets
        self.client_id = get_secret("CLIENT_ID")
        self.tenant_id = get_secret("TENANT_ID")
        self.application_id = get_secret("APPLICATION_ID")
        self.certificate_path = get_secret("CERTIFICATE_PATH")
        self.certificate_password = get_secret("CERTIFICATE_PASSWORD")

        missing = [
            name for name, value in [
                ("CLIENT_ID", self.client_id),
                ("TENANT_ID", self.tenant_id),
                ("APPLICATION_ID", self.application_id),
            ]
            if not value
        ]
        if missing:
            raise ValueError(
                "Följande obligatoriska secrets saknas i Streamlit Cloud "
                f"(eller .env lokalt): {', '.join(missing)}. "
                "Lägg till dem under App → Settings → Secrets."
            )

        # Azure AD endpoint för token-utgivning
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"

        # Definierat Scope enligt Euroclear Vantage dokumentationen
        # .default används för att begära alla behörigheter applikationen är konfigurerad för
        self.scope = [f"https://euroclearb2c01.onmicrosoft.com/{self.application_id}/.default"]

        self.app = None

    def _load_certificate_key(self):
        """
        Laddar privat nyckel och beräknar thumbprint.

        Försöker i ordning:
        1. Läsa .pfx/.pem från disk (CERTIFICATE_PATH – fungerar lokalt).
        2. Avkoda CERTIFICATE_BASE64 från env/Streamlit secrets (fungerar på Streamlit Cloud).

        Returns:
            tuple: (private_key_pem_string, thumbprint_hex_string|None)
        """
        pfx_data = None

        if self.certificate_path and os.path.exists(self.certificate_path):
            file_ext = os.path.splitext(self.certificate_path)[1].lower()

            if file_ext in ['.pem', '.key']:
                with open(self.certificate_path, 'r') as f:
                    return f.read(), None

            if file_ext == '.pfx':
                with open(self.certificate_path, "rb") as f:
                    pfx_data = f.read()
            else:
                raise ValueError(
                    f"Certifikatsformat stöds ej: {file_ext}. Använd .pfx eller .pem"
                )

        if pfx_data is None:
            cert_b64 = get_secret("CERTIFICATE_BASE64")
            if not cert_b64:
                raise FileNotFoundError(
                    "Inget certifikat tillgängligt: varken CERTIFICATE_PATH på disk "
                    "eller CERTIFICATE_BASE64 i Streamlit secrets hittades."
                )
            cert_b64 = cert_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            missing_pad = len(cert_b64) % 4
            if missing_pad:
                cert_b64 += "=" * (4 - missing_pad)
            try:
                pfx_data = base64.b64decode(cert_b64)
            except Exception as e:
                raise ValueError(f"Kunde ej avkoda CERTIFICATE_BASE64: {e}")

        try:
            password = self.certificate_password.encode() if self.certificate_password else None
            private_key, certificate, _additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                password,
            )
        except Exception as e:
            raise Exception(f"Fel vid inläsning av PFX-certifikat: {str(e)}")

        if private_key is None:
            raise ValueError("PFX-data innehåller ingen privat nyckel.")

        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        thumbprint = certificate.fingerprint(hashes.SHA1()).hex() if certificate else None
        return key_pem.decode('utf-8'), thumbprint

    def get_access_token(self):
        """
        Hämtar en giltig access token från Azure AD.
        Hanterar caching automatiskt via MSAL.
        """
        if not self.app:
            # Initiera MSAL applikationen vid första anropet
            private_key, thumbprint = self._load_certificate_key()
            
            client_cred = {"private_key": private_key}
            if thumbprint:
                client_cred["thumbprint"] = thumbprint

            # Skapa ConfidentialClientApplication instance
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=client_cred
            )

        # 1. Försök hämta token från lokal cache (tyst anrop)
        result = self.app.acquire_token_silent(self.scope, account=None)

        if not result:
            # 2. Om ingen giltig token finns i cache, gör ett nytt anrop mot Azure AD
            result = self.app.acquire_token_for_client(scopes=self.scope)

        if not isinstance(result, dict):
            raise Exception(
                f"Oväntat svar från MSAL ({type(result).__name__}). "
                "Kontrollera CLIENT_ID, TENANT_ID och APPLICATION_ID."
            )

        if "access_token" in result:
            return result["access_token"]

        # Fånga och kasta vidare eventuella fel från MSAL
        error_description = result.get("error_description", result.get("error", "Okänt fel"))
        raise Exception(f"Kunde ej hämta access token: {error_description}")

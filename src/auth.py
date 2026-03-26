import os
import msal
import base64
import hashlib
from dotenv import load_dotenv
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization, hashes

load_dotenv()


def _get_secret(key: str, default=None):
    """Hämtar värde från miljövariabel, med fallback till st.secrets (Streamlit Cloud)."""
    value = os.getenv(key)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


class AuthHandler:
    """
    Hanterar autentisering mot Azure Active Directory (AAD) för att erhålla en JWT access token.
    Använder 'Confidential Client' flödet med certifikat.

    Credentials läses från miljövariabler (.env lokalt) med automatisk fallback
    till Streamlit Cloud Secrets när env saknas.
    """
    def __init__(self):
        self.client_id = _get_secret("CLIENT_ID")
        self.tenant_id = _get_secret("TENANT_ID")
        self.application_id = _get_secret("APPLICATION_ID")
        self.certificate_path = _get_secret("CERTIFICATE_PATH")
        self.certificate_password = _get_secret("CERTIFICATE_PASSWORD")

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = [f"https://euroclearb2c01.onmicrosoft.com/{self.application_id}/.default"]

        self.app = None

    def _load_certificate_key(self):
        """
        Laddar privat nyckel och beräknar thumbprint.

        Försöker i ordning:
        1. Läsa .pfx/.pem från disk (CERTIFICATE_PATH – fungerar lokalt)
        2. Avkoda CERTIFICATE_BASE64 från Streamlit secrets (fungerar på Cloud)
        """
        pfx_data = None

        # 1) Fil på disk
        if self.certificate_path and os.path.exists(self.certificate_path):
            file_ext = os.path.splitext(self.certificate_path)[1].lower()
            if file_ext in ['.pem', '.key']:
                with open(self.certificate_path, 'r') as f:
                    return f.read(), None
            with open(self.certificate_path, "rb") as f:
                pfx_data = f.read()

        # 2) Base64-secret (Streamlit Cloud)
        if pfx_data is None:
            cert_b64 = _get_secret("CERTIFICATE_BASE64")
            if not cert_b64:
                raise FileNotFoundError(
                    "Inget certifikat tillgängligt: varken CERTIFICATE_PATH på disk "
                    "eller CERTIFICATE_BASE64 i Streamlit secrets hittades."
                )
            cert_b64 = cert_b64.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            missing_pad = len(cert_b64) % 4
            if missing_pad:
                cert_b64 += "=" * (4 - missing_pad)
            pfx_data = base64.b64decode(cert_b64)

        password = self.certificate_password.encode() if self.certificate_password else None

        private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_data, password)

        if private_key is None:
            raise ValueError("Certifikatet innehåller ingen privat nyckel.")

        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        thumbprint = certificate.fingerprint(hashes.SHA1()).hex() if certificate else None
        return key_pem.decode('utf-8'), thumbprint

    def get_access_token(self):
        """Hämtar en giltig access token från Azure AD. Cachas automatiskt via MSAL."""
        if not self.app:
            private_key, thumbprint = self._load_certificate_key()

            client_cred = {"private_key": private_key}
            if thumbprint:
                client_cred["thumbprint"] = thumbprint

            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=client_cred
            )

        result = self.app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            return result["access_token"]

        error_description = result.get("error_description", result.get("error", "Okänt fel"))
        raise Exception(f"Kunde ej hämta access token: {error_description}")

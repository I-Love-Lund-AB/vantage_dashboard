import os
import msal
import base64
import hashlib
from dotenv import load_dotenv
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization, hashes

# Ladda miljövariabler från .env filen
load_dotenv()

class AuthHandler:
    """
    Hanterar autentisering mot Azure Active Directory (AAD) för att erhålla en JWT access token.
    Använder 'Confidential Client' flödet med certifikat.
    """
    def __init__(self):
        # Hämtar konfiguration från miljövariabler
        self.client_id = os.getenv("CLIENT_ID")
        self.tenant_id = os.getenv("TENANT_ID")
        self.application_id = os.getenv("APPLICATION_ID")
        self.certificate_path = os.getenv("CERTIFICATE_PATH")
        self.certificate_password = os.getenv("CERTIFICATE_PASSWORD")
        
        # Azure AD endpoint för token-utgivning
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        # Definierat Scope enligt Euroclear Vantage dokumentationen
        # .default används för att begära alla behörigheter applikationen är konfigurerad för
        self.scope = [f"https://euroclearb2c01.onmicrosoft.com/{self.application_id}/.default"]
        
        self.app = None

    def _load_certificate_key(self):
        """
        Laddar privat nyckel och beräknar thumbprint från certifikatfilen.
        
        Stödjer .pfx (PKCS#12) och .pem filer.
        
        Returns:
            tuple: (private_key_pem_string, thumbprint_hex_string)
        """
        if not self.certificate_path or not os.path.exists(self.certificate_path):
            raise FileNotFoundError(f"Certifikat hittades ej på sökväg: {self.certificate_path}")

        file_ext = os.path.splitext(self.certificate_path)[1].lower()

        if file_ext == '.pfx':
            try:
                with open(self.certificate_path, "rb") as f:
                    pfx_data = f.read()
                
                # Om lösenord finns, koda det till bytes
                password = self.certificate_password.encode() if self.certificate_password else None
                
                # Extrahera nyckel och certifikat från PFX-filen
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data, 
                    password
                )
                
                if private_key is None:
                    raise ValueError("PFX-filen innehåller ingen privat nyckel.")

                # Serialisera nyckeln till PEM-format (krävs av MSAL Python)
                key_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                # Beräkna SHA-1 Thumbprint (krävs ofta av Azure AD för att identifiera certifikatet)
                if certificate:
                    thumbprint = certificate.fingerprint(hashes.SHA1()).hex()
                else:
                    thumbprint = None

                return key_pem.decode('utf-8'), thumbprint
                
            except Exception as e:
                raise Exception(f"Fel vid inläsning av PFX-certifikat: {str(e)}")
        
        elif file_ext in ['.pem', '.key']:
            # Fallback för rena PEM-filer - thumbprint kan behöva hanteras manuellt om det krävs
            with open(self.certificate_path, 'r') as f:
                return f.read(), None
        
        else:
            raise ValueError(f"Certifikatsformat stöds ej: {file_ext}. Använd .pfx eller .pem")

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

        if "access_token" in result:
            return result["access_token"]
        else:
            # Fånga och kasta vidare eventuella fel från MSAL
            error_description = result.get("error_description", result.get("error", "Okänt fel"))
            raise Exception(f"Kunde ej hämta access token: {error_description}")

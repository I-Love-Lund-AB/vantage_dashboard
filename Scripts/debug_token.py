"""
Debug Script för Euroclear Vantage API
Detta script hjälper dig att felsöka token-generering och visa token-innehållet.
"""
import os
import sys
import json
import base64
from dotenv import load_dotenv

# Fix encoding för Windows terminal
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# Lägg till src till path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from auth import AuthHandler
from api import VantageClient

# Ladda miljövariabler
load_dotenv()

def decode_jwt_payload(token):
    """
    Avkodar JWT-payload utan att verifiera signaturen.
    Användbart för att inspektera token-innehållet.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        print(f"Kunde ej avkoda token: {e}")
        return None

def main():
    print("=" * 60)
    print("EUROCLEAR VANTAGE API - DEBUG INFORMATION")
    print("=" * 60)
    print()
    
    print("KONFIGURATION:")
    print(f"  CLIENT_ID: {os.getenv('CLIENT_ID')}")
    print(f"  TENANT_ID: {os.getenv('TENANT_ID')}")
    print(f"  APPLICATION_ID: {os.getenv('APPLICATION_ID')}")
    print(f"  CERTIFICATE_PATH: {os.getenv('CERTIFICATE_PATH')}")
    print()
    
    try:
        print("Forsoker hama token...")
        auth = AuthHandler()
        token = auth.get_access_token()
        
        print("[OK] Token genererad framgangsrikt!")
        print()
        
        token_preview = f"{token[:50]}...{token[-50:]}"
        print(f"TOKEN (forhandsvisning): {token_preview}")
        print()
        
        payload = decode_jwt_payload(token)
        if payload:
            print("TOKEN-INNEHALL (Payload):")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print()
            
            print("VIKTIGA CLAIMS:")
            print(f"  Audience (aud): {payload.get('aud', 'N/A')}")
            print(f"  Issuer (iss): {payload.get('iss', 'N/A')}")
            print(f"  App ID (azp): {payload.get('azp', 'N/A')}")
            print(f"  Expires (exp): {payload.get('exp', 'N/A')}")
            if 'roles' in payload:
                print(f"  Roles: {payload.get('roles', 'N/A')}")
            print()
        
        print("=" * 60)
        print("TESTAR API-ANROP:")
        print("=" * 60)
        print()
        
        client = VantageClient()
        
        print("1. Testar /issuermetadata...")
        try:
            issuers = client.get_issuer_metadata()
            print(f"   [OK] SUCCESS! Hittade {len(issuers)} bolag.")
            if issuers:
                print(f"   Response (forsta bolaget): {json.dumps(issuers[0], indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"   [FAIL] FAILED: {e}")
        
        print()
        print("2. Testar /completeregister (datum: 2025-12-30, ISIN: SE0018397648)...")
        try:
            data = client.get_complete_register("SE0018397648", "2025-12-30")
            if data:
                print(f"   [OK] SUCCESS! Hittade data.")
                print(f"   Holdings count: {len(data.get('holdings', []))}")
            else:
                print(f"   [WARN] No Content (204) - Inga data for detta datum.")
        except Exception as e:
            print(f"   [FAIL] FAILED: {e}")
        
        print()
        print("=" * 60)
        print("FULLSTANDIG TOKEN (kopiera denna till Euroclear):")
        print("=" * 60)
        print(token)
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] FEL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

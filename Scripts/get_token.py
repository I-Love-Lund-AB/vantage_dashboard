"""
Enkelt script för att snabbt hämta en token att kopiera till Postman.
Kör: python get_token.py
"""
import os
import sys

# Fix encoding
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from dotenv import load_dotenv
from auth import AuthHandler

load_dotenv()

def main():
    print("=" * 70)
    print("HÄMTA TOKEN FÖR POSTMAN")
    print("=" * 70)
    print()
    
    try:
        auth = AuthHandler()
        token = auth.get_access_token()
        
        print("[OK] Token genererad!")
        print()
        print("=" * 70)
        print("KOPIERA DENNA TOKEN TILL POSTMAN:")
        print("=" * 70)
        print()
        print(token)
        print()
        print("=" * 70)
        print()
        print("Instruktioner:")
        print("1. Kopiera token-strängen ovan")
        print("2. I Postman: Authorization > Type: Bearer Token")
        print("3. Klistra in token i fältet")
        print("4. Testa URL: https://vantage-api.euroclear.com/anz/api/external/issuermetadata")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"[FEL] Kunde ej hämta token: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


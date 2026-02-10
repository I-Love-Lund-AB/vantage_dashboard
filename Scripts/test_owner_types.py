"""
Testscript för att testa identifiering av fysiska vs juridiska personer.
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Lägg till src till path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api import VantageClient
from app import is_personnummer

# Ladda miljövariabler
load_dotenv()

ISIN = "SE0018397648"
HOLDING_DATE = "2025-12-30"

def test_identification():
    """Testar identifiering av ägartyper."""
    try:
        print("Hamtar data...")
        client = VantageClient()
        response_data = client.get_complete_register(ISIN, HOLDING_DATE)
        
        if not response_data or 'holdings' not in response_data:
            print("Ingen data hittades.")
            return
        
        holdings = response_data['holdings']
        print(f"Hittade {len(holdings)} aktieagare.\n")
        
        # Testa identifiering
        results = {
            'Fysisk person': [],
            'Juridisk person': [],
            'Okant': []
        }
        
        for holding in holdings[:50]:  # Testa första 50
            pnr_orgnr = holding.get('pnrOrgnr', '')
            name = holding.get('name', '')
            is_person = is_personnummer(pnr_orgnr)
            
            if is_person is True:
                results['Fysisk person'].append((name, pnr_orgnr))
            elif is_person is False:
                results['Juridisk person'].append((name, pnr_orgnr))
            else:
                results['Okant'].append((name, pnr_orgnr))
        
        print("=" * 70)
        print("RESULTAT:")
        print("=" * 70)
        print(f"Fysiska personer: {len(results['Fysisk person'])}")
        print(f"Juridiska personer: {len(results['Juridisk person'])}")
        print(f"Okanta: {len(results['Okant'])}")
        print()
        
        print("Exempel på Fysiska personer:")
        for name, pnr in results['Fysisk person'][:5]:
            print(f"  {name}: {pnr}")
        print()
        
        print("Exempel på Juridiska personer:")
        for name, pnr in results['Juridisk person'][:5]:
            print(f"  {name}: {pnr}")
        print()
        
        print("Exempel på Okanta:")
        for name, pnr in results['Okant'][:10]:
            print(f"  {name}: {pnr}")
        
    except Exception as e:
        print(f"Fel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_identification()


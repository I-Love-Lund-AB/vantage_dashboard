"""
Testscript för att undersöka varför historisk data innan 2024 inte hämtas.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ladda miljövariabler
load_dotenv()

# Lägg till src till path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api import VantageClient

# ISIN för I Love Lund AB
ISIN = "SE0018397648"

def test_date_range():
    """Testar att hämta data för olika datum för att se var problemet ligger."""
    try:
        client = VantageClient()
        print("[OK] API-klient initierad")
    except Exception as e:
        print(f"[ERROR] Kunde inte initiera API-klient: {e}")
        return
    
    # Testa datum från 2017 till nu
    test_dates = []
    today = datetime.today()
    
    # Testa sista dagen varje månad från januari 2017
    for year in range(2017, today.year + 1):
        for month in range(1, 13):
            if year == today.year and month > today.month:
                break
            
            # Sista dagen i månaden
            if month == 12:
                last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Gå bakåt till sista vardagen
            while last_day.weekday() >= 5:  # 5 = lördag, 6 = söndag
                last_day -= timedelta(days=1)
            
            test_dates.append(last_day)
    
    print(f"\nTestar {len(test_dates)} datum fran 2017 till nu...")
    print("=" * 80)
    
    results = {
        'success': [],
        'no_data': [],
        'errors': []
    }
    
    # Testa var 3:e månad för att gå snabbare (kan ändras till alla om behövs)
    for i, test_date in enumerate(test_dates[::3]):  # Var 3:e månad
        date_str = test_date.strftime("%Y-%m-%d")
        
        try:
            response = client.get_complete_register(ISIN, date_str)
            
            if response and 'holdings' in response:
                holdings_count = len(response.get('holdings', []))
                results['success'].append((date_str, holdings_count))
                print(f"[OK] {date_str}: {holdings_count} aktieagare")
            else:
                results['no_data'].append(date_str)
                print(f"[NO DATA] {date_str}: Ingen data (204 No Content)")
        
        except Exception as e:
            results['errors'].append((date_str, str(e)))
            print(f"[ERROR] {date_str}: Fel - {str(e)[:60]}")
    
    # Sammanfattning
    print("\n" + "=" * 80)
    print("SAMMANFATTNING:")
    print(f"[OK] Lyckade hamtningar: {len(results['success'])}")
    print(f"[NO DATA] Inga data (204): {len(results['no_data'])}")
    print(f"[ERROR] Fel: {len(results['errors'])}")
    
    if results['success']:
        print(f"\n[OK] Forsta datum med data: {results['success'][0][0]} ({results['success'][0][1]} aktieagare)")
        print(f"[OK] Sista datum med data: {results['success'][-1][0]} ({results['success'][-1][1]} aktieagare)")
    
    if results['no_data']:
        print(f"\n[NO DATA] Forsta datum utan data: {results['no_data'][0]}")
        print(f"[NO DATA] Sista datum utan data: {results['no_data'][-1]}")
    
    if results['errors']:
        print(f"\n[ERROR] Fel vid foljande datum:")
        for date_str, error in results['errors'][:5]:  # Visa första 5 felen
            print(f"   {date_str}: {error}")

def check_available_dates():
    """Använder isinmetadata för att se vilka datum som finns tillgängliga."""
    try:
        client = VantageClient()
        print("[OK] API-klient initierad")
    except Exception as e:
        print(f"[ERROR] Kunde inte initiera API-klient: {e}")
        return
    
    # Försök hämta metadata - behöver organisationsnummer
    # ISIN: SE0018397648 för I Love Lund AB
    # Vi kan försöka hämta metadata via issuer metadata först
    print("\nForsoker hamta tillgangliga datum via metadata...")
    
    try:
        # Försök hämta issuer metadata
        metadata = client.get_issuer_metadata()
        print(f"[OK] Hamtade issuer metadata")
        print(f"Data struktur: {list(metadata.keys()) if isinstance(metadata, dict) else type(metadata)}")
        
        # Metadata kan vara en lista direkt eller en dict med 'metaData'
        if isinstance(metadata, list):
            metadata_list = metadata
        elif isinstance(metadata, dict) and 'metaData' in metadata:
            metadata_list = metadata['metaData']
        elif isinstance(metadata, dict):
            metadata_list = [metadata]
        else:
            metadata_list = []
        
        print(f"Metadata struktur: {type(metadata)}, antal issuers: {len(metadata_list)}")
        
        # Sök efter vårt ISIN i metadata
        for issuer in metadata_list:
            if not isinstance(issuer, dict):
                continue
            for isin_data in issuer.get('isinData', []):
                if isin_data.get('isin') == ISIN:
                    print(f"\n[OK] Hittade ISIN {ISIN} i metadata!")
                    for api_data in isin_data.get('apiData', []):
                        if api_data.get('apiType') == 'completeregister':
                            available_dates = api_data.get('availableDates', [])
                            print(f"\nTillgangliga datum for completeregister: {len(available_dates)}")
                            for date in available_dates[:20]:  # Visa första 20
                                print(f"   - {date}")
                            if len(available_dates) > 20:
                                print(f"   ... och {len(available_dates) - 20} fler")
                            return available_dates
    
    except Exception as e:
        print(f"[WARNING] Kunde inte hamta metadata: {e}")
        print("Fortsatter med direkt test av datum...")

if __name__ == "__main__":
    print("Undersoker varfor historisk data innan 2024 inte hamtas\n")
    
    # Först försök hämta tillgängliga datum via metadata
    available_dates = check_available_dates()
    
    # Om metadata inte fungerar, testa datum direkt
    if not available_dates:
        print("\n" + "=" * 80)
        print("Testar datum direkt...")
        test_date_range()
    else:
        print("\n" + "=" * 80)
        print("Testar de datum som metadata säger finns tillgängliga...")
        # Testa de datum som metadata visar


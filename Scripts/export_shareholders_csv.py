"""
Script för att exportera aktieägardata till CSV-fil.
Hämtar alla aktieägare med deras vote percentage, holding percentage och namn
för ett specifikt datum.
"""
import os
import sys
import csv
from dotenv import load_dotenv

# Lägg till src till path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api import VantageClient

# Ladda miljövariabler
load_dotenv()

# Hårdkodat ISIN (samma som i app.py)
ISIN = "SE0018397648"

# Datum för export
HOLDING_DATE = "2025-12-30"

def export_shareholders_to_csv(output_file="aktieagare_2025-12-30.csv"):
    """
    Hämtar aktieägardata från Vantage API och exporterar till CSV.
    
    Args:
        output_file (str): Filnamn för CSV-filen
    """
    try:
        print(f"Hämtar aktieägardata för {HOLDING_DATE}...")
        client = VantageClient()
        
        # Hämta data från API
        response_data = client.get_complete_register(ISIN, HOLDING_DATE)
        
        if not response_data:
            print(f"VARNING: Ingen data hittades for {HOLDING_DATE}.")
            print("API:et returnerade 204 No Content - data finns inte for detta datum.")
            return False
        
        if 'holdings' not in response_data:
            print("VARNING: Ovanligt svarsformat - 'holdings' saknas i responsen.")
            return False
        
        holdings = response_data['holdings']
        
        if not holdings:
            print(f"VARNING: Inga aktieagare hittades for {HOLDING_DATE}.")
            return False
        
        print(f"Hittade {len(holdings)} aktieägare.")
        print(f"Exporterar till {output_file}...")
        
        # Skapa CSV-fil
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Namn', 'Holding Percentage', 'Vote Percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Skriv header
            writer.writeheader()
            
            # Skriv varje aktieägare
            for holding in holdings:
                writer.writerow({
                    'Namn': holding.get('name', ''),
                    'Holding Percentage': holding.get('holdingsPercentage', 0),
                    'Vote Percentage': holding.get('votesPercentage', 0)
                })
        
        print(f"OK: Exporterade {len(holdings)} aktieagare till {output_file}")
        return True
        
    except ValueError as e:
        print(f"FEL: Konfigurationsfel: {e}")
        print("Kontrollera att VANTAGE_API_URL ar satt i .env-filen.")
        return False
    except Exception as e:
        print(f"FEL: Fel vid export: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Standardfilnamn baserat på datumet
    output_filename = f"aktieagare_{HOLDING_DATE.replace('-', '_')}.csv"
    
    # Om ett filnamn anges som argument, använd det
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    
    success = export_shareholders_to_csv(output_filename)
    
    if success:
        print("\n" + "="*60)
        print("Export klar!")
        print("="*60)
    else:
        sys.exit(1)


"""
Beräknar hur stor del av ägandet som aktieägare med minst 500 aktier står för.
"""
import os
import sys
from dotenv import load_dotenv

# Lägg till src till path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api import VantageClient

# Ladda miljövariabler
load_dotenv()

# Hårdkodat ISIN (samma som i app.py)
ISIN = "SE0018397648"

# Datum för analys
HOLDING_DATE = "2025-12-30"

# Minsta antal aktier för att räknas med
MIN_SHARES = 500

def calculate_ownership_500plus():
    """
    Beräknar ägandet för aktieägare med minst 500 aktier.
    """
    try:
        print(f"Hamtar aktieagardata for {HOLDING_DATE}...")
        client = VantageClient()
        
        # Hämta data från API
        response_data = client.get_complete_register(ISIN, HOLDING_DATE)
        
        if not response_data:
            print(f"VARNING: Ingen data hittades for {HOLDING_DATE}.")
            return None
        
        if 'holdings' not in response_data:
            print("VARNING: Ovanligt svarsformat - 'holdings' saknas i responsen.")
            return None
        
        # Hämta totalt antal utestående aktier
        issued_quantity = response_data.get('issuedQuantity', 0)
        holdings = response_data['holdings']
        
        if not holdings:
            print(f"VARNING: Inga aktieagare hittades for {HOLDING_DATE}.")
            return None
        
        print(f"Totalt antal utestande aktier: {issued_quantity:,.0f}")
        print(f"Totalt antal aktieagare: {len(holdings)}")
        print()
        
        # Filtrera aktieägare med minst 500 aktier
        shareholders_500plus = []
        total_shares_500plus = 0
        total_holding_percentage_500plus = 0
        total_vote_percentage_500plus = 0
        
        for holding in holdings:
            holdings_quantity = holding.get('holdingsQuantity', 0)
            holdings_percentage = holding.get('holdingsPercentage', 0)
            votes_percentage = holding.get('votesPercentage', 0)
            name = holding.get('name', 'Okänt namn')
            
            if holdings_quantity >= MIN_SHARES:
                shareholders_500plus.append({
                    'name': name,
                    'shares': holdings_quantity,
                    'holding_percentage': holdings_percentage,
                    'vote_percentage': votes_percentage
                })
                total_shares_500plus += holdings_quantity
                total_holding_percentage_500plus += holdings_percentage
                total_vote_percentage_500plus += votes_percentage
        
        # Beräkna andel av totalt ägande
        ownership_percentage = (total_shares_500plus / issued_quantity * 100) if issued_quantity > 0 else 0
        
        # Presentera resultat
        print("=" * 70)
        print("RESULTAT: Aktieagare med minst 500 aktier")
        print("=" * 70)
        print()
        print(f"Antal aktieagare med >= {MIN_SHARES} aktier: {len(shareholders_500plus)}")
        print(f"Totalt antal aktier hos dessa: {total_shares_500plus:,.0f}")
        print()
        print(f"Andel av alla utestande aktier: {ownership_percentage:.2f}%")
        print(f"Sammanlagd holding percentage: {total_holding_percentage_500plus:.2f}%")
        print(f"Sammanlagd vote percentage: {total_vote_percentage_500plus:.2f}%")
        print()
        
        # Visa de största ägarna
        shareholders_500plus_sorted = sorted(shareholders_500plus, key=lambda x: x['shares'], reverse=True)
        
        print("=" * 70)
        print(f"Topp 20 aktieagare med minst {MIN_SHARES} aktier:")
        print("=" * 70)
        print(f"{'Namn':<40} {'Aktier':>15} {'Holding %':>12} {'Vote %':>12}")
        print("-" * 70)
        
        for i, shareholder in enumerate(shareholders_500plus_sorted[:20], 1):
            name = shareholder['name'][:38]  # Trunkera långa namn
            shares = shareholder['shares']
            holding_pct = shareholder['holding_percentage']
            vote_pct = shareholder['vote_percentage']
            print(f"{i:2}. {name:<38} {shares:>15,.0f} {holding_pct:>11.4f}% {vote_pct:>11.4f}%")
        
        if len(shareholders_500plus_sorted) > 20:
            print(f"\n... och {len(shareholders_500plus_sorted) - 20} fler aktieagare med >= {MIN_SHARES} aktier")
        
        print()
        print("=" * 70)
        
        return {
            'issued_quantity': issued_quantity,
            'total_shareholders': len(holdings),
            'shareholders_500plus_count': len(shareholders_500plus),
            'total_shares_500plus': total_shares_500plus,
            'ownership_percentage': ownership_percentage,
            'total_holding_percentage': total_holding_percentage_500plus,
            'total_vote_percentage': total_vote_percentage_500plus
        }
        
    except ValueError as e:
        print(f"FEL: Konfigurationsfel: {e}")
        print("Kontrollera att VANTAGE_API_URL ar satt i .env-filen.")
        return None
    except Exception as e:
        print(f"FEL: Fel vid berakning: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = calculate_ownership_500plus()
    
    if result:
        print("\nBerakning klar!")
    else:
        sys.exit(1)


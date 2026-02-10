"""
Skapar ägarstruktur-fil med korrekta totaler (inkl. A- och B-aktier)
"""
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import sys
sys.path.insert(0, 'src')
from api import VantageClient
from config import ISIN_A, ISIN_B, VOTES_PER_A_SHARE, VOTES_PER_B_SHARE

client = VantageClient()
holding_date = '2025-12-30'

# Hämta A och B aktier
print('Hämtar A-aktier...')
a_data = client.get_complete_register(ISIN_A, holding_date)
a_df = pd.DataFrame(a_data['holdings'])
a_df['shareClass'] = 'A'

print('Hämtar B-aktier...')
b_data = client.get_complete_register(ISIN_B, holding_date)
b_df = pd.DataFrame(b_data['holdings'])
b_df['shareClass'] = 'B'

# Kombinera och aggregera per ägare
combined = pd.concat([a_df, b_df], ignore_index=True)

# Separera A och B per ägare
a_shares = combined[combined['shareClass'] == 'A'].groupby('pnrOrgnr')['holdingsQuantity'].sum()
b_shares = combined[combined['shareClass'] == 'B'].groupby('pnrOrgnr')['holdingsQuantity'].sum()

# Skapa DataFrame med alla ägare
all_owners = pd.DataFrame(index=combined['pnrOrgnr'].unique())
all_owners['A_aktier'] = a_shares.reindex(all_owners.index).fillna(0).astype(int)
all_owners['B_aktier'] = b_shares.reindex(all_owners.index).fillna(0).astype(int)
all_owners['Totalt_aktier'] = all_owners['A_aktier'] + all_owners['B_aktier']

# Storleksklasser
bins = [0, 50, 100, 200, 300, 400, 500, float('inf')]
labels = ['Under 50', '51-100', '101-200', '201-300', '301-400', '401-500', '500+']
all_owners['Storleksklass'] = pd.cut(all_owners['Totalt_aktier'], bins=bins, labels=labels, right=True)

# Aggregera per storleksklass
summary = []
for label in labels:
    group = all_owners[all_owners['Storleksklass'] == label]
    summary.append({
        'Storleksklass': label,
        'Antal aktier': group['Totalt_aktier'].sum(),
        'Antal ägare': len(group),
    })

result = pd.DataFrame(summary)

# Beräkna procent
total_aktier = all_owners['Totalt_aktier'].sum()
total_agare = len(all_owners)
result['% av aktier'] = (result['Antal aktier'] / total_aktier * 100).round(1).astype(str) + '%'
result['% av ägare'] = (result['Antal ägare'] / total_agare * 100).round(1).astype(str) + '%'

# Ordna kolumner
result = result[['Storleksklass', 'Antal aktier', 'Antal ägare', '% av aktier', '% av ägare']]

# Lägg till totalrad
total_row = pd.DataFrame([{
    'Storleksklass': 'Totalt',
    'Antal aktier': int(total_aktier),
    'Antal ägare': total_agare,
    '% av aktier': '100.0%',
    '% av ägare': '100.0%'
}])
result = pd.concat([result, total_row], ignore_index=True)

# Lägg till källhänvisning
source_row = pd.DataFrame([{
    'Storleksklass': 'Källa: Euroclear Sweden AB 30 december 2025',
    'Antal aktier': None,
    'Antal ägare': None,
    '% av aktier': None,
    '% av ägare': None
}])
result = pd.concat([result, source_row], ignore_index=True)

print("\nÄgarstruktur 2025 (inkl. A- och B-aktier):")
print(result.to_string(index=False))
print()
print(f"Totalt antal A-aktier: {a_df['holdingsQuantity'].sum():,}")
print(f"Totalt antal B-aktier: {b_df['holdingsQuantity'].sum():,}")
print(f"Totalt antal aktier: {int(total_aktier):,}")
print(f"Totalt antal ägare: {total_agare}")

# Spara till Excel
output_file = 'output/agarstruktur_2025-12-30_2.xlsx'
result.to_excel(output_file, index=False, sheet_name='Ägarstruktur 2025')
print(f"\nSparad till: {output_file}")



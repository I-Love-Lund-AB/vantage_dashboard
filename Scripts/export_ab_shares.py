"""
Script för att exportera aktieägarlista med A- och B-aktier.
"""
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.insert(0, 'src')
from api import VantageClient
import pandas as pd

def main():
    client = VantageClient()
    
    # ISIN för A och B aktier
    ISIN_A = "SE0018397630"  # A-aktier (10 röster)
    ISIN_B = "SE0018397648"  # B-aktier (1 röst)
    
    holding_date = "2025-12-30"
    
    # Hämta B-aktier
    print(f"Hämtar B-aktier för {holding_date}...")
    b_data = client.get_complete_register(ISIN_B, holding_date)
    print(f"B-aktier: {len(b_data['holdings'])} ägare")
    
    # Hämta A-aktier
    print(f"Hämtar A-aktier för {holding_date}...")
    a_data = client.get_complete_register(ISIN_A, holding_date)
    print(f"A-aktier: {len(a_data['holdings'])} ägare")
    
    # Skapa DataFrames
    b_df = pd.DataFrame(b_data['holdings'])
    b_df = b_df.rename(columns={'holdingsQuantity': 'B_aktier'})
    b_df = b_df[['pnrOrgnr', 'name', 'B_aktier']]
    
    a_df = pd.DataFrame(a_data['holdings'])
    a_df = a_df.rename(columns={'holdingsQuantity': 'A_aktier'})
    a_df = a_df[['pnrOrgnr', 'name', 'A_aktier']]
    
    # Merge på personnr/orgnr
    merged = pd.merge(b_df, a_df, on=['pnrOrgnr', 'name'], how='outer')
    merged = merged.fillna(0)
    merged['A_aktier'] = merged['A_aktier'].astype(int)
    merged['B_aktier'] = merged['B_aktier'].astype(int)
    
    # Beräkna totalt
    merged['Totalt_aktier'] = merged['A_aktier'] + merged['B_aktier']
    merged['Totalt_roster'] = merged['A_aktier'] * 10 + merged['B_aktier']
    
    # Totaler för bolaget
    total_a = a_data.get('issuedQuantity', 13250)
    total_b = b_data.get('issuedQuantity', 417457)
    total_aktier = total_a + total_b
    total_roster = total_a * 10 + total_b
    
    print(f"\nBolagets totaler:")
    print(f"  A-aktier: {total_a:,} (10 röster/st)")
    print(f"  B-aktier: {total_b:,} (1 röst/st)")
    print(f"  Totalt aktier: {total_aktier:,}")
    print(f"  Totalt röster: {total_roster:,}")
    
    # Beräkna procent
    merged['Agarandel_%'] = (merged['Totalt_aktier'] / total_aktier * 100).round(4)
    merged['Rostandel_%'] = (merged['Totalt_roster'] / total_roster * 100).round(4)
    
    # Sortera efter ägarandel (störst först)
    merged = merged.sort_values('Totalt_aktier', ascending=False)
    merged = merged.reset_index(drop=True)
    merged.insert(0, 'Rang', range(1, len(merged) + 1))
    
    # Välj och namnge kolumner
    result = merged[['Rang', 'name', 'A_aktier', 'B_aktier', 'Totalt_aktier', 'Totalt_roster', 'Agarandel_%', 'Rostandel_%']]
    result.columns = ['Rang', 'Namn', 'A-aktier', 'B-aktier', 'Totalt aktier', 'Totalt röster', 'Ägarandel (%)', 'Röstandel (%)']
    
    # Exportera till Excel
    output_file = f'output/aktieagarlista_{holding_date}_med_AB.xlsx'
    result.to_excel(output_file, index=False, sheet_name='Aktieägare')
    
    print(f"\nExporterad till: {output_file}")
    print(f"   Antal ägare: {len(result)}")
    print(f"\nTopp 20 ägare:")
    print(result.head(20).to_string(index=False))

if __name__ == "__main__":
    main()


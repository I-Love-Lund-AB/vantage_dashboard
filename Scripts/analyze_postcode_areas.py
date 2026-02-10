"""
Script för att analysera befintlig data och extrahera vanligaste gatorna
per postnummerområde i Lund.
"""
import pandas as pd
import json
import os
from collections import Counter
import re

def clean_street_name(street):
    """Rensar och normaliserar gatuadresser."""
    if pd.isna(street) or street == '' or str(street).lower() == 'nan':
        return None
    
    street_str = str(street).strip()
    
    # Ta bort vanliga prefix/suffix som kan variera
    # Exempel: "Storgatan 1" -> "Storgatan", "Kungsgatan 10 LGH" -> "Kungsgatan"
    
    # Ta bort lägenhetsnummer och liknande (LGH, A, B, C, etc.)
    street_str = re.sub(r'\s+\d+\s*[A-Za-z]\s*[Ll][Gg][Hh]\.?\s*$', '', street_str, flags=re.IGNORECASE)
    street_str = re.sub(r'\s+[Ll][Gg][Hh]\.?\s*$', '', street_str, flags=re.IGNORECASE)
    street_str = re.sub(r'\s+\d+\s*[A-Za-z]\s*$', '', street_str)  # Ta bort "10 A", "15 B" etc.
    street_str = re.sub(r'\s+\d+[A-Za-z]?$', '', street_str)  # Ta bort husnummer
    street_str = re.sub(r'\s+\d+\s*$', '', street_str)  # Ta bort ensamma nummer
    
    # Ta bort vanliga suffix (men behåll dem om de är viktiga)
    # street_str = re.sub(r'\s+[Vv][Ää][Gg]\.?\s*$', '', street_str)  # Ta bort "väg"
    # street_str = re.sub(r'\s+[Gg][Aa][Tt][Aa][Nn]\.?\s*$', '', street_str)  # Ta bort "gatan"
    
    # Ta bort extra whitespace
    street_str = ' '.join(street_str.split())
    
    # Filtrera bort uppenbart felaktiga värden
    if street_str.upper() in ['BOX', 'BOX ', 'NONE', 'NULL', '']:
        return None
    
    return street_str if street_str else None

def extract_area_name(street):
    """Försöker extrahera områdesnamn från gatuadresser."""
    if not street:
        return None
    
    street_str = str(street).strip()
    
    # Vanliga områdesnamn i Lund
    area_keywords = [
        'centrum', 'fäladen', 'linero', 'gunnesbo', 'klostergården',
        'nöbbelöv', 'dalby', 'ideon', 'max', 'brunnshög', 'norra fäladen',
        'södra fäladen', 'kobjer', 'kobjers', 'kobjersgatan'
    ]
    
    street_lower = street_str.lower()
    for keyword in area_keywords:
        if keyword in street_lower:
            return keyword.title()
    
    return None

def analyze_postcode_areas(data_file="data/shareholders_history.csv", output_file="data/postcode_areas.json"):
    """
    Analyserar befintlig data för att hitta vanligaste gatorna per postnummerområde.
    Räknar endast aktieägare från senaste datumet för att få aktuell fördelning.
    
    Args:
        data_file: Sökväg till CSV-filen med aktieägardata
        output_file: Sökväg där resultatet ska sparas (JSON)
    """
    print("Laddar data...")
    
    if not os.path.exists(data_file):
        print(f"Fel: Datafilen {data_file} hittades inte!")
        return None
    
    df = pd.read_csv(data_file)
    
    if df.empty:
        print("Datafilen är tom!")
        return None
    
    print(f"Laddade {len(df)} rader data")
    
    # Filtrera på senaste datumet för att bara räkna aktuella aktieägare
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        latest_date = df['date'].max()
        df = df[df['date'] == latest_date].copy()
        print(f"Filtrerar på senaste datumet: {latest_date.strftime('%Y-%m-%d')}")
        print(f"Antal poster efter datumfiltrering: {len(df)}")
    else:
        print("Varning: Ingen 'date'-kolumn hittades. Använder all data.")
    
    # Filtrera på Lunds postnummer (221-227)
    lund_postal_prefixes = ['221', '222', '223', '224', '225', '226', '227']
    
    if 'postalCode' not in df.columns:
        print("Fel: Kolumnen 'postalCode' saknas i data!")
        return None
    
    # Rensa och normalisera postnummer
    df['postalCode'] = df['postalCode'].astype(str).str.replace(" ", "")
    df['postal_prefix'] = df['postalCode'].str[:3]
    
    # Filtrera på Lund
    lund_data = df[df['postal_prefix'].isin(lund_postal_prefixes)].copy()
    
    if lund_data.empty:
        print("Ingen data hittades för Lund!")
        return None
    
    print(f"Hittade {len(lund_data)} poster för Lund (från senaste datumet)")
    
    # Analysera per postnummerprefix
    postcode_areas = {}
    
    for prefix in lund_postal_prefixes:
        prefix_data = lund_data[lund_data['postal_prefix'] == prefix].copy()
        
        if prefix_data.empty:
            continue
        
        print(f"\nAnalyserar postnummer {prefix}...")
        print(f"  Antal poster: {len(prefix_data)}")
        
        # Räkna unika aktieägare (baserat på pnrOrgnr eller name)
        if 'pnrOrgnr' in prefix_data.columns:
            unique_shareholders = prefix_data['pnrOrgnr'].nunique()
        elif 'name' in prefix_data.columns:
            unique_shareholders = prefix_data['name'].nunique()
        else:
            unique_shareholders = len(prefix_data)
        
        print(f"  Unika aktieägare: {unique_shareholders}")
        
        # Analysera gator
        streets = []
        areas = []
        
        if 'streetAddress' in prefix_data.columns:
            # Rensa och normalisera gatuadresser
            prefix_data['street_clean'] = prefix_data['streetAddress'].apply(clean_street_name)
            
            # Räkna vanligaste gatorna
            valid_streets = prefix_data['street_clean'].dropna()
            if not valid_streets.empty:
                street_counts = valid_streets.value_counts()
                top_streets = street_counts.head(10).to_dict()
                streets = list(top_streets.keys())
                
                print(f"  Vanligaste gatorna:")
                for street, count in list(top_streets.items())[:5]:
                    print(f"    - {street}: {count} gånger")
        
        # Analysera områden från gator
        if 'streetAddress' in prefix_data.columns:
            prefix_data['area'] = prefix_data['streetAddress'].apply(extract_area_name)
            valid_areas = prefix_data['area'].dropna()
            if not valid_areas.empty:
                area_counts = valid_areas.value_counts()
                areas = list(area_counts.keys())
        
        # Analysera städer (om det finns variation)
        city_info = None
        if 'city' in prefix_data.columns:
            cities = prefix_data['city'].value_counts()
            if len(cities) > 0:
                city_info = cities.index[0]
        
        # Spara resultat - total_records är nu antalet unika aktieägare från senaste datumet
        postcode_areas[prefix] = {
            'name': None,  # Kommer att fyllas i manuellt eller via area_info
            'main_streets': streets[:5],  # Top 5 gator
            'all_streets': streets[:10],  # Top 10 gator
            'areas': list(set(areas)) if areas else [],
            'city': city_info,
            'total_records': unique_shareholders  # Antal unika aktieägare från senaste datumet
        }
        
        # Försök gissa områdesnamn från vanligaste gatan eller area
        if areas:
            postcode_areas[prefix]['name'] = areas[0]
        elif streets:
            # Använd första ordet från vanligaste gatan
            first_street = streets[0]
            if first_street:
                words = first_street.split()
                if words:
                    postcode_areas[prefix]['name'] = words[0]
    
    # Spara till JSON
    output_path = os.path.join(os.path.dirname(data_file), "postcode_areas.json") if "/" not in output_file else output_file
    
    # Skapa output-mappen om den inte finns
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(postcode_areas, f, ensure_ascii=False, indent=2)
    
    print(f"\nResultat sparade till {output_path}")
    print(f"\nSammanfattning (baserat på senaste datumet):")
    for prefix, info in postcode_areas.items():
        print(f"  {prefix}: {info['name'] or 'Okänt'} - {info['total_records']} unika aktieägare, {len(info['main_streets'])} gator")
    
    return postcode_areas

if __name__ == "__main__":
    # Kör analysen
    result = analyze_postcode_areas()
    
    if result:
        print("\nAnalys klar! Du kan nu använda postcode_areas.json i dashboarden.")
    else:
        print("\nAnalysen misslyckades. Kontrollera att datafilen finns och innehåller data.")


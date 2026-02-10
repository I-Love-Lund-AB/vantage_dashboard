"""
Genererar ägarstruktur-rapport för årsredovisning.

Skapar:
- Horisontell stapelgraf (PNG + SVG) som visar antal ägare per storleksklass
- Excel-fil med komplett tabell och grafdata

Användning:
    python generate_ownership_report.py
    python generate_ownership_report.py --date 2025-12-30

Output sparas i vantage_dashboard/output/
"""

import os
import sys
import argparse
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Lägg till src-katalogen till path för att kunna importera moduler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_manager import DataManager
from config import (
    SIZE_BUCKETS_ANNUAL_REPORT,
    ILOVE_BLUE, ILOVE_RED, ILOVE_WHITE, ILOVE_DARK_GREY, ILOVE_BLACK,
    BOLAGSNAMN
)

# =============================================================================
# KONFIGURATION
# =============================================================================

# Output-katalog
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# Graf-inställningar
CHART_WIDTH_INCHES = 7.0  # ~178mm för A4
CHART_HEIGHT_INCHES = 4.5
CHART_DPI = 300

# Försök använda Gill Sans om tillgänglig, annars fallback
PREFERRED_FONTS = ['Gill Sans', 'Gill Sans MT', 'Calibri', 'Arial', 'sans-serif']


# =============================================================================
# HJÄLPFUNKTIONER
# =============================================================================

def get_available_font():
    """Hittar första tillgängliga font från preferenslistan."""
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    for font in PREFERRED_FONTS:
        if font in available_fonts:
            return font
    return 'sans-serif'


def load_shareholder_data(date_str: str = None) -> tuple[pd.DataFrame, str]:
    """
    Laddar aktieägardata från historikfilen.
    
    Args:
        date_str: Specifikt datum (YYYY-MM-DD) eller None för senaste
        
    Returns:
        tuple: (DataFrame med data för valt datum, datum som sträng)
    """
    manager = DataManager(data_file=os.path.join(os.path.dirname(__file__), 'data', 'shareholders_history.csv'))
    df = manager.load_data()
    
    if df.empty:
        raise ValueError("Ingen data hittades i shareholders_history.csv")
    
    # Konvertera datum
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        raise ValueError("Data saknar 'date'-kolumn")
    
    # Välj datum
    if date_str:
        target_date = pd.to_datetime(date_str)
        if target_date not in df['date'].values:
            available_dates = sorted(df['date'].unique())
            raise ValueError(f"Datum {date_str} finns inte i datan. Tillgängliga datum: {[str(d)[:10] for d in available_dates[-5:]]}")
    else:
        target_date = df['date'].max()
    
    # Filtrera på valt datum
    filtered_df = df[df['date'] == target_date].copy()
    date_label = str(target_date)[:10]
    
    print(f"Laddat {len(filtered_df)} rader för datum {date_label}")
    return filtered_df, date_label


def aggregate_by_owner(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregerar data per ägare (pnrOrgnr) för att hantera eventuella dubbletter.
    
    Args:
        df: DataFrame med aktieägardata
        
    Returns:
        DataFrame med en rad per ägare
    """
    if 'pnrOrgnr' not in df.columns or 'holdingsQuantity' not in df.columns:
        raise ValueError("Data saknar nödvändiga kolumner (pnrOrgnr, holdingsQuantity)")
    
    # Aggregera: summera holdings per ägare
    agg_df = df.groupby('pnrOrgnr', as_index=False).agg({
        'holdingsQuantity': 'sum',
        'name': 'first'  # Behåll namn för referens
    })
    
    print(f"Aggregerat till {len(agg_df)} unika ägare")
    return agg_df


def categorize_by_size_class(df: pd.DataFrame) -> pd.DataFrame:
    """
    Kategoriserar ägare i storleksklasser och beräknar statistik.
    
    Args:
        df: DataFrame med aggregerad ägardata
        
    Returns:
        DataFrame med statistik per storleksklass
    """
    bins = SIZE_BUCKETS_ANNUAL_REPORT['bins']
    labels = SIZE_BUCKETS_ANNUAL_REPORT['labels']
    
    # Kategorisera
    df['size_class'] = pd.cut(
        df['holdingsQuantity'],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True
    )
    
    # Totaler
    total_shares = df['holdingsQuantity'].sum()
    total_owners = len(df)
    
    # Gruppera och beräkna statistik
    stats = df.groupby('size_class', observed=True).agg({
        'holdingsQuantity': 'sum',
        'pnrOrgnr': 'count'
    }).reset_index()
    
    stats.columns = ['Storleksklass', 'Antal aktier', 'Antal ägare']
    
    # Säkerställ att alla storleksklasser finns med (även om de är tomma)
    all_classes = pd.DataFrame({'Storleksklass': labels})
    stats = all_classes.merge(stats, on='Storleksklass', how='left')
    stats['Antal aktier'] = stats['Antal aktier'].fillna(0).astype(int)
    stats['Antal ägare'] = stats['Antal ägare'].fillna(0).astype(int)
    
    # Beräkna procent
    stats['% av aktier'] = (stats['Antal aktier'] / total_shares * 100).round(1)
    stats['% av ägare'] = (stats['Antal ägare'] / total_owners * 100).round(1)
    
    # Lägg till totalrad
    total_row = pd.DataFrame([{
        'Storleksklass': 'Totalt',
        'Antal aktier': total_shares,
        'Antal ägare': total_owners,
        '% av aktier': 100.0,
        '% av ägare': 100.0
    }])
    stats = pd.concat([stats, total_row], ignore_index=True)
    
    return stats


# =============================================================================
# GRAF-GENERERING
# =============================================================================

def create_ownership_chart(stats: pd.DataFrame, date_label: str, output_dir: str):
    """
    Skapar horisontell stapelgraf som visar antal ägare per storleksklass.
    
    Args:
        stats: DataFrame med statistik per storleksklass
        date_label: Datum för rapporten (för filnamn)
        output_dir: Katalog för output-filer
    """
    # Exkludera totalraden från grafen
    chart_data = stats[stats['Storleksklass'] != 'Totalt'].copy()
    
    # Använd tillgänglig font
    font_name = get_available_font()
    
    # Skapa figur
    fig, ax = plt.subplots(figsize=(CHART_WIDTH_INCHES, CHART_HEIGHT_INCHES))
    
    # Horisontell stapelgraf
    y_pos = range(len(chart_data))
    bars = ax.barh(
        y_pos,
        chart_data['Antal ägare'],
        color=ILOVE_BLUE,
        edgecolor='none',
        height=0.7
    )
    
    # Y-axel: storleksklasser
    ax.set_yticks(y_pos)
    ax.set_yticklabels(chart_data['Storleksklass'], fontname=font_name, fontsize=10)
    
    # X-axel
    ax.set_xlabel('Antal ägare', fontname=font_name, fontsize=11, color=ILOVE_DARK_GREY)
    
    # Y-axel titel
    ax.set_ylabel('Innehavsstorlek', fontname=font_name, fontsize=11, color=ILOVE_DARK_GREY)
    
    # Titel
    ax.set_title(
        'Ägarstruktur 2025',
        fontname=font_name,
        fontsize=14,
        fontweight='bold',
        color=ILOVE_DARK_GREY,
        pad=15
    )
    
    # Visa värden på staplarna - ALLA inuti med vit text
    max_value = max(chart_data['Antal ägare'])
    for bar, value in zip(bars, chart_data['Antal ägare']):
        width = bar.get_width()
        # Placera text inuti stapeln
        text_x = max(width * 0.5, width - 25)
        
        ax.text(
            text_x,
            bar.get_y() + bar.get_height() / 2,
            f'{int(value)}',
            va='center',
            ha='center',
            fontname=font_name,
            fontsize=9,
            color=ILOVE_WHITE,
            fontweight='bold'
        )
    
    # Styling
    ax.set_facecolor(ILOVE_WHITE)
    fig.set_facecolor(ILOVE_WHITE)
    
    # Ta bort ram och gridlines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(ILOVE_DARK_GREY)
    ax.spines['bottom'].set_color(ILOVE_DARK_GREY)
    
    # Tick-färger
    ax.tick_params(axis='x', colors=ILOVE_DARK_GREY)
    ax.tick_params(axis='y', colors=ILOVE_DARK_GREY)
    
    # X-axel start från 0
    ax.set_xlim(0, max(chart_data['Antal ägare']) * 1.05)
    
    # Invertera y-axeln så att minsta klassen är längst upp
    ax.invert_yaxis()
    
    # Tight layout
    plt.tight_layout()
    
    # Spara endast PNG
    png_path = os.path.join(output_dir, f'agarstruktur_{date_label}.png')
    
    fig.savefig(png_path, dpi=CHART_DPI, bbox_inches='tight', facecolor=ILOVE_WHITE)
    
    plt.close(fig)
    
    print(f"Graf sparad: {png_path}")
    
    return png_path


# =============================================================================
# EXCEL-EXPORT
# =============================================================================

def export_to_excel(stats: pd.DataFrame, date_label: str, output_dir: str):
    """
    Exporterar statistik till Excel med två blad.
    
    Args:
        stats: DataFrame med statistik per storleksklass
        date_label: Datum för rapporten (för filnamn)
        output_dir: Katalog för output-filer
    """
    excel_path = os.path.join(output_dir, f'agarstruktur_{date_label}.xlsx')
    
    # Skapa Excel-writer
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Blad 1: Komplett tabell
        stats_formatted = stats.copy()
        stats_formatted['Antal aktier'] = stats_formatted['Antal aktier'].apply(
            lambda x: f"{int(x):,}".replace(',', ' ')
        )
        stats_formatted['% av aktier'] = stats_formatted['% av aktier'].apply(
            lambda x: f"{x:.1f}%"
        )
        stats_formatted['% av ägare'] = stats_formatted['% av ägare'].apply(
            lambda x: f"{x:.1f}%"
        )
        
        stats_formatted.to_excel(writer, sheet_name='Ägarstruktur', index=False)
        
        # Blad 2: Grafdata (enkel version för att skapa egen graf i Excel)
        graph_data = stats[stats['Storleksklass'] != 'Totalt'][['Storleksklass', 'Antal ägare']].copy()
        graph_data.to_excel(writer, sheet_name='Grafdata', index=False)
        
        # Formatera kolumnbredder
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"Excel sparad: {excel_path}")
    return excel_path


# =============================================================================
# HUVUDFUNKTION
# =============================================================================

def main():
    """Huvudfunktion som kör hela rapportgenereringen."""
    # Argument-parsning
    parser = argparse.ArgumentParser(
        description='Genererar ägarstruktur-rapport för årsredovisning.'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Datum att generera rapport för (YYYY-MM-DD). Default: senaste datum i datan.'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"ÄGARSTRUKTUR-RAPPORT - {BOLAGSNAMN}")
    print("=" * 60)
    
    # Skapa output-katalog om den inte finns
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Skapade katalog: {OUTPUT_DIR}")
    
    try:
        # 1. Ladda data
        print("\n1. Laddar aktieägardata...")
        df, date_label = load_shareholder_data(args.date)
        
        # 2. Aggregera per ägare
        print("\n2. Aggregerar per ägare...")
        agg_df = aggregate_by_owner(df)
        
        # 3. Kategorisera i storleksklasser
        print("\n3. Kategoriserar i storleksklasser...")
        stats = categorize_by_size_class(agg_df)
        
        # Visa statistik
        print("\n" + "=" * 60)
        print("ÄGARSTRUKTUR")
        print("=" * 60)
        print(stats.to_string(index=False))
        print("=" * 60)
        
        # 4. Skapa graf
        print("\n4. Skapar graf...")
        png_path = create_ownership_chart(stats, date_label, OUTPUT_DIR)
        
        # 5. Exportera till Excel
        print("\n5. Exporterar till Excel...")
        excel_path = export_to_excel(stats, date_label, OUTPUT_DIR)
        
        # Sammanfattning
        print("\n" + "=" * 60)
        print("KLART! Filer skapade:")
        print("=" * 60)
        print(f"  - Graf (PNG):  {png_path}")
        print(f"  - Excel:       {excel_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nFEL: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


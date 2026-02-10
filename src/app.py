import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import time
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from dotenv import load_dotenv
import gender_guesser.detector as gender

import sys
import os

# Lägg till nuvarande katalog till sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importera våra anpassade moduler
from api import VantageClient
from data_manager import DataManager
from config import (
    ILOVE_RED, ILOVE_BLUE, ILOVE_WHITE, ILOVE_GREY, ILOVE_BLACK, ILOVE_DARK_GREY,
    ILOVE_COLORS, GENDER_COLORS, OWNER_TYPE_COLORS,
    ISIN, ISIN_A, ISIN_B, VOTES_PER_A_SHARE, VOTES_PER_B_SHARE,
    BOLAGSNAMN, EARLIEST_AVAILABLE_DATE,
    DEFAULT_LUND_POPULATION, LUND_POSTAL_PREFIXES,
    SIZE_BUCKETS, COMPANY_INDICATORS, TOP_OWNERS_COUNT,
    PAGE_TITLE, AUTO_REFRESH_INTERVAL,
    get_color_sequence
)
from tabs import (
    render_gender_analysis,
    render_age_analysis,
    render_owner_type_comparison
)

# --- Sidkonfiguration ---
# Sök efter favicon-fil (stödjer .png, .ico, .svg)
favicon_path = None
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Gå upp till vantage_dashboard-mappen
possible_favicon_paths = [
    os.path.join(base_dir, 'favicon.png'),
    os.path.join(base_dir, 'Logo ILL.png'),  # Använd Logo ILL.png om favicon.png inte finns
    os.path.join(base_dir, 'favicon.ico'),
    os.path.join(base_dir, 'favicon.svg'),
    os.path.join(base_dir, 'assets', 'favicon.png'),
    os.path.join(base_dir, 'assets', 'favicon.ico'),
    os.path.join(base_dir, 'assets', 'favicon.svg'),
]

for path in possible_favicon_paths:
    if os.path.exists(path):
        favicon_path = path
        break

st.set_page_config(
    page_title="Aktieägaranalys Dashboard - I Love Lund",
    page_icon=favicon_path if favicon_path else "📊",
    layout="wide"
)

# --- Brand Book CSS ---
st.markdown("""
<style>
    /* I Love Lund Brand Colors */
    :root {
        --i-love-red: #e30413;
        --i-love-blue: #25408d;
        --i-love-white: #ffffff;
        --i-love-grey: #f6f6f6;
        --i-love-black: #000000;
        --i-love-dark-grey: #2f2f2f;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers - Gill Sans Semibold equivalent styling, I Love Red, UPPERCASE */
    h1, h2, h3 {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-weight: 600;
        color: var(--i-love-red);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Subheaders - Gill Sans Regular, I Love Blue */
    h4, h5, h6 {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-weight: 400;
        color: var(--i-love-blue);
    }
    
    /* Body text - Gill Sans Light */
    body, p, div, span, label, .stText, .stMarkdown {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-weight: 300;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--i-love-grey);
    }
    
    /* Button styling - I Love Blue */
    .stButton > button {
        background-color: var(--i-love-blue);
        color: var(--i-love-white);
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-weight: 400;
        border-radius: 4px;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: var(--i-love-red);
        color: var(--i-love-white);
    }
    
    /* Primary button - I Love Red */
    button[kind="primary"] {
        background-color: var(--i-love-red) !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-weight: 600;
        color: var(--i-love-blue);
    }
    
    /* Metric card containers - add brand colors */
    [data-testid="stMetric"] {
        background-color: var(--i-love-grey);
        border-left: 4px solid var(--i-love-blue);
        padding: 1rem;
        border-radius: 4px;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--i-love-dark-grey);
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
    }
    
    /* Success messages - subtle green or I Love Blue */
    .stSuccess {
        background-color: var(--i-love-grey);
        border-left: 4px solid var(--i-love-blue);
    }
    
    /* Info messages */
    .stInfo {
        background-color: var(--i-love-grey);
        border-left: 4px solid var(--i-love-blue);
    }
    
    /* Warning messages */
    .stWarning {
        background-color: var(--i-love-grey);
        border-left: 4px solid var(--i-love-red);
    }
    
    /* Error messages */
    .stError {
        background-color: var(--i-love-grey);
        border-left: 4px solid var(--i-love-red);
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
    }
    
    /* Selectbox */
    .stSelectbox > div > div > select {
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialisering ---
@st.cache_resource
def get_components():
    try:
        client = VantageClient()
    except Exception as e:
        client = None
    manager = DataManager()
    return client, manager

client, manager = get_components()

# --- Lösenordshantering för avanonymisering ---
def verify_password(password: str, stored_hash: str) -> bool:
    """Verifierar lösenord mot hash med säker jämförelse."""
    try:
        # Skapa hash av inmatat lösenord
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        # Säker jämförelse för att förhindra timing attacks
        return hmac.compare_digest(password_hash, stored_hash)
    except Exception:
        return False

def get_password_hash() -> str:
    """Hämtar lösenordshash från miljövariabel eller använder standard."""
    # Först försök hämta från miljövariabel
    password = os.getenv("DATA_ACCESS_PASSWORD")
    if password:
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Fallback: Standard lösenord (VARNING: Ändra detta i produktion!)
    # Standard: "admin123" - ÄNDRA DETTA!
    default_password = "admin123"
    return hashlib.sha256(default_password.encode()).hexdigest()

# Initiera session state för autentisering
if 'data_access_authenticated' not in st.session_state:
    st.session_state['data_access_authenticated'] = False

# Ladda postnummerområden (om filen finns)
POSTCODE_AREAS = {}
postcode_areas_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'postcode_areas.json')
if os.path.exists(postcode_areas_file):
    try:
        with open(postcode_areas_file, 'r', encoding='utf-8') as f:
            POSTCODE_AREAS = json.load(f)
    except Exception as e:
        print(f"Kunde inte ladda postcode_areas.json: {e}")

# Färger och konstanter importeras nu från config.py

def apply_brand_layout(fig):
    """Applicerar I Love Lund brand book layout på Plotly-figurer"""
    fig.update_layout(
        plot_bgcolor=ILOVE_WHITE,
        paper_bgcolor=ILOVE_WHITE,
        font_family="Gill Sans, sans-serif",
        title_font_color=ILOVE_RED,
        font_color=ILOVE_DARK_GREY,
        title_font_size=16,
        font_size=12
    )
    return fig

# --- HJÄLPFUNKTIONER ---
def get_last_month_end_date():
    """
    Räknar ut sista dagen i föregående månad.
    Detta är oftast datumet då ny data finns tillgänglig.
    """
    today = datetime.today()
    # Första dagen i denna månad
    first_of_this_month = today.replace(day=1)
    # Sista dagen i förra månaden är dagen innan första dagen i denna månad
    last_month_end = first_of_this_month - timedelta(days=1)
    return last_month_end


def filter_by_time_period(df, date_col, period):
    if df.empty: return df
    max_date = df[date_col].max()
    if period == "YTD":
        # YTD börjar från stängning föregående år (30 dec) = öppning nuvarande år
        # Om vi är i 2025, börja från 2024-12-30
        start_date = datetime(max_date.year - 1, 12, 30)
    elif period == "QTD":
        # QTD ska visa utvecklingen från kvartalets "öppning".
        # Eftersom vi mäter vid månadsskiften använder vi stängningen precis före kvartalsstart
        # (t.ex. stängning sep = öppning okt) om den finns i datan.
        #
        # Kvartalsstart (kalenderkvartal):
        # Q1: 1 jan, Q2: 1 apr, Q3: 1 jul, Q4: 1 okt
        curr_quarter = (max_date.month - 1) // 3 + 1
        quarter_start_months = {1: 1, 2: 4, 3: 7, 4: 10}
        start_month = quarter_start_months[curr_quarter]
        quarter_start = pd.Timestamp(datetime(max_date.year, start_month, 1))

        # Hitta senaste datum innan kvartalsstart (stängning månaden före)
        prev_dates = df[df[date_col] < quarter_start][date_col]
        if not prev_dates.empty:
            start_date = prev_dates.max()
        else:
            start_date = quarter_start
    elif period == "1Y":
        start_date = max_date - timedelta(days=365)
    else: # Max
        # Max = från tidigast tillgängliga datum (2024-01-31), inte från ev. äldre rader i filen
        start_date = max(pd.Timestamp(df[date_col].min()), EARLIEST_AVAILABLE_DATE)
    
    start_date = pd.Timestamp(start_date)
    return df[df[date_col] >= start_date].copy()


def get_reference_date_one_year_back(df: pd.DataFrame, latest_date: pd.Timestamp) -> pd.Timestamp | None:
    """
    Hittar referensdatum cirka ett år tillbaka i tiden baserat på månadsavslut.

    Logik:
    - Försök hitta sista tillgängliga datum i samma månad ett år tidigare.
    - Om inget datum finns i den månaden, ta närmast föregående datum
      som ligger före (latest_date - 1 år).
    - Returnerar None om ingen lämplig datapunkt finns.
    """
    if df.empty or 'date' not in df.columns or pd.isna(latest_date):
        return None

    # Säkerställ Timestamp
    latest_date = pd.Timestamp(latest_date)
    dates = pd.to_datetime(df['date'])

    # 1) Försök hitta sista datum i samma månad ett år tidigare
    target_year = latest_date.year - 1
    target_month = latest_date.month

    same_month_mask = (dates.dt.year == target_year) & (dates.dt.month == target_month)
    same_month_candidates = dates[same_month_mask]

    if not same_month_candidates.empty:
        return pd.Timestamp(same_month_candidates.max())

    # 2) Fallback: närmast föregående datum före latest_date - 1 år
    approx_ref = latest_date - pd.DateOffset(years=1)
    older_candidates = dates[dates <= approx_ref]
    if not older_candidates.empty:
        return pd.Timestamp(older_candidates.max())

    # Ingen historik tillgänglig ett år tillbaka
    return None


def build_owner_snapshot(df_for_date: pd.DataFrame,
                         quantity_col: str = 'holdingsQuantity',
                         prefix: str = '') -> pd.DataFrame:
    """
    Bygger ett aggregerat snapshot per ägare (pnrOrgnr) för ett visst datum.

    Returnerar kolumner:
        - pnrOrgnr
        - name (första förekomsten om den finns)
        - coAdress (första förekomsten om den finns)
        - A_shares, B_shares (om de finns)
        - votesQuantity (om den finns)
        - {prefix}_quantity
        - {prefix}_rank (1 = störst ägare)
    """
    if df_for_date.empty or quantity_col not in df_for_date.columns or 'pnrOrgnr' not in df_for_date.columns:
        return pd.DataFrame()

    # Normalisera kolumnnamn: coAddress -> coAdress
    df_normalized = df_for_date.copy()
    if 'coAddress' in df_normalized.columns and 'coAdress' not in df_normalized.columns:
        df_normalized['coAdress'] = df_normalized['coAddress']

    agg_dict: dict[str, object] = {quantity_col: 'sum'}
    if 'name' in df_normalized.columns:
        agg_dict['name'] = 'first'
    if 'coAdress' in df_normalized.columns:
        agg_dict['coAdress'] = 'first'
    # Inkludera A/B-aktier och röster om de finns
    if 'A_shares' in df_normalized.columns:
        agg_dict['A_shares'] = 'sum'
    if 'B_shares' in df_normalized.columns:
        agg_dict['B_shares'] = 'sum'
    if 'votesQuantity' in df_normalized.columns:
        agg_dict['votesQuantity'] = 'sum'

    grouped = df_normalized.groupby('pnrOrgnr', as_index=False).agg(agg_dict)

    quantity_col_out = f"{prefix}_quantity" if prefix else 'quantity'
    rank_col_out = f"{prefix}_rank" if prefix else 'rank'

    grouped[quantity_col_out] = grouped[quantity_col]
    # Rangordna: 1 = flest aktier
    grouped[rank_col_out] = grouped[quantity_col_out].rank(method="min", ascending=False).astype('Int64')

    result_cols = ['pnrOrgnr']
    if 'name' in grouped.columns:
        result_cols.append('name')
    if 'coAdress' in grouped.columns:
        result_cols.append('coAdress')
    if 'A_shares' in grouped.columns:
        result_cols.append('A_shares')
    if 'B_shares' in grouped.columns:
        result_cols.append('B_shares')
    if 'votesQuantity' in grouped.columns:
        result_cols.append('votesQuantity')
    result_cols.extend([quantity_col_out, rank_col_out])

    return grouped[result_cols]


def build_top50_comparison(current_agg: pd.DataFrame,
                           ref_agg: pd.DataFrame | None = None,
                           top_n: int = 50) -> pd.DataFrame:
    """
    Bygger en jämförelsetabell mellan nuvarande och historiska ägarsnapshots.

    Returnerar en DataFrame med bl.a.:
        - Rank_now
        - Rank_change (text med pil)
        - Name
        - PnrOrgnr
        - CoAdress
        - Quantity_now
        - Quantity_change (text med pil)
    """
    if current_agg is None or current_agg.empty:
        return pd.DataFrame()

    df_current = current_agg.copy()
    # Säkerställ kolumnnamn
    if 'current_quantity' not in df_current.columns:
        # anta generiska namn från build_owner_snapshot utan prefix
        if 'quantity' in df_current.columns:
            df_current = df_current.rename(columns={'quantity': 'current_quantity',
                                                    'rank': 'current_rank'})

    merge_cols = ['pnrOrgnr']
    ref_cols = []
    if ref_agg is not None and not ref_agg.empty:
        df_ref = ref_agg.copy()
        if 'ref_quantity' not in df_ref.columns:
            if 'quantity' in df_ref.columns:
                df_ref = df_ref.rename(columns={'quantity': 'ref_quantity',
                                                'rank': 'ref_rank'})
        ref_cols = ['ref_quantity', 'ref_rank']
        merged = pd.merge(
            df_current,
            df_ref[merge_cols + ref_cols],
            on='pnrOrgnr',
            how='left'
        )
    else:
        merged = df_current.copy()
        merged['ref_quantity'] = pd.NA
        merged['ref_rank'] = pd.NA

    # Beräkna förändringar
    merged['ref_quantity_filled'] = merged['ref_quantity'].fillna(0)
    merged['delta_quantity'] = merged['current_quantity'] - merged['ref_quantity_filled']

    def quantity_trend_symbol(delta: float) -> str:
        if pd.isna(delta) or delta == 0:
            return "→"
        return "↑" if delta > 0 else "↓"

    merged['quantity_trend'] = merged['delta_quantity'].apply(quantity_trend_symbol)

    def rank_trend_label(row) -> str:
        current_rank = row.get('current_rank', pd.NA)
        ref_rank = row.get('ref_rank', pd.NA)
        if pd.isna(current_rank):
            return ""
        if pd.isna(ref_rank):
            return "Ny"
        try:
            delta = int(ref_rank) - int(current_rank)
        except Exception:
            return "→"
        if delta == 0:
            return "→"
        symbol = "↑" if delta > 0 else "↓"
        return f"{symbol}{abs(delta)}"

    merged['rank_trend'] = merged.apply(rank_trend_label, axis=1)

    # Sortera på nuvarande quantity och välj topp N
    merged_sorted = merged.sort_values('current_quantity', ascending=False).head(top_n)

    # Kombinera namn och coAdress om coAdress finns
    # Normalisera coAddress -> coAdress om det behövs
    if 'coAddress' in merged_sorted.columns and 'coAdress' not in merged_sorted.columns:
        merged_sorted['coAdress'] = merged_sorted['coAddress']
    
    if 'name' in merged_sorted.columns and 'coAdress' in merged_sorted.columns:
        def combine_name_coadress(row):
            name = str(row.get('name', '')) if pd.notna(row.get('name')) else ''
            coadress = row.get('coAdress', '')
            # Hantera både NaN och tomma strängar
            if pd.notna(coadress):
                coadress = str(coadress).strip()
                if coadress and coadress != '' and coadress.lower() != 'nan':
                    return f"{name}: {coadress}"
            return name
        merged_sorted['name'] = merged_sorted.apply(combine_name_coadress, axis=1)

    # Bygg vänliga kolumner för UI
    def format_quantity_change(row) -> str:
        delta = row['delta_quantity']
        symbol = row['quantity_trend']
        if pd.isna(delta) or (ref_agg is None or row.get('ref_quantity', pd.NA) is pd.NA):
            # Ny ägare eller ingen historik
            if symbol == "↑":
                return "Ny ↑"
            return "–"
        if delta == 0:
            return "→ 0"
        return f"{symbol} {int(delta):,}".replace(",", " ")

    merged_sorted['Quantity_change'] = merged_sorted.apply(format_quantity_change, axis=1)

    # Slutlig tabell
    final_cols = []
    final_cols.append('current_rank')
    final_cols.append('rank_trend')
    if 'name' in merged_sorted.columns:
        final_cols.append('name')
    # Lägg till A/B-aktier om de finns
    if 'A_shares' in merged_sorted.columns:
        final_cols.append('A_shares')
    if 'B_shares' in merged_sorted.columns:
        final_cols.append('B_shares')
    final_cols.append('current_quantity')
    # Lägg till röster om de finns
    if 'votesQuantity' in merged_sorted.columns:
        final_cols.append('votesQuantity')
    final_cols.append('Quantity_change')

    result = merged_sorted[final_cols].copy()
    rename_dict = {
        'current_rank': 'Rank (nu)',
        'rank_trend': 'Rank-förändring',
        'name': 'Namn',
        'A_shares': 'A-aktier',
        'B_shares': 'B-aktier',
        'current_quantity': 'Totalt aktier',
        'votesQuantity': 'Röster',
        'Quantity_change': 'Förändring'
    }
    result = result.rename(columns={k: v for k, v in rename_dict.items() if k in result.columns})

    # Formatera siffror för visning
    for col in ['Totalt aktier', 'A-aktier', 'B-aktier', 'Röster']:
        if col in result.columns:
            result[col] = result[col].apply(
                lambda x: f"{int(x):,}".replace(",", " ") if pd.notna(x) and x != 0 else ("0" if pd.notna(x) else "")
            )

    return result


def is_personnummer(pnr_orgnr, name=None):
    """
    Identifierar om ett nummer är ett personnummer eller organisationsnummer.
    
    Personnummer i Sverige:
    - 12-siffriga: YYYYMMDD-XXXX där YYYY är födelseår (vanligtvis 19XX eller 20XX)
    - 10-siffriga: YYMMDD-XXXX där YY är födelseår (vanligtvis 00-15)
    - Månad: 01-12, Dag: 01-31
    
    Organisationsnummer:
    - 11-siffriga: Alltid organisationsnummer
    - 12-siffriga: XXYYMMDD-XXXX där XX är oftast 16-99 (INTE 19 eller 20)
    - 10-siffriga: XXYYMMDD-XXXX där XX är oftast 16-99
    
    Args:
        pnr_orgnr: Personnummer eller organisationsnummer
        name: Namn på ägaren (används som hint om numret är oklart)
    
    Returnerar: True om personnummer, False om organisationsnummer, None om okänt
    """
    if pd.isna(pnr_orgnr):
        return None
    
    try:
        pnr_str = str(pnr_orgnr).strip()
        
        # Ta bort bindestreck och mellanslag
        pnr_clean = pnr_str.replace('-', '').replace(' ', '')
        
        # Kontrollera att det bara är siffror
        if not pnr_clean.isdigit():
            return None
        
        # Organisationsnummer kan vara 10, 11 eller 12 siffror
        # Personnummer är vanligtvis 10 eller 12 siffror
        if len(pnr_clean) not in [10, 11, 12]:
            return None
        
        # 11-siffriga nummer är ALLTID organisationsnummer
        if len(pnr_clean) == 11:
            return False
        
        # För 12-siffriga nummer:
        # Personnummer: YYYYMMDD-XXXX där YYYY börjar med 19 eller 20
        # Organisationsnummer: XXYYMMDD-XXXX där XX är 16-99 (INTE 19 eller 20)
        if len(pnr_clean) == 12:
            first_two = int(pnr_clean[:2])
            year_prefix = pnr_clean[:2]  # Första två siffrorna som sträng
            year_full = int(pnr_clean[:4])
            month = int(pnr_clean[4:6])
            day = int(pnr_clean[6:8])
            
            # Om första två är 19 eller 20, är det troligen personnummer
            # Detta är den viktigaste indikatorn för personnummer
            if year_prefix in ['19', '20']:
                return True  # Personnummer (börjar med 19 eller 20)
            
            # Om första två är 16-18 eller 21-99, är det troligen organisationsnummer
            if 16 <= first_two <= 18 or 21 <= first_two <= 99:
                return False  # Organisationsnummer
            
            # Om dag är 00, är det troligen organisationsnummer
            if day == 0:
                return False
            
            # Om månad eller dag är ogiltig, är det troligen organisationsnummer
            if not (1 <= month <= 12) or not (1 <= day <= 31):
                return False
            
            # Annars okänt (kan vara personnummer med ovanligt år, men börjar inte med 19/20)
            return None
        
        # För 10-siffriga nummer: YYMMDD-XXXX
        first_two = int(pnr_clean[:2])
        month = int(pnr_clean[2:4])
        day = int(pnr_clean[4:6])
        
        # Organisationsnummer: Om första två siffrorna är 16-99, är det organisationsnummer
        if 16 <= first_two <= 99:
            return False  # Organisationsnummer
        
        # Personnummer: Om första två siffrorna är 00-15, och månad är 01-12 och dag är 01-31,
        # är det troligen ett personnummer
        if 0 <= first_two <= 15:
            if 1 <= month <= 12 and 1 <= day <= 31:
                return True  # Personnummer
        
        # Om månad är 01-12 och dag är 01-31, är det troligen personnummer
        if 1 <= month <= 12 and 1 <= day <= 31:
            return True
        
        # Om dag är 00 eller månad är inte 01-12, är det troligen organisationsnummer
        if day == 0 or not (1 <= month <= 12):
            return False
        
        return None  # Okänt
    except (ValueError, IndexError):
        return None


def calculate_age_from_personnummer(pnr_orgnr, reference_date=None):
    """
    Beräknar ålder från svenskt personnummer.
    
    Args:
        pnr_orgnr: Personnummer som str eller nummer
        reference_date: Referensdatum för åldersberäkning (default: idag)
    
    Returnerar: Ålder i år, eller None om det inte är ett personnummer
    """
    if reference_date is None:
        reference_date = datetime.today()
    
    if not is_personnummer(pnr_orgnr):
        return None
    
    try:
        pnr_str = str(pnr_orgnr).strip()
        pnr_clean = pnr_str.replace('-', '').replace(' ', '')
        
        # Om 12 siffror, ta bort de första två
        if len(pnr_clean) == 12:
            year = int(pnr_clean[:4])
            month = int(pnr_clean[4:6])
            day = int(pnr_clean[6:8])
        else:
            # 10 siffror: YYMMDD-XXXX
            year_short = int(pnr_clean[:2])
            month = int(pnr_clean[2:4])
            day = int(pnr_clean[4:6])
            
            # Bestäm sekulum baserat på ålder
            # Om YY + 100 < nuvarande år, är det 1900-talet
            # Annars är det 2000-talet
            current_year = reference_date.year
            century = 1900 if (year_short + 100) < current_year else 2000
            year = century + year_short
        
        birth_date = datetime(year, month, day)
        age = (reference_date - birth_date).days // 365
        return age
    except (ValueError, IndexError):
        return None


# Initiera gender detector (cached för prestanda)
@st.cache_resource
def get_gender_detector():
    """Returnerar en cached gender detector-instans."""
    return gender.Detector(case_sensitive=False)


def extract_first_name(name_str):
    """
    Extraherar förnamn från en namnsträng.
    
    Hanterar olika format:
    - "EFTERNAMN, FÖRNAMN" -> "FÖRNAMN"
    - "FÖRNAMN EFTERNAMN" -> "FÖRNAMN"
    - "FÖRNAMN1 FÖRNAMN2 EFTERNAMN" -> "FÖRNAMN1"
    
    Args:
        name_str: Namnsträng (kan vara None eller tom)
    
    Returnerar: Förnamn som sträng, eller None om det inte går att extrahera
    """
    if pd.isna(name_str) or not name_str or not isinstance(name_str, str):
        return None
    
    name_clean = name_str.strip()
    if not name_clean:
        return None
    
    # Kontrollera företagsindikatorer (COMPANY_INDICATORS från config.py)
    if any(indicator in name_clean.upper() for indicator in COMPANY_INDICATORS):
        return None  # Detta är troligen ett företag, inte en person
    
    # Om det finns ett komma, är formatet troligen "EFTERNAMN, FÖRNAMN"
    if ',' in name_clean:
        parts = [p.strip() for p in name_clean.split(',')]
        if len(parts) >= 2:
            # Efter kommat är förnamnet (eller förnamn)
            first_name_part = parts[1]
            # Ta första ordet (första förnamnet)
            first_name = first_name_part.split()[0] if first_name_part.split() else None
            return first_name if first_name else None
    
    # Om inget komma, anta format "FÖRNAMN EFTERNAMN"
    # Ta första ordet som förnamn
    name_parts = name_clean.split()
    if name_parts:
        return name_parts[0]
    
    return None


def classify_gender_from_name(name_str, pnr_orgnr=None, is_person_precomputed=None):
    """
    Klassificerar kön baserat på namn.
    
    Args:
        name_str: Namnsträng
        pnr_orgnr: Personnummer/organisationsnummer (används för att verifiera att det är en person)
        is_person_precomputed: Om redan beräknat, skicka in för att undvika omberäkning
    
    Returnerar: "Man", "Kvinna", "Okänt", eller None (om det inte är en person)
    """
    # Om det finns ett personnummer, kontrollera att det verkligen är en person
    if is_person_precomputed is not None:
        is_person = is_person_precomputed
    elif pnr_orgnr is not None:
        is_person = is_personnummer(pnr_orgnr)
    else:
        is_person = None
    
    if is_person is False:
        return None  # Detta är en juridisk person (företag)
    # Om is_person är None eller True, fortsätt med namnanalys
    
    # Extrahera förnamn
    first_name = extract_first_name(name_str)
    if not first_name:
        return "Okänt"
    
    try:
        detector = get_gender_detector()
        # gender-guesser använder default (kombination av flera språk) vilket fungerar bra för svenska namn
        gender_result = detector.get_gender(first_name)
        
        # Mappa resultatet
        if gender_result in ['male', 'mostly_male']:
            return "Man"
        elif gender_result in ['female', 'mostly_female']:
            return "Kvinna"
        else:
            # 'andy' (androgynous), 'unknown', eller None
            return "Okänt"
    except Exception:
        return "Okänt"


# --- FUNKTION FÖR ATT SAMMANSTÄLLA A- OCH B-AKTIER ---
def merge_ab_shares(df: pd.DataFrame) -> pd.DataFrame:
    """
    Slår ihop A- och B-aktier per ägare (pnrOrgnr) och beräknar korrekta röster.
    
    För varje ägare beräknas:
    - A_shares: Antal A-aktier
    - B_shares: Antal B-aktier
    - holdingsQuantity: Totalt antal aktier (A + B)
    - votesQuantity: Totalt antal röster (A * 10 + B * 1)
    
    Args:
        df: DataFrame med rådata som kan innehålla både A- och B-aktier
        
    Returns:
        DataFrame med sammanslagna aktieinnehav per ägare
    """
    if df.empty:
        return df
    
    # Om shareClass inte finns, anta att allt är B-aktier (bakåtkompatibilitet)
    if 'shareClass' not in df.columns:
        df = df.copy()
        df['shareClass'] = 'B'
    
    # Separera A och B aktier
    a_shares = df[df['shareClass'] == 'A'].copy()
    b_shares = df[df['shareClass'] == 'B'].copy()
    
    # Skapa pivot per ägare
    result_dfs = []
    
    # Grundläggande kolumner att behålla (från första förekomsten)
    base_cols = ['pnrOrgnr', 'name', 'coAddress', 'streetAddress', 'postalCode', 
                 'city', 'countryCode', 'accountType', 'regType', 'date']
    base_cols = [c for c in base_cols if c in df.columns]
    
    # Aggregera B-aktier
    if not b_shares.empty:
        b_agg = b_shares.groupby('pnrOrgnr', as_index=False).agg({
            **{col: 'first' for col in base_cols if col != 'pnrOrgnr' and col in b_shares.columns},
            'holdingsQuantity': 'sum'
        })
        b_agg = b_agg.rename(columns={'holdingsQuantity': 'B_shares'})
        result_dfs.append(b_agg)
    
    # Aggregera A-aktier
    if not a_shares.empty:
        a_agg = a_shares.groupby('pnrOrgnr', as_index=False).agg({
            **{col: 'first' for col in base_cols if col != 'pnrOrgnr' and col in a_shares.columns},
            'holdingsQuantity': 'sum'
        })
        a_agg = a_agg.rename(columns={'holdingsQuantity': 'A_shares'})
        result_dfs.append(a_agg)
    
    if not result_dfs:
        return df
    
    # Merge A och B
    if len(result_dfs) == 2:
        b_agg = result_dfs[0]  # B-aktier data
        a_agg = result_dfs[1]  # A-aktier data
        
        # Full outer merge - behåll all info från båda sidor
        merged = pd.merge(
            b_agg,
            a_agg,
            on='pnrOrgnr',
            how='outer',
            suffixes=('', '_from_a')
        )
        
        # För ägare som ENDAST har A-aktier, fyll i namn och annan info från A-data
        for col in base_cols:
            if col == 'pnrOrgnr':
                continue
            col_from_a = f'{col}_from_a'
            if col in merged.columns and col_from_a in merged.columns:
                # Fyll i saknade värden från A-aktie-data
                merged[col] = merged[col].fillna(merged[col_from_a])
                merged = merged.drop(columns=[col_from_a])
            elif col_from_a in merged.columns:
                # Kolumnen finns bara i A-data
                merged[col] = merged[col_from_a]
                merged = merged.drop(columns=[col_from_a])
    else:
        merged = result_dfs[0]
    
    # Fyll i saknade värden för aktieantal
    if 'A_shares' not in merged.columns:
        merged['A_shares'] = 0
    if 'B_shares' not in merged.columns:
        merged['B_shares'] = 0
    
    merged['A_shares'] = merged['A_shares'].fillna(0).astype(int)
    merged['B_shares'] = merged['B_shares'].fillna(0).astype(int)
    
    # Beräkna totaler
    merged['holdingsQuantity'] = merged['A_shares'] + merged['B_shares']
    merged['votesQuantity'] = merged['A_shares'] * VOTES_PER_A_SHARE + merged['B_shares'] * VOTES_PER_B_SHARE
    
    # Beräkna procentandelar (baserat på total för bolaget)
    # Hämta totala antal aktier och röster från config eller beräkna
    total_a = a_shares['holdingsQuantity'].sum() if not a_shares.empty else 0
    total_b = b_shares['holdingsQuantity'].sum() if not b_shares.empty else 0
    total_shares = total_a + total_b
    total_votes = total_a * VOTES_PER_A_SHARE + total_b * VOTES_PER_B_SHARE
    
    if total_shares > 0:
        merged['holdingsPercentage'] = (merged['holdingsQuantity'] / total_shares * 100).round(4)
    else:
        merged['holdingsPercentage'] = 0
        
    if total_votes > 0:
        merged['votesPercentage'] = (merged['votesQuantity'] / total_votes * 100).round(4)
    else:
        merged['votesPercentage'] = 0
    
    # Lägg till ISIN (använd B-aktiers ISIN som standard)
    merged['isin'] = ISIN_B
    
    return merged


# --- CACHAD DATA-ENRICHMENT ---
@st.cache_data
def enrich_owner_data(df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Berikar ägardata med förberäknade kolumner för ägartyp, ålder och kön.
    
    Denna funktion körs EN gång och cachas, vilket undviker att is_personnummer()
    och andra tunga funktioner anropas flera gånger för samma data.
    
    Args:
        df: DataFrame med aktieägardata (måste innehålla 'pnrOrgnr')
        reference_date: Referensdatum för åldersberäkning
    
    Returnerar: DataFrame med nya kolumner: is_person, owner_type, age, gender
    """
    if df.empty or 'pnrOrgnr' not in df.columns:
        return df
    
    if reference_date is None:
        reference_date = datetime.today()
    
    result = df.copy()
    
    # 1. Beräkna is_person EN gång per rad
    result['is_person'] = result['pnrOrgnr'].apply(is_personnummer)
    
    # 2. Bestäm owner_type baserat på is_person och namn
    def determine_owner_type(row):
        is_person = row.get('is_person')
        name = str(row.get('name', '')).upper() if pd.notna(row.get('name')) else ''
        
        if is_person is True:
            return 'Fysisk person'
        elif is_person is False:
            return 'Juridisk person'
        else:
            # Oklart - använd namn som hint (COMPANY_INDICATORS från config.py)
            if any(indicator in name for indicator in COMPANY_INDICATORS):
                return 'Juridisk person'
            if ',' in name or (len(name.split()) <= 3 and name):
                return 'Fysisk person'
            return 'Juridisk person'
    
    result['owner_type'] = result.apply(determine_owner_type, axis=1)
    
    # 3. Beräkna ålder för fysiska personer (använd förberäknad is_person)
    def calc_age_if_person(row):
        if row.get('is_person') is not True:
            return None
        return calculate_age_from_personnummer(row['pnrOrgnr'], reference_date)
    
    result['age'] = result.apply(calc_age_if_person, axis=1)
    
    # 4. Klassificera kön för fysiska personer (använd förberäknad is_person)
    def classify_gender_if_person(row):
        if row.get('owner_type') != 'Fysisk person':
            return None
        return classify_gender_from_name(
            row.get('name'), 
            row.get('pnrOrgnr'),
            is_person_precomputed=row.get('is_person')
        )
    
    result['gender'] = result.apply(classify_gender_if_person, axis=1)
    
    return result

# --- SIDEBAR (Konfiguration) ---
st.sidebar.title("KONFIGURATION")

# 1. Hämta Data
st.sidebar.header("Hämta Aktiebok")

# HÅRDKODAT STANDARD-DATUM: Sista dagen i förra månaden
default_date = get_last_month_end_date()

# ISIN och BOLAGSNAMN importeras från config.py

# Input-fält (endast datum, ISIN är hårdkodat)
st.sidebar.write(f"**Bolag:** {BOLAGSNAMN}")

fetch_date = st.sidebar.date_input("Datum", value=default_date, 
                                   help="Välj sista dagen i månaden du vill hämta data för.")

if st.sidebar.button("Hämta Data"):
    if client:
        with st.spinner(f"Hämtar data för {fetch_date}..."):
            try:
                date_str = fetch_date.strftime("%Y-%m-%d")
                all_records = []
                
                # Hämta data för BÅDE A- och B-aktier
                for share_class, isin in [('A', ISIN_A), ('B', ISIN_B)]:
                    response_data = client.get_complete_register(isin, date_str)
                    
                    if response_data and 'holdings' in response_data:
                        holdings_list = response_data['holdings']
                        
                        # Metadata för varje rad
                        metadata = {
                            'isin': response_data.get('isin', isin),
                            'shareClass': share_class,
                            'issuerName': response_data.get('issuerName', 'Unknown'),
                            'holdingDate': response_data.get('holdingDate', date_str),
                            'issuedQuantity': response_data.get('issuedQuantity', 0),
                            'votingRight': response_data.get('votingRight', 1)
                        }
                        
                        # Platta ut
                        for h in holdings_list:
                            record = h.copy()
                            record.update(metadata)
                            record['date'] = metadata['holdingDate'][:10]
                            all_records.append(record)
                        
                        st.sidebar.info(f"Hämtade {len(holdings_list)} {share_class}-aktieägare")
                
                if all_records:
                    # Spara
                    manager.save_data(all_records)
                    st.sidebar.success(f"✅ Hämtade totalt {len(all_records)} poster (A + B aktier)!")
                else:
                    st.sidebar.warning(f"⚠️ Ingen data hittades för {date_str}. (API svarade 204 No Content).")
                    st.sidebar.info("💡 **Tips:** API:et returnerar 204 när data saknas för detta datum. Detta kan bero på:")
                    st.sidebar.markdown("""
                    - Data finns inte för detta specifika datum
                    - Data är inte tillgänglig än (för framtida datum)
                    - För äldre datum: Data kan finnas men kräver specifikt datumformat eller annan endpoint
                    - Försök med sista bankdagen i månaden istället för sista kalenderdagen
                    """)
                    
            except Exception as e:
                error_msg = str(e)
                st.sidebar.error(f"❌ API Fel: {error_msg}")
                
                # Ge mer specifik information om felet
                if "400" in error_msg or "Bad Request" in error_msg:
                    st.sidebar.info("💡 **400 Bad Request:** Kontrollera att datumet är i formatet YYYY-MM-DD och att ISIN är korrekt.")
                elif "401" in error_msg or "Unauthorized" in error_msg:
                    st.sidebar.info("💡 **401 Unauthorized:** Autentisering misslyckades. Kontrollera certifikat och credentials.")
                elif "403" in error_msg or "Forbidden" in error_msg:
                    st.sidebar.info("💡 **403 Forbidden:** Du har inte behörighet att hämta data för detta ISIN eller datum.")
                elif "404" in error_msg:
                    st.sidebar.info("💡 **404 Not Found:** Endpoint eller resurs hittades inte.")
                elif "500" in error_msg:
                    st.sidebar.info("💡 **500 Server Error:** Serverfel hos Euroclear. Försök igen senare.")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-uppdatera (30s)", value=False)

# Initiera lund_inhabitants i session state om det inte finns
if 'lund_inhabitants' not in st.session_state:
    st.session_state['lund_inhabitants'] = DEFAULT_LUND_POPULATION

# --- MAIN DASHBOARD (Huvudvy) ---
st.title("AKTIEÄGARANALYS")

# Ladda historik
df = manager.load_data()

if df.empty:
    st.info("👋 Välkommen! Här kan du utforska våra aktieägares fördelning och trender.")
    st.markdown("""
    **Kom igång:**
    1. Kontrollera att datumet i sidomenyn är korrekt (standard är sista dagen förra månaden).
    2. Klicka på **"Hämta Data"** för att ladda ner aktuell data.
    3. När datan laddats ner kommer analysen att visas automatiskt.
    """)
else:
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Filtrera på båda ISIN (A och B aktier)
    if 'isin' in df.columns:
        filtered_df = df[df['isin'].isin([ISIN_A, ISIN_B])].copy()
    else:
        filtered_df = df.copy()
    
    # KPI
    st.markdown("### Översikt")
    
    latest_date = filtered_df['date'].max()
    latest_data_raw = filtered_df[filtered_df['date'] == latest_date]
    
    # Slå ihop A- och B-aktier per ägare
    latest_data = merge_ab_shares(latest_data_raw)
    
    # Visa senaste datum som liten info-text
    st.caption(f"📅 **Senaste Datum:** {str(latest_date)[:10]}")
    
    # Visa information om A/B-aktier om båda finns
    if 'A_shares' in latest_data.columns and 'B_shares' in latest_data.columns:
        total_a = latest_data['A_shares'].sum()
        total_b = latest_data['B_shares'].sum()
        total_votes = total_a * VOTES_PER_A_SHARE + total_b * VOTES_PER_B_SHARE
        if total_a > 0:
            st.caption(f"📊 **Aktieslag:** {total_a:,} A-aktier (10 röster) + {total_b:,} B-aktier (1 röst) = {total_votes:,} röster")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_holders = len(latest_data)
    total_shares_held = latest_data['holdingsQuantity'].sum() if 'holdingsQuantity' in latest_data.columns else 0
    
    if 'holdingsQuantity' in latest_data.columns:
        # Definition: "storägare" = 500 eller fler (>= 500)
        small_holders = len(latest_data[latest_data['holdingsQuantity'] < 500])
        large_holders = len(latest_data[latest_data['holdingsQuantity'] >= 500])
    else:
        small_holders, large_holders = 0, 0
    
    kpi1.metric("Totalt Antal Ägare", total_holders)
    kpi2.metric("Ägare < 500 Aktier", small_holders)
    kpi3.metric("Ägare ≥ 500 Aktier", large_holders)

    # Analys Tabbar
    st.markdown("### Analys")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Översikt & Trender",
        "Distribution",
        "Geografi (Lund Fokus)",
        "Ägartyper",
        "Cap Table - topp 50"
    ])
    
    # Initiera alla figurer för export
    fig_trend, fig_pen, fig_dist, fig_large, fig_cities, fig_lund = None, None, None, None, None, None

    # TAB 1: Trender
    with tab1:
        st.markdown("#### Trender över tid")
        if 'date' in filtered_df.columns:
            # Räkna antalet unika aktieägare per datum (baserat på pnrOrgnr eller name)
            if 'pnrOrgnr' in filtered_df.columns:
                daily_counts = filtered_df.groupby('date')['pnrOrgnr'].nunique().reset_index(name='Shareholders Count')
            elif 'name' in filtered_df.columns:
                daily_counts = filtered_df.groupby('date')['name'].nunique().reset_index(name='Shareholders Count')
            else:
                # Fallback: räkna rader
                daily_counts = filtered_df.groupby('date').size().reset_index(name='Shareholders Count')
            
            # RAD 1: Kontroller (tidsperiod + förändring i vänstra kolumnen, invånare i högra)
            col_left, col_inhabitants = st.columns([3, 3])
            
            with col_left:
                # Inre kolumner för tidsperiod och förändringskort
                col_period, col_change = st.columns([2, 1])
                
                with col_period:
                    time_period = st.radio("Välj Tidsperiod", ["Max", "YTD", "QTD", "1Y"], horizontal=True)
                    if time_period == "Max":
                        st.caption("**Max** = från tidigast tillgängliga datum (2024-01-31) till senaste datum i datan.")
                    elif time_period == "YTD":
                        st.caption("**YTD** = från stängning föregående år (30 dec) till senaste datum i datan.")
                    elif time_period == "QTD":
                        st.caption("**QTD** = från stängning precis före kvartalsstart (t.ex. sep→okt, dec→jan) till senaste datum i datan.")
                    else:
                        st.caption("**1Y** = senaste 365 dagarna från senaste datum i datan.")
                
                trend_data = filter_by_time_period(daily_counts, 'date', time_period)
                
                with col_change:
                    if not trend_data.empty:
                        start_val = trend_data.sort_values('date').iloc[0]['Shareholders Count']
                        end_val = trend_data.sort_values('date').iloc[-1]['Shareholders Count']
                        abs_change = end_val - start_val
                        pct_change = (abs_change / start_val * 100) if start_val != 0 else 0
                        st.metric(f"Förändring ({time_period})", f"{abs_change:+d}", f"{pct_change:+.2f}%", delta_color="off")
            
            with col_inhabitants:
                st.markdown("#### Marknadspenetration i Lund")
                lund_inhabitants = st.number_input(
                    "Totala Invånare i Lund", 
                    value=st.session_state.get('lund_inhabitants', DEFAULT_LUND_POPULATION), 
                    step=1000, 
                    key='lund_inhabitants_trends',
                    help=f"Befolkningsmängd i Lund (standard: {DEFAULT_LUND_POPULATION:,}, slutet av 2024)"
                )
                st.session_state['lund_inhabitants'] = lund_inhabitants
            
            # RAD 2: Parallella grafer
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                if not trend_data.empty:
                    fig_trend = px.line(trend_data, x='date', y='Shareholders Count', markers=True, 
                                      title="Antal Aktieägare över Tid",
                                      labels={'date': 'Datum', 'Shareholders Count': 'Antal Ägare'},
                                      color_discrete_sequence=[ILOVE_BLUE])
                    apply_brand_layout(fig_trend)
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            with col_t2:
                # Räkna alla aktieägare (inte bara Lundbor)
                if 'pnrOrgnr' in filtered_df.columns:
                    all_shareholders_counts = filtered_df.groupby('date')['pnrOrgnr'].nunique().reset_index(name='Shareholders Count')
                elif 'name' in filtered_df.columns:
                    all_shareholders_counts = filtered_df.groupby('date')['name'].nunique().reset_index(name='Shareholders Count')
                else:
                    all_shareholders_counts = filtered_df.groupby('date').size().reset_index(name='Shareholders Count')
                
                if not all_shareholders_counts.empty:
                    all_shareholders_counts['Penetration %'] = (all_shareholders_counts['Shareholders Count'] / lund_inhabitants) * 100
                    
                    fig_pen = px.line(
                        all_shareholders_counts, 
                        x='date', 
                        y='Penetration %', 
                        markers=True,
                        title=f"Marknadspenetration i Lund (Befolkning: {lund_inhabitants:,})",
                        labels={'date': 'Datum', 'Penetration %': 'Andel av Befolkningen (%)'},
                        color_discrete_sequence=[ILOVE_RED]
                    )
                    fig_pen.update_layout(
                        yaxis=dict(
                            tickformat='.2f',
                            ticksuffix='%'
                        )
                    )
                    apply_brand_layout(fig_pen)
                    st.plotly_chart(fig_pen, use_container_width=True)
                else:
                    st.info("Ingen data tillgänglig.")

    # TAB 2: Distribution (Ägarstruktur)
    with tab2:
        st.markdown("#### Ägarstruktur")
        if 'holdingsQuantity' in latest_data.columns:
            # Storleksklasser enligt årsredovisningsformat
            # Viktigt: Vi vill att "≥ 500" ska inkludera exakt 500.
            # Med right=True måste vi därför bryta vid 499 så att 500 hamnar i sista bucket.
            bins = [0, 50, 100, 200, 300, 400, 499, float('inf')]
            labels = ['Under 50', '51-100', '101-200', '201-300', '301-400', '401-499', '≥ 500']
            dist_data = latest_data.copy()
            dist_data['Size Bucket'] = pd.cut(dist_data['holdingsQuantity'], bins=bins, labels=labels, right=True)
            
            # Räkna ägare per storleksklass
            bucket_counts = dist_data['Size Bucket'].value_counts().reindex(labels, fill_value=0).reset_index()
            bucket_counts.columns = ['Innehavsstorlek', 'Antal Ägare']
            
            # Beräkna antal aktier per storleksklass
            bucket_shares = dist_data.groupby('Size Bucket', observed=True)['holdingsQuantity'].sum().reindex(labels, fill_value=0).reset_index()
            bucket_shares.columns = ['Innehavsstorlek', 'Antal Aktier']
            
            # Slå ihop för komplett tabell
            summary_df = pd.merge(bucket_counts, bucket_shares, on='Innehavsstorlek')
            
            # Beräkna procentandelar
            total_owners = summary_df['Antal Ägare'].sum()
            total_shares = summary_df['Antal Aktier'].sum()
            summary_df['% av Ägare'] = (summary_df['Antal Ägare'] / total_owners * 100).round(1).astype(str) + '%'
            summary_df['% av Aktier'] = (summary_df['Antal Aktier'] / total_shares * 100).round(1).astype(str) + '%'
            
            # Skapa två kolumner: graf och tabell
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                # Horisontell stapelgraf (som i bilden)
                fig_dist = px.bar(
                    bucket_counts, 
                    y='Innehavsstorlek', 
                    x='Antal Ägare', 
                    text='Antal Ägare',
                    title=f"Ägarstruktur {latest_date.year}",
                    orientation='h',
                    color_discrete_sequence=[ILOVE_BLUE]
                )
                fig_dist.update_traces(
                    textposition='inside',
                    textfont=dict(color='white', size=14)
                )
                fig_dist.update_layout(
                    yaxis=dict(
                        categoryorder='array',
                        categoryarray=labels[::-1],  # Omvänd ordning så "Under 50" är överst
                        title='Innehavsstorlek'
                    ),
                    xaxis=dict(title='Antal ägare'),
                    height=400
                )
                apply_brand_layout(fig_dist)
                st.plotly_chart(fig_dist, use_container_width=True)
            
            with col_table:
                # Visa sammanfattningstabell
                st.markdown("##### Sammanfattning")
                
                # Formatera tabellen för visning
                display_df = summary_df[['Innehavsstorlek', 'Antal Aktier', 'Antal Ägare', '% av Aktier', '% av Ägare']].copy()
                display_df['Antal Aktier'] = display_df['Antal Aktier'].apply(lambda x: f"{int(x):,}".replace(",", " "))
                
                # Lägg till totalrad
                total_row = pd.DataFrame([{
                    'Innehavsstorlek': 'Totalt',
                    'Antal Aktier': f"{int(total_shares):,}".replace(",", " "),
                    'Antal Ägare': total_owners,
                    '% av Aktier': '100.0%',
                    '% av Ägare': '100.0%'
                }])
                display_df = pd.concat([display_df, total_row], ignore_index=True)
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Källa
                st.caption(f"Källa: Euroclear Sweden AB {str(latest_date)[:10].replace('-', ' ')}")
            
            # --- Större storleksklasser för storägare ---
            st.markdown("---")
            st.markdown("#### Fördelning storägare")
            
            # Storleksklasser för större innehav
            large_bins = [0, 500, 1000, 5000, 10000, float('inf')]
            large_labels = ['1-500', '501-1 000', '1 001-5 000', '5 001-10 000', '10 000+']
            dist_data['Large Bucket'] = pd.cut(dist_data['holdingsQuantity'], bins=large_bins, labels=large_labels, right=True)
            large_bucket_counts = dist_data['Large Bucket'].value_counts().reindex(large_labels, fill_value=0).reset_index()
            large_bucket_counts.columns = ['Innehavsstorlek', 'Antal Ägare']
            
            # Vertikal stapelgraf för storägare
            fig_large = px.bar(
                large_bucket_counts, 
                x='Innehavsstorlek', 
                y='Antal Ägare', 
                text='Antal Ägare',
                title="Antal Ägare per Storleksklass (större innehav)",
                color_discrete_sequence=[ILOVE_BLUE]
            )
            fig_large.update_traces(textposition='outside')
            # Lägg till marginal ovanför högsta stapeln så att etiketten inte kapas
            max_value = large_bucket_counts['Antal Ägare'].max()
            fig_large.update_layout(
                yaxis=dict(range=[0, max_value * 1.15])  # 15% extra utrymme
            )
            apply_brand_layout(fig_large)
            st.plotly_chart(fig_large, use_container_width=True)

    # TAB 3: Geografi
    with tab3:
        st.markdown("#### Geografisk Analys")
        
        if 'city' in latest_data.columns:
            city_data = latest_data.copy()
            city_data['city_clean'] = city_data['city'].astype(str).str.title().str.strip()
            city_counts = city_data['city_clean'].value_counts()
            
            # Ta topp 10 och lägg till "Övriga" för resten
            top_10_cities = city_counts.head(10)
            other_cities_count = city_counts.iloc[10:].sum() if len(city_counts) > 10 else 0
            
            # Skapa DataFrame med topp 10 + Övriga
            top_cities = top_10_cities.reset_index()
            top_cities.columns = ['Stad', 'Antal Ägare']
            
            if other_cities_count > 0:
                top_cities = pd.concat([
                    top_cities,
                    pd.DataFrame([{'Stad': 'Övriga', 'Antal Ägare': other_cities_count}])
                ], ignore_index=True)
            
            # Skapa kolumnlayout: städer-diagram till vänster, pajdiagram till höger
            col_cities, col_pie = st.columns(2)
            
            with col_cities:
                fig_cities = px.bar(top_cities, x='Stad', y='Antal Ägare', 
                                  title="Antal Ägare per Stad (Topp 10)", 
                                  text_auto=True,
                                  color_discrete_sequence=[ILOVE_BLUE])
                fig_cities.update_traces(textangle=0)
                apply_brand_layout(fig_cities)
                st.plotly_chart(fig_cities, use_container_width=True)
            
            with col_pie:
                # Räkna Lund vs Övriga baserat på postnummer (prefix importeras från config.py)
                pie_data = latest_data.copy()
                
                if 'postalCode' in pie_data.columns:
                    pie_data['postalCode'] = pie_data['postalCode'].astype(str).str.replace(" ", "")
                    pie_data['postal_prefix'] = pie_data['postalCode'].str[:3]
                    lund_count = len(pie_data[pie_data['postal_prefix'].isin(LUND_POSTAL_PREFIXES)])
                    other_count = len(pie_data) - lund_count
                else:
                    # Fallback: använd stadnamn om postnummer saknas
                    pie_data['city_clean'] = pie_data['city'].astype(str).str.title().str.strip()
                    lund_count = len(pie_data[pie_data['city_clean'].str.contains('Lund', case=False, na=False)])
                    other_count = len(pie_data) - lund_count
                
                # Skapa pajdiagram
                pie_df = pd.DataFrame({
                    'Kategori': ['Lund', 'Övriga'],
                    'Antal Ägare': [lund_count, other_count]
                })
                
                fig_pie = px.pie(pie_df, values='Antal Ägare', names='Kategori', 
                                title="Geografisk Fördelning: Lund vs Övriga Orter",
                                color_discrete_sequence=[ILOVE_RED, ILOVE_BLUE])
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                apply_brand_layout(fig_pie)
                st.plotly_chart(fig_pie, use_container_width=True)
            
        st.markdown("---")
        st.markdown("##### Lund Fördjupning (Postnummerområden)")
        if 'city' in latest_data.columns and 'postalCode' in latest_data.columns:
            # Förbättrad filtrering: Använd postnummer för att säkerställa att det verkligen är Lund
            # Postnummerprefix (LUND_POSTAL_PREFIXES) importeras från config.py
            lund_data = latest_data.copy()
            lund_data['postalCode'] = lund_data['postalCode'].astype(str).str.replace(" ", "")
            lund_data['postal_prefix'] = lund_data['postalCode'].str[:3]
            
            # Filtrera på postnummerprefix (mer exakt än bara stadsnamn)
            lund_data = lund_data[lund_data['postal_prefix'].isin(LUND_POSTAL_PREFIXES)].copy()
            
            if not lund_data.empty:
                def get_region_label(prefix):
                    """Hämtar kortnamn för postnummerområdet."""
                    if prefix in POSTCODE_AREAS and POSTCODE_AREAS[prefix]:
                        area_info = POSTCODE_AREAS[prefix]
                        short_name = area_info.get('short_name', '')
                        if short_name:
                            return short_name
                        name = area_info.get('name', '')
                        if name:
                            return name.split(',')[0].split(':')[-1].strip()
                    return f"{prefix} XX"
                
                def get_region_full_info(prefix):
                    """Hämtar fullständig information för hover-tooltip."""
                    if prefix in POSTCODE_AREAS and POSTCODE_AREAS[prefix]:
                        area_info = POSTCODE_AREAS[prefix]
                        name = area_info.get('name', '')
                        if name:
                            return f"{prefix} XX, {name}"
                    return f"{prefix} XX"
                
                def get_prefix_from_label(label):
                    """Hämtar prefix från label genom att matcha mot POSTCODE_AREAS."""
                    if label == 'Övriga':
                        return '999'
                    for prefix, info in POSTCODE_AREAS.items():
                        short_name = info.get('short_name', '')
                        if short_name and short_name == label:
                            return prefix
                        name = info.get('name', '')
                        if name:
                            first_part = name.split(',')[0].split(':')[-1].strip()
                            if first_part == label:
                                return prefix
                    return '999'
                
                def get_full_info_from_label(label):
                    """Hämtar fullständig info från label genom att matcha mot POSTCODE_AREAS."""
                    if label == 'Övriga':
                        return label
                    prefix = get_prefix_from_label(label)
                    if prefix != '999':
                        return get_region_full_info(prefix)
                    return label
                
                lund_data['Region'] = lund_data['postal_prefix'].apply(get_region_label)
                region_counts = lund_data['Region'].value_counts()
                
                # Ta topp postnummerområden och lägg till "Övriga" för resten
                top_regions = region_counts.head(10)
                other_regions_count = region_counts.iloc[10:].sum() if len(region_counts) > 10 else 0
                
                region_df = top_regions.reset_index()
                region_df.columns = ['Postnummerområde', 'Antal Ägare']
                
                if other_regions_count > 0:
                    region_df = pd.concat([
                        region_df,
                        pd.DataFrame([{'Postnummerområde': 'Övriga', 'Antal Ägare': other_regions_count}])
                    ], ignore_index=True)
                
                # Lägg till fullständig information för hover-tooltip
                region_df['Full_Info'] = region_df['Postnummerområde'].apply(get_full_info_from_label)
                
                def sort_key(x):
                    if x == 'Övriga':
                        return (999, 'Övriga')
                    prefix = get_prefix_from_label(x)
                    if prefix != '999':
                        return (int(prefix), x)
                    return (999, x)
                
                region_df['sort_key'] = region_df['Postnummerområde'].apply(sort_key)
                region_df = region_df.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
                
                fig_lund = px.bar(
                    region_df, 
                    x='Postnummerområde', 
                    y='Antal Ägare', 
                    title="Antal Ägare per Postnummerområde i Lund", 
                    text_auto=True,
                    color_discrete_sequence=[ILOVE_BLUE],
                    custom_data=['Full_Info']
                )
                # Lägg till hover-template med fullständig information för staplarna
                fig_lund.update_traces(
                    textangle=0,
                    hovertemplate='<b>%{customdata[0]}</b><br>Antal Ägare: %{y}<extra></extra>'
                )
                
                # Rotera x-axeln för bättre läsbarhet
                fig_lund.update_xaxes(tickangle=-45)
                apply_brand_layout(fig_lund)
                st.plotly_chart(fig_lund, use_container_width=True)
                
                # Visa mer information om områden
                with st.expander("ℹ️ Information om postnummerområden"):
                    for prefix in sorted(LUND_POSTAL_PREFIXES):
                        if prefix in POSTCODE_AREAS and POSTCODE_AREAS[prefix]:
                            info = POSTCODE_AREAS[prefix]
                            st.write(f"**{prefix} XX:**")
                            if info.get('name'):
                                st.write(f"  - Område: {info['name']}")
                            if info.get('main_streets'):
                                streets = [s.split()[0] for s in info['main_streets'][:3]]  # Ta första ordet från top 3 gator
                                st.write(f"  - Vanligaste gatorna: {', '.join(set(streets))}")
                            st.write("")
            else:
                st.info("Ingen data tillgänglig för Lund (baserat på postnummer 221-227 XX).")

    # TAB 4: Ägartyper
    with tab4:
        st.markdown("#### Analys av Fysiska vs Juridiska Personer")
        
        if 'pnrOrgnr' not in latest_data.columns:
            st.warning("⚠️ Data saknar 'pnrOrgnr'-kolumn. Kan inte analysera ägartyper.")
        else:
            # Använd cachad funktion för att berika data (beräknar is_person, owner_type, age, gender EN gång)
            analysis_df = enrich_owner_data(latest_data, reference_date=latest_date.to_pydatetime() if hasattr(latest_date, 'to_pydatetime') else latest_date)
            
            # Debug: Visa fördelning
            type_counts_debug = analysis_df['owner_type'].value_counts()
            if 'Okänt' in type_counts_debug.index and type_counts_debug['Okänt'] > 0:
                st.info(f"ℹ️ **Debug:** {type_counts_debug['Okänt']} ägare kunde inte klassificeras som fysisk eller juridisk person.")
            
            # Filtrera bort okända
            known_types_df = analysis_df[analysis_df['owner_type'] != 'Okänt'].copy()
            
            # Om alla är "Okänt", visa varning och inkludera dem ändå för analys
            if known_types_df.empty and not analysis_df.empty:
                st.warning("⚠️ Kunde inte identifiera några ägartyper. Visar alla ägare som 'Okänt'.")
                known_types_df = analysis_df.copy()
            
            if not known_types_df.empty:
                physical_df = known_types_df[known_types_df['owner_type'] == 'Fysisk person']
                
                # Använd separata renderingsfunktioner från tabs-modulen
                render_gender_analysis(physical_df)
                render_age_analysis(physical_df)
                render_owner_type_comparison(known_types_df, physical_df)
            else:
                st.warning("⚠️ Kunde inte identifiera ägartyper i datan.")

    # TAB 5: Cap Table - topp 50 (nivå, förändring och historik)
    with tab5:
        st.markdown("#### Cap Table - topp 50, placering och förändring")

        # Samma lösenords-skydd som för rådata
        if not st.session_state.get('data_access_authenticated', False):
            st.warning("⚠️ **GDPR-varning:** Cap Table innehåller känsliga personuppgifter.")

            col1, col2 = st.columns([2, 1])
            with col1:
                cap_password = st.text_input(
                    "Lösenord för att visa fullständig Cap Table:",
                    type="password",
                    help="Samma lösenord som används för att låsa upp rådata längst ned på sidan.",
                    key="cap_table_password"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("🔓 Avanonymisera Cap Table", type="primary", key="cap_table_unlock"):
                    stored_hash = get_password_hash()
                    if verify_password(cap_password, stored_hash):
                        st.session_state['data_access_authenticated'] = True
                        st.success("✅ Autentisering lyckades! Cap Table låst upp.")
                        st.rerun()
                    else:
                        st.error("❌ Felaktigt lösenord!")

            st.info("💡 Du kan också låsa upp data via sektionen **\"Visa Rådata\"** längst ned på sidan.")
        else:
            if 'holdingsQuantity' not in latest_data.columns:
                st.warning("⚠️ Data saknar 'holdingsQuantity'-kolumn. Kan inte visa topp 50-tabell.")
            else:
                # Hitta referensdatum ett år tillbaka
                ref_date = get_reference_date_one_year_back(filtered_df, latest_date)

                if ref_date is None:
                    st.info("ℹ️ Ingen historik tillgänglig ett år tillbaka. Visar endast nuvarande topp 50 utan pilar.")
                    ref_data = None
                else:
                    ref_data_raw = filtered_df[filtered_df['date'] == ref_date].copy()
                    # Slå ihop A- och B-aktier för referensdatum
                    ref_data = merge_ab_shares(ref_data_raw)
                    st.caption(f"📅 Jämförelse mot referensdatum: {str(ref_date)[:10]}")

                # Bygg snapshots
                current_snapshot = build_owner_snapshot(
                    latest_data,
                    quantity_col='holdingsQuantity',
                    prefix='current'
                )
                ref_snapshot = None
                if ref_data is not None and not ref_data.empty:
                    ref_snapshot = build_owner_snapshot(
                        ref_data,
                        quantity_col='holdingsQuantity',
                        prefix='ref'
                    )

                top50_df = build_top50_comparison(current_snapshot, ref_snapshot, top_n=50)

                if top50_df.empty:
                    st.info("Ingen data att visa i topp 50-tabellen.")
                else:
                    # Visa tabellen utan överflödig index-kolumn
                    st.dataframe(top50_df, use_container_width=True, hide_index=True)

                    st.markdown("###### Förklaring")
                    st.markdown("""
- **Rank (nu)**: Ägarens position baserat på antal aktier vid senaste datumet.
- **Rank-förändring**: Pil och siffra som visar hur många placeringar ägaren har klättrat (↑) eller tappat (↓) jämfört med referensdatum. `"Ny"` betyder ny ägare.
- **Förändring Holding Quantity**: Pil och antal aktier som ägandet har ökat (↑) eller minskat (↓) med jämfört med referensdatum. `→ 0` betyder oförändrat, `Ny ↑` betyder ny ägare.
- **Obs:** Personer som äger aktier både i eget namn (fysisk person) och via bolag visas som separata rader och aggregeras inte.
""")

    # --- RAPPORT ---
    st.markdown("---")
    st.subheader("📤 Dela Rapport")
    if st.button("Generera HTML-rapport"):
        report_filename = f"Aktieagarrapport_{datetime.now().strftime('%Y-%m-%d')}.html"
        try:
            import base64
            import glob
            
            # Läs in logotypen och konvertera till base64
            logo_base64 = ""
            logo_files = glob.glob(os.path.join(os.path.dirname(os.path.dirname(__file__)), '*ILL*AB*.png'))
            if logo_files:
                with open(logo_files[0], 'rb') as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
            
            # Skapa komplett HTML-rapport med alla grafer och information
            html_content_parts = []
            html_content_parts.append("<!DOCTYPE html>\n<html lang='sv'>\n<head>")
            html_content_parts.append("<meta charset='UTF-8'>")
            html_content_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
            html_content_parts.append("<title>Aktieägarrapport - I Love Lund</title>")
            html_content_parts.append("<style>")
            # Brand Book CSS - I Love Lund
            html_content_parts.append("""
                @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600&display=swap');
                
                :root {
                    --ilove-red: #e30413;
                    --ilove-blue: #25408d;
                    --ilove-white: #ffffff;
                    --ilove-grey: #f6f6f6;
                    --ilove-dark-grey: #2f2f2f;
                }
                
                * { box-sizing: border-box; }
                
                body {
                    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Open Sans', sans-serif;
                    font-weight: 300;
                    margin: 0;
                    padding: 20px;
                    background-color: var(--ilove-grey);
                    color: var(--ilove-dark-grey);
                    line-height: 1.6;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: var(--ilove-white);
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }
                
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 4px solid var(--ilove-red);
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }
                
                .header-logo {
                    max-height: 80px;
                    width: auto;
                }
                
                .header-title {
                    text-align: right;
                }
                
                h1 {
                    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, sans-serif;
                    font-weight: 600;
                    color: var(--ilove-red);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin: 0;
                    font-size: 28px;
                }
                
                .header-date {
                    color: var(--ilove-blue);
                    font-size: 16px;
                    margin-top: 5px;
                }
                
                h2 {
                    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, sans-serif;
                    font-weight: 600;
                    color: var(--ilove-red);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-top: 40px;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid var(--ilove-grey);
                    font-size: 20px;
                }
                
                h3 {
                    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, sans-serif;
                    font-weight: 400;
                    color: var(--ilove-blue);
                    margin-top: 25px;
                    font-size: 16px;
                }
                
                .kpi-container {
                    display: flex;
                    gap: 20px;
                    margin: 25px 0;
                    flex-wrap: wrap;
                }
                
                .kpi-box {
                    background: linear-gradient(135deg, var(--ilove-blue) 0%, #1a2d5a 100%);
                    color: var(--ilove-white);
                    padding: 25px;
                    border-radius: 8px;
                    flex: 1;
                    min-width: 200px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(37,64,141,0.2);
                }
                
                .kpi-box.highlight {
                    background: linear-gradient(135deg, var(--ilove-red) 0%, #b00310 100%);
                    box-shadow: 0 2px 10px rgba(227,4,19,0.2);
                }
                
                .kpi-label {
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    opacity: 0.9;
                    margin-bottom: 8px;
                }
                
                .kpi-value {
                    font-size: 32px;
                    font-weight: 600;
                }
                
                .chart-container {
                    margin: 30px 0;
                    padding: 25px;
                    background-color: var(--ilove-grey);
                    border-radius: 8px;
                    border-left: 4px solid var(--ilove-blue);
                }
                
                .two-col {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                }
                
                @media (max-width: 768px) {
                    .two-col { grid-template-columns: 1fr; }
                    .kpi-container { flex-direction: column; }
                    .header { flex-direction: column; text-align: center; }
                    .header-title { text-align: center; margin-top: 15px; }
                }
                
                .section-divider {
                    border: none;
                    border-top: 2px solid var(--ilove-grey);
                    margin: 40px 0;
                }
                
                .footer {
                    margin-top: 50px;
                    padding-top: 25px;
                    border-top: 4px solid var(--ilove-red);
                    text-align: center;
                    color: var(--ilove-dark-grey);
                    font-size: 14px;
                }
                
                .footer-contact {
                    margin-top: 10px;
                    color: var(--ilove-blue);
                }
                
                .footer-logo {
                    max-height: 50px;
                    margin-bottom: 15px;
                    opacity: 0.8;
                }
                
                @media print {
                    body { background: white; padding: 0; }
                    .container { box-shadow: none; padding: 20px; }
                    .chart-container { break-inside: avoid; }
                }
            """)
            html_content_parts.append("</style>")
            html_content_parts.append("</head>\n<body>")
            html_content_parts.append("<div class='container'>")
            
            # Header med logotyp
            html_content_parts.append("<div class='header'>")
            if logo_base64:
                html_content_parts.append(f"<img src='data:image/png;base64,{logo_base64}' alt='I Love Lund' class='header-logo'>")
            html_content_parts.append("<div class='header-title'>")
            html_content_parts.append("<h1>Aktieägarrapport</h1>")
            html_content_parts.append(f"<div class='header-date'>Rapportdatum: {str(latest_date)[:10]}</div>")
            html_content_parts.append("</div></div>")
            
            # KPI-sektion
            html_content_parts.append("<h2>Översikt</h2>")
            html_content_parts.append("<div class='kpi-container'>")
            html_content_parts.append(f"<div class='kpi-box highlight'><div class='kpi-label'>Senaste Datum</div><div class='kpi-value'>{str(latest_date)[:10]}</div></div>")
            html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>Totalt Antal Ägare</div><div class='kpi-value'>{total_holders:,}</div></div>")
            html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>Ägare &lt; 500 Aktier</div><div class='kpi-value'>{small_holders:,}</div></div>")
            html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>Ägare ≥ 500 Aktier</div><div class='kpi-value'>{large_holders:,}</div></div>")
            html_content_parts.append("</div>")
            
            # A/B-aktier information
            if 'A_shares' in latest_data.columns and 'B_shares' in latest_data.columns:
                total_a = latest_data['A_shares'].sum()
                total_b = latest_data['B_shares'].sum()
                total_votes = total_a * VOTES_PER_A_SHARE + total_b * VOTES_PER_B_SHARE
                if total_a > 0:
                    html_content_parts.append("<div class='kpi-container'>")
                    html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>A-aktier (10 röster)</div><div class='kpi-value'>{total_a:,}</div></div>")
                    html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>B-aktier (1 röst)</div><div class='kpi-value'>{total_b:,}</div></div>")
                    html_content_parts.append(f"<div class='kpi-box'><div class='kpi-label'>Totalt Röster</div><div class='kpi-value'>{total_votes:,}</div></div>")
                    html_content_parts.append("</div>")
            
            # === SEKTION 1: TRENDER ===
            if fig_trend:
                html_content_parts.append("<h2>Trender över Tid</h2>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_trend, full_html=False, include_plotlyjs='cdn')
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            # Marknadspenetration
            if fig_pen:
                html_content_parts.append("<h3>Marknadspenetration i Lund</h3>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_pen, full_html=False, include_plotlyjs=False)
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            # === SEKTION 2: ÄGARSTRUKTUR ===
            if fig_dist:
                html_content_parts.append("<h2>Ägarstruktur</h2>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_dist, full_html=False, include_plotlyjs=False)
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            # Fördelning storägare
            if fig_large:
                html_content_parts.append("<h3>Fördelning Storägare</h3>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_large, full_html=False, include_plotlyjs=False)
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            # === SEKTION 3: GEOGRAFI ===
            html_content_parts.append("<h2>Geografisk Analys</h2>")
            if fig_cities:
                html_content_parts.append("<h3>Topp 10 Städer</h3>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_cities, full_html=False, include_plotlyjs=False)
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            if fig_lund:
                html_content_parts.append("<h3>Lund - Postnummerområden</h3>")
                html_content_parts.append("<div class='chart-container'>")
                plotly_html = pio.to_html(fig_lund, full_html=False, include_plotlyjs=False)
                html_content_parts.append(plotly_html)
                html_content_parts.append("</div>")
            
            # === SEKTION 4: ÄGARTYPER ===
            # Skapa grafer för Ägartyper-sektionen
            if 'pnrOrgnr' in latest_data.columns:
                html_content_parts.append("<h2>Ägartypsanalys</h2>")
                
                # Berika data för ägartypsanalys
                analysis_df = enrich_owner_data(latest_data, reference_date=latest_date.to_pydatetime() if hasattr(latest_date, 'to_pydatetime') else latest_date)
                known_types_df = analysis_df[analysis_df['owner_type'] != 'Okänt'].copy()
                
                if not known_types_df.empty:
                    physical_df = known_types_df[known_types_df['owner_type'] == 'Fysisk person']
                    
                    # --- Könsfördelning ---
                    if not physical_df.empty and 'gender' in physical_df.columns:
                        gender_df = physical_df[physical_df['gender'].notna()].copy()
                        if not gender_df.empty:
                            gender_counts = gender_df['gender'].value_counts()
                            gender_counts_for_chart = gender_counts[gender_counts > 0]
                            
                            if not gender_counts_for_chart.empty:
                                html_content_parts.append("<h3>Könsfördelning - Fysiska Personer</h3>")
                                html_content_parts.append("<div class='chart-container'>")
                                html_content_parts.append("<div class='two-col'>")
                                
                                # Pie chart för antal ägare per kön
                                fig_gender = px.pie(
                                    values=gender_counts_for_chart.values,
                                    names=gender_counts_for_chart.index,
                                    title="Könsfördelning: Antal Ägare",
                                    color_discrete_sequence=[ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY]
                                )
                                fig_gender.update_layout(
                                    plot_bgcolor=ILOVE_WHITE,
                                    paper_bgcolor=ILOVE_WHITE,
                                    font_family="Gill Sans, sans-serif",
                                    title_font_color=ILOVE_RED
                                )
                                plotly_html = pio.to_html(fig_gender, full_html=False, include_plotlyjs=False)
                                html_content_parts.append(f"<div>{plotly_html}</div>")
                                
                                # Pie chart för holding percentage per kön
                                if 'holdingsPercentage' in gender_df.columns:
                                    gender_summary = gender_df.groupby('gender').agg({'holdingsPercentage': 'sum'}).reset_index()
                                    gender_summary = gender_summary[gender_summary['holdingsPercentage'] > 0]
                                    if not gender_summary.empty:
                                        fig_gender_pct = px.pie(
                                            values=gender_summary['holdingsPercentage'].values,
                                            names=gender_summary['gender'].values,
                                            title="Könsfördelning: Andel av Ägande (%)",
                                            color_discrete_sequence=[ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY]
                                        )
                                        fig_gender_pct.update_layout(
                                            plot_bgcolor=ILOVE_WHITE,
                                            paper_bgcolor=ILOVE_WHITE,
                                            font_family="Gill Sans, sans-serif",
                                            title_font_color=ILOVE_RED
                                        )
                                        plotly_html = pio.to_html(fig_gender_pct, full_html=False, include_plotlyjs=False)
                                        html_content_parts.append(f"<div>{plotly_html}</div>")
                                
                                html_content_parts.append("</div></div>")
                    
                    # --- Åldersfördelning ---
                    if not physical_df.empty and 'age' in physical_df.columns and physical_df['age'].notna().any():
                        html_content_parts.append("<h3>Åldersfördelning - Fysiska Personer</h3>")
                        html_content_parts.append("<div class='chart-container'>")
                        html_content_parts.append("<div class='two-col'>")
                        
                        # Histogram över åldrar
                        fig_age_hist = px.histogram(
                            physical_df,
                            x='age',
                            nbins=20,
                            title="Åldersfördelning: Antal Ägare per Åldersgrupp",
                            labels={'age': 'Ålder (år)', 'count': 'Antal Ägare'},
                            color_discrete_sequence=[ILOVE_RED]
                        )
                        fig_age_hist.update_layout(
                            plot_bgcolor=ILOVE_WHITE,
                            paper_bgcolor=ILOVE_WHITE,
                            font_family="Gill Sans, sans-serif",
                            title_font_color=ILOVE_RED
                        )
                        plotly_html = pio.to_html(fig_age_hist, full_html=False, include_plotlyjs=False)
                        html_content_parts.append(f"<div>{plotly_html}</div>")
                        
                        # Boxplot
                        fig_age_box = px.box(
                            physical_df,
                            y='age',
                            title="Åldersöversikt: Median, Kvartiler och Spridning",
                            labels={'age': 'Ålder (år)'},
                            color_discrete_sequence=[ILOVE_RED]
                        )
                        fig_age_box.update_layout(
                            plot_bgcolor=ILOVE_WHITE,
                            paper_bgcolor=ILOVE_WHITE,
                            font_family="Gill Sans, sans-serif",
                            title_font_color=ILOVE_RED
                        )
                        plotly_html = pio.to_html(fig_age_box, full_html=False, include_plotlyjs=False)
                        html_content_parts.append(f"<div>{plotly_html}</div>")
                        
                        html_content_parts.append("</div></div>")
                    
                    # --- Fysiska vs Juridiska personer ---
                    type_counts = known_types_df['owner_type'].value_counts()
                    type_counts_for_chart = type_counts[type_counts > 0]
                    
                    if not type_counts_for_chart.empty:
                        html_content_parts.append("<h3>Fysiska vs Juridiska Personer</h3>")
                        html_content_parts.append("<div class='chart-container'>")
                        
                        fig_type = px.pie(
                            values=type_counts_for_chart.values,
                            names=type_counts_for_chart.index,
                            title="Fördelning: Fysiska vs Juridiska Personer",
                            color_discrete_sequence=[ILOVE_RED, ILOVE_BLUE]
                        )
                        fig_type.update_layout(
                            plot_bgcolor=ILOVE_WHITE,
                            paper_bgcolor=ILOVE_WHITE,
                            font_family="Gill Sans, sans-serif",
                            title_font_color=ILOVE_RED
                        )
                        plotly_html = pio.to_html(fig_type, full_html=False, include_plotlyjs=False)
                        html_content_parts.append(plotly_html)
                        html_content_parts.append("</div>")
            
            # Cap Table - topp 50 (endast om data är upplåst)
            if st.session_state.get('data_access_authenticated', False):
                if 'holdingsQuantity' in latest_data.columns:
                    html_content_parts.append("<h2>Cap Table - Topp 50 Ägare</h2>")
                    html_content_parts.append("<div class='chart-container'>")
                    
                    # Hitta referensdatum ett år tillbaka
                    ref_date = get_reference_date_one_year_back(filtered_df, latest_date)
                    ref_data_report = None
                    if ref_date is not None:
                        ref_data_raw = filtered_df[filtered_df['date'] == ref_date].copy()
                        # Slå ihop A- och B-aktier för referensdatum
                        ref_data_report = merge_ab_shares(ref_data_raw)
                    
                    # Bygg snapshots
                    current_snapshot = build_owner_snapshot(
                        latest_data,
                        quantity_col='holdingsQuantity',
                        prefix='current'
                    )
                    ref_snapshot = None
                    if ref_data_report is not None and not ref_data_report.empty:
                        ref_snapshot = build_owner_snapshot(
                            ref_data_report,
                            quantity_col='holdingsQuantity',
                            prefix='ref'
                        )
                    
                    top50_df = build_top50_comparison(current_snapshot, ref_snapshot, top_n=50)
                    
                    if not top50_df.empty:
                        # Skapa HTML-tabell med styling
                        html_content_parts.append("""
                        <style>
                            .cap-table {
                                width: 100%;
                                border-collapse: collapse;
                                font-size: 14px;
                                margin: 20px 0;
                            }
                            .cap-table th {
                                background-color: var(--ilove-blue);
                                color: white;
                                padding: 12px 8px;
                                text-align: left;
                                font-weight: 600;
                            }
                            .cap-table td {
                                padding: 10px 8px;
                                border-bottom: 1px solid #eee;
                            }
                            .cap-table tr:nth-child(even) {
                                background-color: var(--ilove-grey);
                            }
                            .cap-table tr:hover {
                                background-color: #e8e8e8;
                            }
                            .rank-up { color: #28a745; font-weight: bold; }
                            .rank-down { color: var(--ilove-red); font-weight: bold; }
                            .rank-new { color: var(--ilove-blue); font-weight: bold; }
                        </style>
                        """)
                        
                        html_content_parts.append("<table class='cap-table'>")
                        html_content_parts.append("<thead><tr>")
                        for col in top50_df.columns:
                            html_content_parts.append(f"<th>{col}</th>")
                        html_content_parts.append("</tr></thead>")
                        html_content_parts.append("<tbody>")
                        
                        for _, row in top50_df.iterrows():
                            html_content_parts.append("<tr>")
                            for col in top50_df.columns:
                                val = str(row[col])
                                # Formatera rank-förändring och förändring med färg
                                if col == 'Rank-förändring':
                                    if '↑' in val:
                                        val = f"<span class='rank-up'>{val}</span>"
                                    elif '↓' in val:
                                        val = f"<span class='rank-down'>{val}</span>"
                                    elif 'Ny' in val:
                                        val = f"<span class='rank-new'>{val}</span>"
                                elif col in ['Förändring', 'Förändring Holding Quantity']:
                                    if '↑' in val and 'Ny' not in val:
                                        val = f"<span class='rank-up'>{val}</span>"
                                    elif '↓' in val:
                                        val = f"<span class='rank-down'>{val}</span>"
                                    elif 'Ny' in val:
                                        val = f"<span class='rank-new'>{val}</span>"
                                html_content_parts.append(f"<td>{val}</td>")
                            html_content_parts.append("</tr>")
                        
                        html_content_parts.append("</tbody></table>")
                        
                        if ref_date:
                            html_content_parts.append(f"<p style='font-size: 12px; color: #666;'>📅 Jämförelse mot referensdatum: {str(ref_date)[:10]}</p>")
                        else:
                            html_content_parts.append("<p style='font-size: 12px; color: #666;'>ℹ️ Ingen historik tillgänglig ett år tillbaka.</p>")
                        
                        # Förklaring av kolumner
                        html_content_parts.append("""
                        <p style='font-size: 11px; color: #888; margin-top: 15px;'>
                        <strong>Obs:</strong> Personer som äger aktier både i eget namn (fysisk person) och via bolag visas som separata rader och aggregeras inte.
                        </p>
                        """)
                    
                    html_content_parts.append("</div>")
            else:
                # Data är inte upplåst - visa meddelande
                html_content_parts.append("<h2>Cap Table - Topp 50 Ägare</h2>")
                html_content_parts.append("<div class='chart-container'>")
                html_content_parts.append("""
                <div style='padding: 40px; text-align: center; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;'>
                    <p style='font-size: 18px; color: #856404;'>🔒 <strong>Cap Table är skyddad</strong></p>
                    <p style='color: #856404;'>För att inkludera Cap Table topp 50 i rapporten, avanonymisera först datan i dashboard-appen genom att ange lösenord.</p>
                </div>
                """)
                html_content_parts.append("</div>")
            
            # Footer
            html_content_parts.append("<div class='footer'>")
            if logo_base64:
                html_content_parts.append(f"<img src='data:image/png;base64,{logo_base64}' alt='I Love Lund' class='footer-logo'>")
            html_content_parts.append("<p>Denna rapport är genererad från <strong>Vantage API</strong>.</p>")
            html_content_parts.append("<p class='footer-contact'>Skapad av <strong>Axel Lundberg</strong> · Vid frågor: <strong>0705227904</strong></p>")
            html_content_parts.append("</div>")
            
            html_content_parts.append("</div>")
            html_content_parts.append("</body>\n</html>")
            full_html_content = "".join(html_content_parts)
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(full_html_content)
            st.success(f"Rapport klar: {report_filename}")
            with open(report_filename, "rb") as file:
                file_data = file.read()
                st.download_button("Ladda ner", file_data, report_filename, "text/html")
        except Exception as e:
            st.error(f"Fel: {e}")
            import traceback
            st.code(traceback.format_exc())

    with st.expander("Visa Rådata"):
        # Lösenordsautentisering för avanonymisering
        if not st.session_state['data_access_authenticated']:
            st.warning("⚠️ **GDPR-varning:** Personuppgifter är anonymiserade för att skydda integriteten.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                password_input = st.text_input(
                    "Lösenord för att visa fullständig data:",
                    type="password",
                    help="Ange lösenord för att avanonymisera och visa alla personuppgifter",
                    key="data_access_password"
                )
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("🔓 Avanonymisera", type="primary"):
                    stored_hash = get_password_hash()
                    if verify_password(password_input, stored_hash):
                        st.session_state['data_access_authenticated'] = True
                        st.success("✅ Autentisering lyckades!")
                        st.rerun()
                    else:
                        st.error("❌ Felaktigt lösenord!")
            
            # Visa anonymiserad data
            display_df = filtered_df.copy()
            
            # Anonymisera känsliga personuppgifter
            def anonymize_pnr(x):
                """Anonymisera personnummer: XX***XX"""
                x_str = str(x)
                if x_str and x_str != 'nan' and len(x_str) > 4:
                    return f"{x_str[:2]}***{x_str[-2:]}"
                return "***"
            
            def anonymize_name(x):
                """Anonymisera namn: A***"""
                x_str = str(x)
                if x_str and x_str != 'nan' and len(x_str) > 0:
                    return f"{x_str[0]}***"
                return "***"
            
            def anonymize_address(x):
                """Anonymisera adress: Första ordet + ***"""
                x_str = str(x)
                if x_str and x_str != 'nan':
                    parts = x_str.split()
                    if len(parts) > 0:
                        return f"{parts[0]}***"
                return "***"
            
            # Applicera anonymisering
            if 'pnrOrgnr' in display_df.columns:
                display_df['pnrOrgnr'] = display_df['pnrOrgnr'].apply(anonymize_pnr)
            if 'name' in display_df.columns:
                display_df['name'] = display_df['name'].apply(anonymize_name)
            if 'streetAddress' in display_df.columns:
                display_df['streetAddress'] = display_df['streetAddress'].apply(anonymize_address)
            if 'coAdress' in display_df.columns:
                display_df['coAdress'] = display_df['coAdress'].apply(anonymize_address)
            
            # Visa endast relevanta kolumner för analys (exkludera känsliga fält helt)
            safe_columns = [col for col in display_df.columns if col not in ['streetAddress', 'coAdress']]
            display_df = display_df[safe_columns]
            
            st.dataframe(display_df, use_container_width=True)
            
            st.info("💡 **Tips:** Ange lösenord ovan för att visa fullständig data. Se GDPR_GUIDE.md för mer information om dataskydd.")
        
        else:
            # Användare är autentiserad - visa fullständig data
            st.success("🔓 **Fullständig data visas** - Du är autentiserad.")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.warning("⚠️ **Varning:** Du ser nu känsliga personuppgifter. Hantera denna information enligt GDPR.")
            with col2:
                if st.button("🔒 Anonymisera igen", type="secondary"):
                    st.session_state['data_access_authenticated'] = False
                    st.rerun()
            
            # Visa fullständig data
            st.dataframe(filtered_df, use_container_width=True)
            
            st.info("💡 **Säkerhet:** Logga ut genom att klicka på 'Anonymisera igen' när du är klar. Sessionen sparas tills du loggar ut eller laddar om sidan.")

if auto_refresh:
    time.sleep(30)
    st.rerun()

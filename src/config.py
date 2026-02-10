"""
Konfigurationsfil för Vantage Dashboard.

Samlar alla konstanter, färger och inställningar på ett ställe
för enklare underhåll och konsekvent användning.
"""

import pandas as pd

# =============================================================================
# BRAND BOOK - I Love Lund Färgpalett
# =============================================================================
ILOVE_RED = "#e30413"
ILOVE_BLUE = "#25408d"
ILOVE_WHITE = "#ffffff"
ILOVE_GREY = "#f6f6f6"
ILOVE_BLACK = "#000000"
ILOVE_DARK_GREY = "#2f2f2f"

# Plotly färgpalett (ordning för grafer)
ILOVE_COLORS = [ILOVE_RED, ILOVE_BLUE, ILOVE_DARK_GREY, ILOVE_GREY]

# Färgmappning för specifika kategorier
GENDER_COLORS = {
    'Man': ILOVE_BLUE,
    'Kvinna': ILOVE_RED,
    'Okänt': ILOVE_DARK_GREY
}

OWNER_TYPE_COLORS = {
    'Fysisk person': ILOVE_RED,
    'Juridisk person': ILOVE_BLUE
}


# =============================================================================
# BOLAGSINFORMATION
# =============================================================================
# A-aktier har 10 röster per aktie, B-aktier har 1 röst per aktie
ISIN_A = "SE0018397630"  # A-aktier (10 röster/aktie)
ISIN_B = "SE0018397648"  # B-aktier (1 röst/aktie)
ISIN = ISIN_B  # Bakåtkompatibilitet - default till B-aktier
BOLAGSNAMN = "I Love Lund AB"

# Röstvärden per aktieslag
VOTES_PER_A_SHARE = 10
VOTES_PER_B_SHARE = 1


# =============================================================================
# DATUMGRÄNSER
# =============================================================================
# Tidigast tillgängliga datum i Euroclear-datan
EARLIEST_AVAILABLE_DATE = pd.Timestamp("2024-01-31")


# =============================================================================
# LUND-SPECIFIKA INSTÄLLNINGAR
# =============================================================================
# Befolkningsmängd i Lund (slutet av 2024)
DEFAULT_LUND_POPULATION = 131_590

# Postnummerprefix för Lund (221 XX - 227 XX)
LUND_POSTAL_PREFIXES = ['221', '222', '223', '224', '225', '226', '227']


# =============================================================================
# STORLEKSKLASSER FÖR DISTRIBUTION
# =============================================================================
# Standard storleksklasser för ägarfördelning
SIZE_BUCKETS = {
    'bins': [0, 500, 1000, 5000, 10000, float('inf')],
    'labels': ['1-500', '501-1,000', '1,001-5,000', '5,001-10,000', '10,000+']
}

# Storleksklasser för årsredovisning (mer detaljerade)
SIZE_BUCKETS_ANNUAL_REPORT = {
    'bins': [0, 50, 100, 200, 300, 400, 500, float('inf')],
    'labels': ['Under 50', '51-100', '101-200', '201-300', '301-400', '401-500', '500+']
}


# =============================================================================
# FÖRETAGSIDENTIFIERING
# =============================================================================
# Indikatorer i namn som tyder på juridisk person (företag)
COMPANY_INDICATORS = [
    'AB', 'AKTIEBOLAG', 'AKTIE AB', 'INVEST', 'FÖRSÄKRING',
    'PENSION', 'FÖRVALTNING', 'HOLDING', 'PARTNER', 'LABS',
    'INDUSTRIES', 'WORLDWIDE', 'WEALTH', 'MANAGEMENT', 'PUBL',
    'HANDELSBOLAG', 'HB', 'KB', 'KOMMANDITBOLAG', 'STIFTELSE',
    'FÖRENING', 'EKONOMISK FÖRENING', 'BOSTADSRÄTTSFÖRENING'
]


# =============================================================================
# DASHBOARD-INSTÄLLNINGAR
# =============================================================================
# Sidkonfiguration
PAGE_TITLE = "Aktieägaranalys Dashboard - I Love Lund"
PAGE_ICON = "📊"  # Fallback om favicon saknas

# Auto-refresh intervall (sekunder)
AUTO_REFRESH_INTERVAL = 30

# Antal ägare i Cap Table
TOP_OWNERS_COUNT = 50


# =============================================================================
# HJÄLPFUNKTIONER FÖR FÄRGER
# =============================================================================
def get_color_sequence(categories: list, color_map: dict, default_colors: list = None) -> list:
    """
    Returnerar en lista med färger baserat på kategorier och färgmappning.
    
    Args:
        categories: Lista med kategorier (t.ex. ['Man', 'Kvinna'])
        color_map: Dict med kategori -> färg mappning
        default_colors: Fallback-färger om kategori saknas i mappningen
    
    Returns:
        Lista med färgkoder
    """
    if default_colors is None:
        default_colors = ILOVE_COLORS
    
    colors = []
    for i, cat in enumerate(categories):
        if cat in color_map:
            colors.append(color_map[cat])
        elif i < len(default_colors):
            colors.append(default_colors[i])
        else:
            colors.append(ILOVE_DARK_GREY)
    
    return colors


"""
Renderingsfunktioner för Ägartyper-fliken (Tab 4).

Innehåller:
- render_gender_analysis: Könsfördelning för fysiska personer
- render_age_analysis: Åldersfördelning för fysiska personer
- render_owner_type_comparison: Jämförelse fysiska vs juridiska personer
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# Importera konfiguration och hjälpfunktioner
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    ILOVE_RED, ILOVE_BLUE, ILOVE_DARK_GREY,
    GENDER_COLORS, OWNER_TYPE_COLORS,
    get_color_sequence
)


def apply_brand_layout(fig):
    """Applicerar I Love Lund brand book layout på Plotly-figurer."""
    from config import ILOVE_WHITE, ILOVE_RED, ILOVE_DARK_GREY
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


def render_gender_analysis(physical_df: pd.DataFrame) -> None:
    """
    Renderar könsfördelningsanalysen för fysiska personer.
    
    Args:
        physical_df: DataFrame med endast fysiska personer, måste innehålla 'gender'-kolumn
    """
    if physical_df.empty or 'gender' not in physical_df.columns:
        st.info("Ingen könsdata tillgänglig för fysiska personer.")
        return
    
    st.markdown("---")
    st.markdown("##### Könsfördelning: Fysiska Personer")
    
    # Expanderbar förklaring
    with st.expander("ℹ️ Om könsklassificeringen"):
        st.markdown("""
        **Om könsklassificeringen:**
        
        Könsfördelningen baseras på automatisk analys av förnamn. Systemet klassificerar endast fysiska personer (inte juridiska personer/företag).
        
        **"Okänt"** inkluderar:
        - Unisex-namn (namn som kan tillhöra både män och kvinnor)
        - Ovanliga eller utländska namn som systemet inte kan identifiera
        - Initialer eller förkortningar
        - Namn där kön inte kunde bestämmas med säkerhet
        - Juridiska personer (som av misstag kan ha klassificerats som fysiska personer)
        
        **⚠️ Viktigt:** Indelningen kan ibland bli fel. Systemet gör sitt bästa baserat på namn, men det finns alltid en risk för felaktig klassificering, särskilt för ovanliga namn eller namn med kulturellt varierande användning.
        
        **Teknisk förklaring:**
        
        Systemet använder ett bibliotek som analyserar förnamn för att försöka identifiera kön. Processen fungerar så här:
        
        1. **Förnamnsextraktion:** Systemet extraherar förnamnet från namnsträngen (t.ex. "BROMMESSON, MAGNUS" → "MAGNUS")
        2. **Könsklassificering:** Förnamnet analyseras mot en databas med namn och deras vanligaste könstillhörighet
        3. **Resultat:** Systemet returnerar "Man", "Kvinna" eller "Okänt"
        
        **Begränsningar:**
        - Systemet fungerar bäst med vanliga svenska och internationella namn
        - Ovanliga namn, utländska namn eller namn med kulturellt varierande användning kan klassificeras fel
        - Unisex-namn placeras i "Okänt" för att undvika felaktig klassificering
        - Systemet kan inte hantera initialer eller förkortningar
        
        **Rekommendation:**
        Använd denna indelning som en indikation, inte som absolut sanning. För exakta siffror krävs manuell verifiering eller direkt kontakt med aktieägarna.
        """)
    
    # Filtrera bort None-värden och räkna kön
    gender_df = physical_df[physical_df['gender'].notna()].copy()
    if gender_df.empty:
        st.info("Ingen könsklassificering kunde göras för fysiska personer.")
        return
    
    gender_counts = gender_df['gender'].value_counts()
    
    # Se till att alla kön finns med även om en är 0
    for gender in ['Man', 'Kvinna', 'Okänt']:
        if gender not in gender_counts.index:
            gender_counts[gender] = 0
    
    # Filtrera bort 0-värden för pie chart
    gender_counts_for_chart = gender_counts[gender_counts > 0]
    
    if gender_counts_for_chart.empty:
        st.info("Ingen könsklassificering kunde göras för fysiska personer.")
        return
    
    # Beräkna ägande per kön för pie chart
    has_holdings = 'holdingsPercentage' in gender_df.columns
    
    if has_holdings:
        gender_summary = gender_df.groupby('gender').agg({
            'holdingsPercentage': 'sum'
        }).reset_index()
        gender_summary = gender_summary[gender_summary['holdingsPercentage'] > 0]
    
    # Visa grafer i två kolumner
    col_gender1, col_gender2 = st.columns(2)
    
    with col_gender1:
        # Pie chart för antal ägare per kön
        colors_gender = get_color_sequence(
            list(gender_counts_for_chart.index), 
            GENDER_COLORS
        )
        
        fig_gender = px.pie(
            values=gender_counts_for_chart.values,
            names=gender_counts_for_chart.index,
            title="Könsfördelning: Antal Ägare",
            color_discrete_sequence=colors_gender if colors_gender else [ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY]
        )
        apply_brand_layout(fig_gender)
        st.plotly_chart(fig_gender, use_container_width=True)
    
    with col_gender2:
        if has_holdings and not gender_summary.empty:
            # Pie chart för holding percentage per kön
            colors_gender_pct = get_color_sequence(
                list(gender_summary['gender'].values),
                GENDER_COLORS
            )
            
            fig_gender_pct = px.pie(
                values=gender_summary['holdingsPercentage'].values,
                names=gender_summary['gender'].values,
                title="Könsfördelning: Andel av Ägande (%)",
                color_discrete_sequence=colors_gender_pct if colors_gender_pct else [ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY]
            )
            apply_brand_layout(fig_gender_pct)
            st.plotly_chart(fig_gender_pct, use_container_width=True)
        else:
            st.info("Ingen holding-data tillgänglig för könsfördelning.")
    
    # KPI-kort för kön
    col_k1, col_k2, col_k3 = st.columns(3)
    men_count = gender_counts.get('Man', 0)
    women_count = gender_counts.get('Kvinna', 0)
    unknown_gender_count = gender_counts.get('Okänt', 0)
    total_gender_all = men_count + women_count + unknown_gender_count
    
    if total_gender_all > 0:
        men_pct = (men_count / total_gender_all * 100)
        women_pct = (women_count / total_gender_all * 100)
        unknown_pct = (unknown_gender_count / total_gender_all * 100)
    else:
        men_pct = women_pct = unknown_pct = 0
    
    with col_k1:
        st.metric("Män", f"{men_count} ({men_pct:.1f}%)")
    with col_k2:
        st.metric("Kvinnor", f"{women_count} ({women_pct:.1f}%)")
    with col_k3:
        st.metric("Okänt Kön", f"{unknown_gender_count} ({unknown_pct:.1f}%)")


def render_age_analysis(physical_df: pd.DataFrame) -> None:
    """
    Renderar åldersfördelningsanalysen för fysiska personer.
    
    Args:
        physical_df: DataFrame med endast fysiska personer, måste innehålla 'age'-kolumn
    """
    st.markdown("---")
    st.markdown("##### Åldersfördelning: Fysiska Personer")
    
    if physical_df.empty or 'age' not in physical_df.columns:
        st.info("Ingen åldersdata tillgänglig för fysiska personer.")
        return
    
    if not physical_df['age'].notna().any():
        st.info("Ingen åldersdata tillgänglig för fysiska personer.")
        return
    
    # Ta bort None-värden
    ages = physical_df['age'].dropna()
    
    if ages.empty:
        st.info("Ingen åldersdata tillgänglig för fysiska personer.")
        return
    
    col_age1, col_age2 = st.columns(2)
    
    with col_age1:
        # Histogram över åldrar
        fig_age_hist = px.histogram(
            physical_df,
            x='age',
            nbins=20,
            title="Åldersfördelning: Antal Ägare per Åldersgrupp",
            labels={'age': 'Ålder (år)', 'count': 'Antal Ägare'},
            color_discrete_sequence=[ILOVE_RED]
        )
        apply_brand_layout(fig_age_hist)
        st.plotly_chart(fig_age_hist, use_container_width=True)
    
    with col_age2:
        # Boxplot över åldrar
        fig_age_box = px.box(
            physical_df,
            y='age',
            title="Åldersöversikt: Median, Kvartiler och Spridning",
            labels={'age': 'Ålder (år)'},
            color_discrete_sequence=[ILOVE_RED]
        )
        apply_brand_layout(fig_age_box)
        st.plotly_chart(fig_age_box, use_container_width=True)
    
    # Åldersstatistik
    st.markdown("**Åldersstatistik för Fysiska Personer:**")
    age_stats = ages.describe()
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Medelålder", f"{age_stats['mean']:.1f} år")
    with col_stat2:
        st.metric("Medianålder", f"{age_stats['50%']:.1f} år")
    with col_stat3:
        st.metric("Yngst", f"{age_stats['min']:.0f} år")
    with col_stat4:
        st.metric("Äldst", f"{age_stats['max']:.0f} år")


def render_owner_type_comparison(known_types_df: pd.DataFrame, physical_df: pd.DataFrame) -> None:
    """
    Renderar jämförelsen mellan fysiska och juridiska personer.
    
    Args:
        known_types_df: DataFrame med alla ägare (exkl. okända typer)
        physical_df: DataFrame med endast fysiska personer
    """
    st.markdown("---")
    st.markdown("##### Jämförelse: Fysiska vs Juridiska Personer")
    
    if known_types_df.empty:
        st.warning("⚠️ Ingen data tillgänglig för jämförelse.")
        return
    
    # KPI-kort för ägartyper
    col1, col2, col3, col4 = st.columns(4)
    
    total_owners = len(known_types_df)
    physical_count = len(known_types_df[known_types_df['owner_type'] == 'Fysisk person'])
    legal_count = len(known_types_df[known_types_df['owner_type'] == 'Juridisk person'])
    physical_pct = (physical_count / total_owners * 100) if total_owners > 0 else 0
    legal_pct = (legal_count / total_owners * 100) if total_owners > 0 else 0
    
    with col1:
        st.metric("Totalt Antal Ägare", total_owners)
    with col2:
        st.metric("Fysiska Personer", f"{physical_count} ({physical_pct:.1f}%)")
    with col3:
        st.metric("Juridiska Personer", f"{legal_count} ({legal_pct:.1f}%)")
    
    # Beräkna snittålder för fysiska personer
    if not physical_df.empty and 'age' in physical_df.columns and physical_df['age'].notna().any():
        avg_age = physical_df['age'].mean()
        with col4:
            st.metric("Snittålder (Fysiska)", f"{avg_age:.1f} år")
    else:
        with col4:
            st.metric("Snittålder (Fysiska)", "N/A")
    
    # Jämförelse: Antal ägare (pie chart)
    st.markdown("##### Jämförelse: Antal Ägare")
    type_counts = known_types_df['owner_type'].value_counts()
    
    # Se till att båda typerna finns med
    for owner_type in ['Fysisk person', 'Juridisk person']:
        if owner_type not in type_counts.index:
            type_counts[owner_type] = 0
    
    # Filtrera bort 0-värden för pie chart
    type_counts_for_chart = type_counts[type_counts > 0]
    
    if not type_counts_for_chart.empty:
        colors = get_color_sequence(
            list(type_counts_for_chart.index),
            OWNER_TYPE_COLORS
        )
        
        fig_type_count = px.pie(
            values=type_counts_for_chart.values,
            names=type_counts_for_chart.index,
            title="Fördelning: Fysiska vs Juridiska Personer",
            color_discrete_sequence=colors if colors else [ILOVE_RED, ILOVE_BLUE]
        )
        apply_brand_layout(fig_type_count)
        st.plotly_chart(fig_type_count, use_container_width=True)
    else:
        st.warning("Ingen data att visa i pie chart.")
    
    # Jämförelse: Ägande (aktier och procent)
    st.markdown("##### Jämförelse: Ägande")
    
    if 'holdingsQuantity' in known_types_df.columns:
        type_summary = known_types_df.groupby('owner_type').agg({
            'holdingsQuantity': 'sum',
            'holdingsPercentage': 'sum',
            'votesPercentage': 'sum'
        }).reset_index()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig_shares = px.bar(
                type_summary,
                x='owner_type',
                y='holdingsQuantity',
                title="Totalt Innehav per Ägartyp (Antal Aktier)",
                labels={'holdingsQuantity': 'Antal Aktier', 'owner_type': 'Ägartyp'},
                color='owner_type',
                color_discrete_map=OWNER_TYPE_COLORS,
                text_auto='.0f'
            )
            apply_brand_layout(fig_shares)
            st.plotly_chart(fig_shares, use_container_width=True)
        
        with col_right:
            fig_pct = px.bar(
                type_summary,
                x='owner_type',
                y='holdingsPercentage',
                title="Andel av Ägande per Ägartyp (%)",
                labels={'holdingsPercentage': 'Andel (%)', 'owner_type': 'Ägartyp'},
                color='owner_type',
                color_discrete_map=OWNER_TYPE_COLORS,
                text_auto='.2f'
            )
            apply_brand_layout(fig_pct)
            st.plotly_chart(fig_pct, use_container_width=True)
    
    # Detaljerad tabell
    st.markdown("##### Detaljerad Översikt")
    
    agg_dict = {'pnrOrgnr': 'count'}
    if 'holdingsQuantity' in known_types_df.columns:
        agg_dict['holdingsQuantity'] = ['sum', 'mean']
    if 'holdingsPercentage' in known_types_df.columns:
        agg_dict['holdingsPercentage'] = 'sum'
    if 'votesPercentage' in known_types_df.columns:
        agg_dict['votesPercentage'] = 'sum'
    if 'age' in known_types_df.columns:
        agg_dict['age'] = ['mean', 'min', 'max']
    
    summary_table = known_types_df.groupby('owner_type').agg(agg_dict).round(2)
    
    # Flatten kolumnnamn om det finns multi-level columns
    if isinstance(summary_table.columns, pd.MultiIndex):
        summary_table.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary_table.columns.values]
    
    # Rename kolumner för bättre läsbarhet
    column_mapping = {
        'pnrOrgnr_count': 'Antal',
        'holdingsQuantity_sum': 'Totalt Aktier',
        'holdingsQuantity_mean': 'Snitt Aktier',
        'holdingsPercentage_sum': 'Totalt Holding %',
        'votesPercentage_sum': 'Totalt Vote %',
        'age_mean': 'Snitt Ålder',
        'age_min': 'Min Ålder',
        'age_max': 'Max Ålder'
    }
    summary_table = summary_table.rename(columns=column_mapping)
    
    st.dataframe(summary_table, use_container_width=True)


# Plan: Visualisering av Ägare per Storleksklass

## Översikt
Skapa en snygg och tydlig visualisering som visar antalet ägare i olika storleksklasser baserat på antal aktier de äger.

## Storleksklasser
Följande intervall föreslås (kan justeras baserat på faktisk data):
- **0-100 aktier** - Mycket små ägare
- **100-500 aktier** - Små ägare
- **500-1,000 aktier** - Medel-små ägare
- **1,000-5,000 aktier** - Medelstora ägare
- **5,000-10,000 aktier** - Stora ägare
- **10,000-50,000 aktier** - Mycket stora ägare
- **50,000+ aktier** - Extra stora ägare

## Visualiseringar

### 1. Bar Chart (Horisontell)
- **Typ**: Horisontell bar chart
- **X-axel**: Antal ägare
- **Y-axel**: Storleksklasser (sorterade från störst till minst)
- **Färger**: Gradient från ILOVE_BLUE till ILOVE_RED baserat på storlek
- **Fördelar**: Lätt att läsa, tydlig hierarki

### 2. Pie Chart
- **Typ**: Pie chart
- **Värden**: Antal ägare per klass
- **Färger**: Brand colors (ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY)
- **Fördelar**: Visar fördelning visuellt

### 3. Tabell
- **Kolumner**:
  - Storleksklass (intervall)
  - Antal ägare
  - Procent av totalt antal ägare
  - Totala aktier i klassen
  - Procent av totala aktier
  - Genomsnittligt antal aktier per ägare
  - Median antal aktier
- **Sortering**: Från störst till minst intervall
- **Formatering**: Tysandsseparatorer, procent med 1 decimal

### 4. KPI-kort (valfritt)
- Totalt antal ägare
- Genomsnittligt antal aktier per ägare
- Median antal aktier
- Största ägaren (antal aktier)

## Layout

### Placering
- Egen sektion i tab4 (Ägartyper-fliken)
- Placera efter åldersanalysen, före jämförelsen fysiska vs juridiska personer
- Eller som egen sektion längst ner

### Struktur
1. **Rubrik**: "Ägare per Storleksklass"
2. **KPI-kort** (valfritt, 4 kolumner)
3. **Graf-sektion** (2 kolumner):
   - Vänster: Bar chart
   - Höger: Pie chart
4. **Tabell**: Detaljerad tabell med alla statistik

## Teknisk Implementation

### Funktion: `categorize_holdings_size(holdings_quantity)`
```python
def categorize_holdings_size(quantity):
    """Kategoriserar ägare baserat på antal aktier."""
    if quantity < 100:
        return "0-100"
    elif quantity < 500:
        return "100-500"
    elif quantity < 1000:
        return "500-1,000"
    elif quantity < 5000:
        return "1,000-5,000"
    elif quantity < 10000:
        return "5,000-10,000"
    elif quantity < 50000:
        return "10,000-50,000"
    else:
        return "50,000+"
```

### Data Processing
1. Applicera kategorisering på `holdingsQuantity`
2. Gruppera per storleksklass
3. Beräkna statistik (antal, summa, medel, median)
4. Sortera klasser i logisk ordning

## Design Considerations

### Färger
- Använd brand colors konsekvent
- Gradient för bar chart kan vara snyggt
- Pie chart: Använd ILOVE_BLUE, ILOVE_RED, ILOVE_DARK_GREY, ILOVE_GREY

### Interaktivitet
- Hover-tooltips med detaljerad information
- Möjlighet att klicka på bar/pie segment för mer info (valfritt)

### Responsivitet
- Använd `use_container_width=True` för alla grafer
- Tabell ska vara scrollbar om den blir för lång

## Alternativ Layout (Om data är mycket skev)
Om det finns många små ägare och få stora:
- Använd logaritmisk skala för bar chart
- Eller separera i två sektioner: "Små ägare" och "Stora ägare"
- Eller använd en "waterfall" chart för att visa koncentrationen

## Ytterligare Förbättringar (Framtida)
- Jämförelse över tid (hur har fördelningen ändrats?)
- Filtrera på fysiska vs juridiska personer
- Export till CSV



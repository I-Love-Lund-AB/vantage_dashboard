import os
import pandas as pd
from datetime import datetime

class DataManager:
    """
    Hanterar lagring och inläsning av aktieägardata till/från en lokal CSV-fil.
    Detta möjliggör historisk analys och minskar behovet av upprepade API-anrop.
    """
    def __init__(self, data_file="data/shareholders_history.csv"):
        self.data_file = data_file
        self.data_dir = os.path.dirname(data_file)
        
        # Skapa datamappen om den inte finns
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_data(self):
        """
        Laddar in all historisk data från CSV-filen.
        
        Returnerar:
            pd.DataFrame: DataFrame med all data, eller en tom DataFrame om filen saknas.
        """
        if os.path.exists(self.data_file):
            try:
                # Läs in CSV med pandas
                df = pd.read_csv(self.data_file)
                # Konvertera datumkolumnen till datetime-objekt för enklare hantering
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                return df
            except Exception as e:
                print(f"Fel vid inläsning av data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def save_data(self, new_data: list):
        """
        Lägger till (append) ny data till historikfilen.
        Om data för samma datum redan finns, ersätts den gamla datan.
        
        Args:
            new_data (list): Lista av dictionaries som innehåller de nya posterna.
        """
        if not new_data:
            return

        new_df = pd.DataFrame(new_data)
        
        # Lägg till en tidsstämpel för när vi hämtade denna data
        new_df['fetched_at'] = datetime.now()
        
        # Konvertera datum till datetime om det behövs
        if 'date' in new_df.columns:
            new_df['date'] = pd.to_datetime(new_df['date'])

        existing_df = self.load_data()
        
        if not existing_df.empty:
            # Hämta datum från ny data (för att veta vad vi ska ta bort)
            new_dates = new_df['date'].unique() if 'date' in new_df.columns else []
            
            # Ta bort gamla data för samma datum(er) för att undvika dubbletter
            if len(new_dates) > 0 and 'date' in existing_df.columns:
                existing_df['date'] = pd.to_datetime(existing_df['date'])
                # Behåll endast rader där datumet INTE finns i nya datan
                existing_df = existing_df[~existing_df['date'].isin(new_dates)]
            
            # Slå ihop existerande (filtrerad) data med ny data
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = new_df

        # Spara tillbaka till CSV
        updated_df.to_csv(self.data_file, index=False)
        print(f"Sparade {len(new_df)} nya poster till {self.data_file}")

    def get_last_update_time(self):
        """
        Returnerar tidpunkten då datafilen senast ändrades.
        """
        if os.path.exists(self.data_file):
            return datetime.fromtimestamp(os.path.getmtime(self.data_file))
        return None

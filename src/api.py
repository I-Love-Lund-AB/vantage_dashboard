import os
import requests
from auth import AuthHandler, _get_secret

class VantageClient:
    """
    Klient för att kommunicera med Euroclear Vantage API.
    Hanterar autentisering och specifika API-anrop.
    """
    def __init__(self):
        self.auth = AuthHandler()
        self.base_url = _get_secret("VANTAGE_API_URL")
        if not self.base_url:
            raise ValueError(
                "VANTAGE_API_URL saknas. Sätt den i .env (lokalt) "
                "eller i Streamlit Cloud Secrets."
            )

    def _get_headers(self):
        """
        Skapar HTTP-headers som krävs för anropet, inklusive Bearer Token.
        """
        # Hämta en giltig access token (ny eller cachad)
        token = self.auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Vantage-Python-Client/1.0",  # User-Agent kan krävas av vissa API:er
            "Content-Type": "application/json"  # Explicit Content-Type
        }

    def get_issuer_metadata(self):
        """
        Hämtar metadata om utgivare (Issuers) som användaren har tillgång till.
        
        Endpoint: /issuermetadata
        
        Returnerar:
            JSON-data (lista av issuers) vid framgång.
            Kastar RequestException vid fel (t.ex. 401, 403).
        """
        endpoint = f"{self.base_url}/issuermetadata"
        # Vi låter exceptions bubbla upp så att UI:t kan hantera specifika felkoder (t.ex. 403 Forbidden)
        response = requests.get(
            endpoint, 
            headers=self._get_headers(),
            verify=True,  # Explicit SSL-verifiering
            timeout=30  # Timeout för att undvika hängning
        )
        response.raise_for_status()
        return response.json()

    def get_isin_metadata(self, org_number: str, api_id: str = None):
        """
        Hämtar ISIN-metadata för ett specifikt organisationsnummer.
        
        Args:
            org_number (str): Organisationsnummer för utgivaren.
            api_id (str, optional): Specifikt API-ID att filtrera på (t.ex. 'completeregister').
        """
        endpoint = f"{self.base_url}/isinmetadata"
        params = {"orgNumber": org_number}
        if api_id:
            params["apiId"] = api_id
            
        response = requests.get(
            endpoint, 
            headers=self._get_headers(), 
            params=params,
            verify=True,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_complete_register(self, isin: str, holding_date: str):
        """
        Hämtar den kompletta aktieboken (Shareholder Register) för en specifik ISIN och datum.
        
        Args:
            isin (str): Värdepapprets ISIN-kod.
            holding_date (str): Referensdatum i formatet YYYY-MM-DD.
        
        Returnerar:
            dict: JSON-data om lyckat (Status 200).
            None: Om ingen data finns för datumet (Status 204).
        
        Raises:
            requests.RequestException: Vid fel i API-anropet (400, 401, 403, 500, etc.)
        """
        endpoint = f"{self.base_url}/completeregister" 
        params = {
            "isin": isin,
            "holdingDate": holding_date
        }

        response = requests.get(
            endpoint, 
            headers=self._get_headers(), 
            params=params,
            verify=True,  # Explicit SSL-verifiering
            timeout=30  # Timeout för att undvika hängning
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            # 204 No Content är ett "lyckat" anrop men betyder att data saknas för vald dag
            # Detta kan betyda:
            # 1. Data finns inte för detta specifika datum
            # 2. Data är inte tillgänglig än (för framtida datum)
            # 3. Data finns inte i systemet för detta datum
            return None
        else:
            # För alla andra statuskoder (400, 403, 500), kasta ett fel
            # Detta ger oss bättre felmeddelanden
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Lägg till mer information i felmeddelandet
                error_msg = f"HTTP {response.status_code}: {str(e)}"
                if response.text:
                    error_msg += f" - Response: {response.text[:200]}"
                raise requests.exceptions.HTTPError(error_msg, response=response)
            return None

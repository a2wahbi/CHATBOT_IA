import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def connect_to_google_sheets():
    """Connecte à Google Sheets et retourne la feuille spécifiée."""
    try:
        # Définir la portée des autorisations
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Charger les credentials depuis un fichier sécurisé
        creds = ServiceAccountCredentials.from_json_keyfile_name("chatbotiatekin-e779d1bd984d.json", scope)
        client = gspread.authorize(creds)
        
        # Ouvrir la feuille Google Sheets
        return client.open("Conversations IoT").sheet1
    except Exception as e:
        raise RuntimeError(f"Erreur de connexion à Google Sheets : {e}")

def save_to_google_sheets(user_message, assistant_response, section_name):
    """Enregistre une conversation dans Google Sheets avec la date/heure."""
    try:
        # Obtenir la date et l'heure actuelles
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Connexion à Google Sheets
        sheet = connect_to_google_sheets()
        
        # Ajouter une nouvelle ligne avec les données
        sheet.append_row([timestamp, user_message, assistant_response, section_name])
        print("Données enregistrées avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement des données : {e}")
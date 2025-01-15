import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import gspread
def connect_to_google_sheets():
    """Connecte à Google Sheets en fonction de l'environnement."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Vérifier l'environnement
        env = os.getenv("ENV", "local")  # Par défaut, on considère l'environnement local
        
        if env == "production":
            # En ligne (Streamlit Cloud), utiliser les secrets Streamlit
            credentials_json = st.secrets["GOOGLE_CREDENTIALS"]
            creds_dict = json.loads(credentials_json)
        else:
            # En local, utiliser le fichier credentials.json
            creds_path = "chatbotiatekin-e779d1bd984d.json"
            with open(creds_path, "r") as f:
                creds_dict = json.load(f)

        # Autoriser les credentials
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
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
#database.py
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import gspread

def connect_to_google_sheets():
    """Connecte à Google Sheets et retourne le classeur complet."""
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
        return client.open("Conversations IoT")  # Retourne le classeur entier
    except Exception as e:
        raise RuntimeError(f"Erreur de connexion à Google Sheets : {e}")
    

def save_to_google_sheets(user_message, assistant_response, section_name , sheet_name):
    """Enregistre une conversation dans Google Sheets avec la date/heure dans une feuille spécifique"""
    try:
        # Obtenir la date et l'heure actuelles
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spreadsheet = connect_to_google_sheets()
        
        # Sélectionner la feuille par son nom
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"La feuille {sheet_name} n'existe pas.")
            return

        # Ajouter une nouvelle ligne
        sheet.append_row([timestamp, user_message, assistant_response, section_name])

        #st.write("Données enregistrées avec succès.")
    except Exception as e:
        st.write(f"Erreur lors de l'enregistrement des données : {e}")

def create_new_sheet(sheet_name):
    """Crée une nouvelle feuille dans le classeur Google Sheets."""
    try:
        spreadsheet = connect_to_google_sheets()
        if sheet_name not in [sheet.title for sheet in spreadsheet.worksheets()]:
            new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="10")
            # Ajouter les en-têtes
            new_sheet.append_row(["Timestamp", "User Message", "Assistant Response", "Section Name"])
        return spreadsheet.worksheet(sheet_name)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la création de la nouvelle feuille : {e}")
    
def test_google_sheets():
    try:
        sheet = connect_to_google_sheets()
        st.write(f"Connexion réussie à la feuille : {sheet.title}")
        # Lire quelques lignes pour vérifier
        data = sheet.get_all_records()
        st.write(f"Données actuelles dans la feuille : {data}")
    except Exception as e:
        st.write(f"Erreur de connexion à Google Sheets : {e}")
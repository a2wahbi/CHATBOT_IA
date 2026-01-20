#database.py
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def save_to_google_sheets(user_message, assistant_response, section_name, cahier_content=None):
    """
    Enregistre une conversation ou un cahier des charges dans Google Sheets.
    
    Args:
        user_message (str): Message de l'utilisateur.
        assistant_response (str): Réponse générée par l'assistant.
        section_name (str): Section actuelle de la discussion.
        cahier_content (str): Contenu du cahier des charges (facultatif).
    """
    try:
        # Obtenir la feuille actuelle depuis la session
        current_sheet_name = st.session_state.get("current_sheet")
        if not current_sheet_name:
            #st.error("Aucune feuille active n'est définie.")
            return
        
        # Obtenir le classeur et la feuille actuelle
        spreadsheet = connect_to_google_sheets()
        sheet = spreadsheet.worksheet(current_sheet_name)

        if cahier_content:
            # Ajouter le contenu du cahier des charges avec une ligne vide pour séparer
            sheet.append_row([])
            sheet.append_row(["Cahier des Charges :"])
            sheet.append_row([cahier_content])
        else:
            # Ajouter une nouvelle ligne pour la discussion
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_to_write = [None, None, None, timestamp, user_message, assistant_response, section_name]
            sheet.append_row(data_to_write)

    except Exception as e:
        st.error(f"Erreur lors de l'enregistrement des données : {e}")

def connect_to_google_sheets():
    raw = st.secrets["GOOGLE_CREDENTIALS"]
    creds_info = json.loads(raw)  # raw est une string JSON
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def create_new_sheet_from_user(email, first_name, last_name ):
    """
    Crée une nouvelle feuille Google Sheets basée sur le nom complet et l'email de l'utilisateur.
    Enregistre également le prénom, nom et email dans la première ligne de la feuille.

    Args:
        email (str): L'adresse e-mail de l'utilisateur.
        first_name (str): Le prénom de l'utilisateur.
        last_name (str): Le nom de l'utilisateur.

    Returns:
        worksheet: La feuille nouvellement créée.
    """
    try:
        spreadsheet = connect_to_google_sheets()

        # Générer le nom de la feuille à partir du prénom, du nom et de l'email
        full_name = f"{first_name} {last_name}"
        sheet_name = f"{first_name}_{last_name}_{email.split('@')[0]}"
        
        # Nettoyer les caractères invalides dans le nom de la feuille
        import re
        sheet_name = re.sub(r"[^\w\s-]", "_", sheet_name)

        # Vérifier si une feuille avec ce nom existe déjà
        if sheet_name in [sheet.title for sheet in spreadsheet.worksheets()]:
            st.warning(f"La feuille {sheet_name} existe déjà.")
            return spreadsheet.worksheet(sheet_name)
        

        # Créer une nouvelle feuille
        new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="10")
        
       # Ajouter les en-têtes et les informations utilisateur dans la première ligne
        new_sheet.append_row(["Email", "Prénom", "Nom", "Timestamp", "User Message", "Assistant Response", "Section Name"])
        new_sheet.append_row([email, first_name, last_name])  # Deuxième ligne avec les infos utilisateur
        
        return new_sheet

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

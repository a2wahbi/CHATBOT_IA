# database.py
import json
import re
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# Scopes nécessaires pour lire/écrire Sheets + accès Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_gspread_client() -> gspread.Client:
    """
    Retourne un client gspread authentifié via le JSON de service account
    stocké dans st.secrets["GOOGLE_CREDENTIALS"] (format string JSON).
    """
    if "GOOGLE_CREDENTIALS" not in st.secrets:
        raise RuntimeError(
            "GOOGLE_CREDENTIALS manquant dans Streamlit Secrets. "
            "Ajoute le JSON du service account dans Manage app → Secrets."
        )

    raw = st.secrets["GOOGLE_CREDENTIALS"]

    # raw doit être une string JSON
    if not isinstance(raw, str):
        # parfois Streamlit peut renvoyer un mapping selon comment c'est saisi
        raw = json.dumps(dict(raw))

    try:
        creds_info = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"GOOGLE_CREDENTIALS n'est pas un JSON valide: {e}. "
            "Vérifie le contenu collé dans Secrets (guillemets, \\n, caractères invisibles)."
        )

    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_spreadsheet() -> gspread.Spreadsheet:
    """
    Ouvre le Google Spreadsheet cible via son ID stocké dans st.secrets["SHEET_ID"].
    """
    if "SHEET_ID" not in st.secrets:
        raise RuntimeError(
            "SHEET_ID manquant dans Streamlit Secrets. "
            "Ajoute l'ID (entre /d/ et /edit dans l'URL du Google Sheet)."
        )

    client = _get_gspread_client()
    sheet_id = st.secrets["SHEET_ID"]

    try:
        return client.open_by_key(sheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        raise RuntimeError(
            "SpreadsheetNotFound: le SHEET_ID est incorrect OU le Google Sheet "
            "n'est pas partagé avec le service account (client_email)."
        )


def _sanitize_worksheet_title(title: str) -> str:
    """
    Nettoie un titre d'onglet (worksheet) pour éviter les caractères invalides.
    """
    title = title.strip()
    title = re.sub(r"[^\w\s-]", "_", title)  # remplace caractères spéciaux
    title = re.sub(r"\s+", " ", title)       # espaces multiples
    # Google Sheets limite le titre d'onglet à 100 caractères
    return title[:100]


def create_new_sheet_from_user(email: str, first_name: str, last_name: str):
    """
    Crée (ou récupère) un onglet (worksheet) dédié à l'utilisateur dans le Spreadsheet.
    Stocke son nom dans st.session_state["current_sheet"].
    """
    spreadsheet = _get_spreadsheet()

    # Nom de l'onglet basé sur user
    base = f"{first_name}_{last_name}_{email.split('@')[0]}"
    sheet_name = _sanitize_worksheet_title(base)

    # Liste des titres existants
    existing_titles = [ws.title for ws in spreadsheet.worksheets()]
    if sheet_name in existing_titles:
        ws = spreadsheet.worksheet(sheet_name)
        st.session_state["current_sheet"] = sheet_name
        return ws

    # Créer un nouvel onglet
    ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)

    # En-têtes + ligne d'identité user
    ws.append_row(
        ["Email", "Prénom", "Nom", "Timestamp", "User Message", "Assistant Response", "Section Name"],
        value_input_option="RAW",
    )
    ws.append_row([email, first_name, last_name], value_input_option="RAW")

    st.session_state["current_sheet"] = sheet_name
    return ws


def save_to_google_sheets(
    user_message: str,
    assistant_response: str,
    section_name: str,
    cahier_content: str | None = None,
):
    """
    Enregistre la conversation (ou le cahier des charges) dans l'onglet actif.
    Nécessite que st.session_state["current_sheet"] soit défini (via create_new_sheet_from_user).
    """
    current_sheet_name = st.session_state.get("current_sheet")
    if not current_sheet_name:
        # pas de sheet actif -> on n'écrit rien
        return

    spreadsheet = _get_spreadsheet()

    try:
        ws = spreadsheet.worksheet(current_sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        raise RuntimeError(
            f"Worksheet '{current_sheet_name}' introuvable. "
            "Relance create_new_sheet_from_user() ou vérifie le nom."
        )

    if cahier_content:
        # Séparer visuellement
        ws.append_row([], value_input_option="RAW")
        ws.append_row(["Cahier des Charges :"], value_input_option="RAW")
        ws.append_row([cahier_content], value_input_option="RAW")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [None, None, None, timestamp, user_message, assistant_response, section_name]
    ws.append_row(row, value_input_option="RAW")


def test_google_sheets():
    """
    Petit test: ouvre le Spreadsheet et liste les onglets.
    À appeler temporairement pour debug.
    """
    spreadsheet = _get_spreadsheet()
    titles = [ws.title for ws in spreadsheet.worksheets()]
    st.success(f"Connexion Google Sheets OK ✅ Spreadsheet: {spreadsheet.title}")
    st.write("Onglets existants :", titles)

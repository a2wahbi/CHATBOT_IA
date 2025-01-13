import io

"""Gestion et Exportation de l'Historique des Conversations"""

def generate_chat_history_text(history):
    """Génère un texte formaté de l'historique des conversations."""
    text_output = "Historique de la conversation :\n\n"
    for message in history:
        text_output += f"Utilisateur : {message['human']}\n"
        text_output += f"Assistant : {message['AI']}\n\n"
    return text_output

def download_chat_history(history):
    """Créer un fichier téléchargeable pour l'historique des conversations."""
    chat_text = generate_chat_history_text(history)
    return io.BytesIO(chat_text.encode('utf-8'))



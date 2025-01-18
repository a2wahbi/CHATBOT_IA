#buttons.py
import io
import streamlit as st
from cahierDeCharge import next_section
"""
Gestion et Exportation de l'Historique des Conversations

Ce module fournit des fonctions pour :
1. Générer une version textuelle de l'historique des conversations.
2. Créer un fichier téléchargeable contenant cet historique.
3. Afficher des boutons interactifs dans une interface Streamlit, y compris un bouton d'exportation dans un popover.

Utilisation :
- Importer `display_interactive_buttons` pour ajouter les boutons à une interface Streamlit.
- Les fonctions `generate_chat_history_text` et `download_chat_history` sont appelées en interne.
"""


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



def display_interactive_buttons(input_question_container, clear_text, clear_text_with_default):
    """
    Affiche  les boutons 'Envoyer', 'Je ne sais pas' et 'Export' dans un conteneur.

    Args:
        input_question_container (streamlit.container): Conteneur dans lequel placer les boutons.
        clear_text (callable): Fonction appelée lors du clic sur le bouton 'Envoyer'.
        clear_text_with_default (callable): Fonction appelée lors du clic sur le bouton 'Je ne sais pas'.
    """

    col1, col2, col3 , col4 = input_question_container.columns([1,1.4,1.5,1])

    # Bouton Envoyer
    col4.button("Envoyer", type = "primary", on_click=clear_text , use_container_width = True , icon=":material/send:")

    # Bouton Je ne sais pas
    col2.button("🤔 Je ne sais pas", on_click=lambda: clear_text_with_default("Je ne sais pas"),  use_container_width = True)

    #boutton pour passer a la nouvelle section 
    col3.button("➡️ Prochaine section", on_click = next_section , use_container_width = True )
    # Bouton dans un popover pour télécharger l'historique
    popover = col1.popover("📁 Export" , use_container_width = True)
    if st.session_state.chat_history:  # Vérification si un historique existe
        chat_file = download_chat_history(st.session_state.chat_history)
        popover.download_button(
            label="📥 Télécharger en tant que fichier texte",
            data=chat_file,
            file_name="historique_conversation.txt",
            mime="text/plain"
        )
    else:
        popover.write("Aucune conversation à télécharger.")


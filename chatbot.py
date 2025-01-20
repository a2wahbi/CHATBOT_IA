#chatbot.py
import streamlit as st
import os
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
import json
import whisper
import tempfile
from buttons import display_interactive_buttons
from cahierDeCharge import section_prompts, system_prompt, generate_full_prompt , next_section
from cahierDeCharge import get_updated_prompt_template , display_summary_history , init , generate_summary_document
from layout import get_historique_container , get_title_container , get_input_question_container
from database import save_to_google_sheets , connect_to_google_sheets , create_new_sheet  
from init import app_init

result = {
    "text": "",  # Chaîne de caractères pour le texte résultant
    "segments": [],  # Liste pour les détails au niveau des segments
    "language": None  # Langue détectée, initialement définie comme None
}


##############################################################################
#                               Styles                                       #
##############################################################################
# Charger le fichier CSS si le fichier existe
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

##############################################################################
#                               speech to text                                #
##############################################################################
def audio_input_widget (): 
    # Enregistrement via st.audio_input
    audio_data = input_question_container.audio_input("speech text widget" , label_visibility= "collapsed" )
    if audio_data is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            audio_path = tmpfile.name
            try:
                # Sauvegarder l'audio temporairement
                tmpfile.write(audio_data.read())

                global result
                result = model.transcribe(audio_path)

            except Exception as e:
                st.error(f"Une erreur est survenue pendant l'enregistrement ou la transcription : {e}")
            finally:
                # Supprimer le fichier temporaire
                if os.path.exists(audio_path):
                    os.remove(audio_path)

def start_new_discussion():
    """Démarre une nouvelle discussion en créant une nouvelle feuille."""
    spreadsheet = connect_to_google_sheets()  # Récupère le classeur
    existing_sheets = [sheet.title for sheet in spreadsheet.worksheets()]  # Liste des feuilles existantes
    discussion_number = len(existing_sheets) + 1
    new_sheet_name = f"Discussion {discussion_number}"

    # Créer une nouvelle feuille
    create_new_sheet(new_sheet_name)

    # Réinitialiser les données dans l'application
    st.session_state.chat_history = []
    st.session_state.current_sheet = new_sheet_name
    #st.success(f"Nouvelle discussion créée : {new_sheet_name}")

########################################################################################
#                               Fonction Utiles                                         #
########################################################################################
def clear_text():
        """Génère une réponse uniquement si l'entrée utilisateur n'est pas vide."""
        user_input = st.session_state.get("text", "").strip()
        # Ignorer si l'entrée utilisateur est vide
        if not user_input:
            historique_container.warning("Veuillez entrer un texte avant d'envoyer.", icon="⚠️")
            return
        try:
                # Transform chat history to LangChain-compatible format
                formatted_history = []
                for message in st.session_state.chat_history:
                    formatted_history.append({'role': 'user', 'content': message['human']})
                    formatted_history.append({'role': 'assistant', 'content': message['AI']})

                # Format the prompt dynamically
                formatted_prompt = prompt_template.format_prompt(
                    chat_history=formatted_history,  # Pass the transformed chat history
                    human_input=st.session_state["text"]  # Include the user's input
                ).to_messages()

                # Generate a response using the formatted prompt
                response = groq_chat(formatted_prompt)

                # Add the user input and AI response to the session's chat history
                st.session_state.chat_history.append({'human': st.session_state["text"] , 'AI': response.content})
                
                        # Enregistrement
                save_to_google_sheets(
                    st.session_state["text"],
                    response.content,
                    st.session_state.current_section,
                    st.session_state.current_sheet
                )
                
                # Save to the file if memory length is reached
                if len(st.session_state.chat_history) % memory_length == 0:
                    append_history_to_file(st.session_state.chat_history[-memory_length:])
        except Exception as e:
                st.error(f"Erreur lors de la génération de la réponse : {str(e)}")
                            #Clean the user input  
        st.session_state["text"] = ""  

def clear_text_with_default(default_input="Je ne sais pas"):
    """Fonction similaire à clear_text, mais prend un texte par défaut comme entrée."""
    try:
        # Transform chat history to LangChain-compatible format
        formatted_history = []
        for message in st.session_state.chat_history:
            formatted_history.append({'role': 'user', 'content': message['human']})
            formatted_history.append({'role': 'assistant', 'content': message['AI']})

        # Format the prompt dynamically with default input
        formatted_prompt = prompt_template.format_prompt(
            chat_history=formatted_history,  # Pass the transformed chat history
            human_input=default_input  # Use default input like "Je ne sais pas"
        ).to_messages()

        # Generate a response using the formatted prompt
        response = groq_chat(formatted_prompt)

        # Add the user input and AI response to the session's chat history
        st.session_state.chat_history.append({'human': default_input, 'AI': response.content})

        # Save to the file if memory length is reached
        if len(st.session_state.chat_history) % memory_length == 0:
            append_history_to_file(st.session_state.chat_history[-memory_length:])
    except Exception as e:
        st.error(f"Erreur lors de la génération de la réponse : {str(e)}")

#Enregistrer les données dans un fichier JSON 
HISTORY_FILE = "chat_history.json"
def save_history_to_file(history, filename = HISTORY_FILE):
    """Enregistre l'historique de la conversation dans un fichier JSON. """
    with open(filename, "w") as f:
        json.dump(history, f , indent = 4)

def append_history_to_file(new_messages, filename = HISTORY_FILE):
    """Ajoute de nouvelles conversations à la fin de l'historique JSON. """
    history = load_history_from_file(filename)
    history.extend(new_messages)
    save_history_to_file(history, filename)

def load_history_from_file(filename = HISTORY_FILE):
    """Charge l'historique de la conversation depuis un fichier JSON."""
    if os.path.exists(filename):
        with open(filename, "r") as f :
            return json.load(f)
    return []
    
def setup_sidebar():
    """Configure la barre latérale avec le logo, la progression des sections, et le bouton de réinitialisation."""
    st.sidebar.image('TEKIN logo 2019 couleur.png', use_container_width=True)
    display_section_progress()
    # Bouton pour réinitialiser la conversation
    if st.sidebar.button("Réinitialiser la conversation"):
        save_history_to_file([])  # Réinitialiser le fichier
        st.session_state.chat_history = []
        st.sidebar.success("Conversation réinitialisée.")

def display_section_progress():
    """Affiche la progression des sections dans la barre latérale."""
    st.sidebar.write("## Progression")
    sections = list(section_prompts.keys())
    current_index = sections.index(st.session_state.current_section)
    total_sections = len(sections)
    progress_value = (current_index + 1) / total_sections

    st.sidebar.progress(progress_value, text=f"Section {current_index + 1} sur {total_sections}")
    st.sidebar.write("### Progression des Sections")
    for idx, section in enumerate(sections):
        icon = "✅" if idx < current_index else "🚀" if idx == current_index else "⏳"
        color = "green" if idx < current_index else "red" if idx == current_index else "gray"
        st.sidebar.markdown(f"{icon} <span style='color: {color}; font-weight: bold;'>{section}</span>", unsafe_allow_html=True)


##############################################################################
#                               Display functions                            #
##############################################################################  
def display_historique(historique_container):
        # Affichage de l'historique de la conversation
    historique_container.subheader("📝 Conversation")

    for message in st.session_state.chat_history:
        if message['human'] is None and message['AI'].startswith("Bienvenue 👋!"):
            # Affichage du message de bienvenue avec un style personnalisé
            historique_container.markdown(
                f"""
                <div style='
                    background-color: #F9F9F9; 
                    border: 1px solid #E5E5E5; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin-bottom: 20px; 
                    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
                    font-family: Arial, sans-serif; 
                    font-size: 16px; 
                    line-height: 1.6; 
                    color: #333;'>
                    <strong style='font-size: 18px; color: #2A7AE4;'>Bienvenue 👋 !</strong><br>
                    {message['AI']}
                </div>
                """, 
                unsafe_allow_html=True
            )
        elif message['human'] is None and message['AI'].startswith("###"):
            # Affichage des titres de section avec un style personnalisé
            historique_container.markdown(
                f"""
                <h3 style='
                    color: #FF5733; 
                    font-size: 24px; 
                    font-weight: bold; 
                    text-align: center; 
                    margin-top: 20px; 
                    margin-bottom: 10px; 
                    border-bottom: 2px solid #FF5733;
                    padding-bottom: 5px;
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
                '>{message['AI'][4:].strip()}</h3>
                """, 
                unsafe_allow_html=True
            )
        elif message['human'] is None and "Merci pour votre confiance" in message['AI']:
            # Affichage du message de fin
            historique_container.markdown(
                f"""
                <div style='
                    background-color: #EAF7FF; 
                    border: 1px solid #B3E5FC; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin-bottom: 20px;
                    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
                    font-family: Arial, sans-serif;
                    color: #01579B;'>
                    {message['AI']}
                </div>
                """, 
                unsafe_allow_html=True
            )
        elif message['human'] is None and '📥 [Cliquez ici pour télécharger' in message['AI']:
            # Bouton de téléchargement
            download_content = generate_summary_document()
            historique_container.download_button(
                label="📥 Télécharger le cahier de charge en format .txt",
                data=download_content,
                file_name="resume_projet_iot.txt",
                mime="text/plain"
            )
        else:
            with st.spinner("En écriture..."):
                if message["human"] and message["human"].strip():  # Vérifie que le message utilisateur n'est pas vide
                    historique_container.chat_message("user").write(message["human"])
                if message["AI"] and message["AI"].strip():  # Vérifie que le message de l'IA n'est pas vide
                    historique_container.chat_message("assistant").write(message["AI"])

def display_intro_message(Historique_container):
    """
    Affiche un message de bienvenue stylisé avec un bouton déclenchant un callback Python.
    """
    # Texte stylisé avec Markdown et CSS pour centrer les titres
    Historique_container.markdown(
        """
<style>
/* Titre principal */
.title {
    text-align: center;
    color: white;
    font-size: 24px; /* Taille réduite */
    font-weight: bold;
    background: linear-gradient(90deg, #ff8c00, #ff5722);
    padding: 10px; /* Espacement réduit */
    border-radius: 10px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.15);
}

/* Sous-titre */
.subtitle {
    text-align: center;
    font-size: 16px; /* Taille réduite */
    color: white;
    background: linear-gradient(90deg, #4682b4, #1e90ff);
    padding: 8px; /* Espacement réduit */
    border-radius: 10px;
    margin-top: 10px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.15);
}

/* Contenu */
.content {
    font-size: 16px; /* Taille réduite */
    color: white;
    line-height: 1.6; /* Espacement légèrement réduit */
    text-align: justify;
    padding: 10px; /* Espacement interne réduit */
    border-radius: 10px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
    margin-top: 15px;
}
</style>
<h3 class="title">👋 Bienvenue chez TEKIN !</h3>
<h5 class="subtitle">🌟 Créez votre cahier des charges IoT facilement !</h5>
<div class="content">
    Nous sommes ravis de vous accompagner dans votre projet. Ce processus est <strong>simple et structuré</strong> en plusieurs sections, 
    chacune dédiée à un aspect spécifique de votre projet IoT.
    <br><br>
    <strong>👉 Comment ça marche ?</strong><br>
    - Je vous poserai des questions claires pour collecter les informations essentielles.<br>
    - Une fois une section terminée, vous pouvez passer à la suivante en cliquant sur le bouton <strong>"Prochaine section"</strong>, situé à côté du bouton <strong>"Envoyer"</strong>.
    <br><br>
    <strong>🎯 Prêt à commencer ? Cliquez sur le bouton ci-dessous !</strong>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Bouton centré avec une icône
    col1, col2, col3 = Historique_container.columns([1, 2, 1])  # Colonnes pour centrer le bouton
    with col2:
        if Historique_container.button("🆕 Nouvelle discussion"):
            start_new_discussion()


##############################################################################
#                               APP                                          #
##############################################################################  

# Initialisation 
title_container , historique_container , input_question_container , model_choice, memory_length, max_tokens , memory  , groq_chat , conversation , model  = app_init()

# Initialisation de l'historique de conversation dans la session
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = load_history_from_file()

if 'current_section' not in st.session_state:
    st.session_state.current_section = "Accueil"

if 'full_prompt' not in st.session_state:
    st.session_state.full_prompt = generate_full_prompt(
        st.session_state.current_section, 
        ""
    )

if "current_sheet" not in st.session_state:
    st.session_state.current_sheet = "Discussion 1"  # Feuille par défaut
    create_new_sheet(st.session_state.current_sheet)

if 'history_summary' not in st.session_state:
    st.session_state.history_summary = [] 

init()
# Obtenir le prompt template mis à jour
prompt_template = get_updated_prompt_template()

# Stocker groq_chat dans st.session_state
st.session_state.groq_chat = groq_chat

# Appel de la fonction d'affichage du message d'introduction
if len(st.session_state.chat_history) == 0:
    display_intro_message(historique_container)
else:
    # Si une discussion est déjà en cours, afficher l'historique
    display_historique(historique_container)



# Widget audio
#audio_input_widget()

# Champ de saisie pour la question utilisateu
if result["text"] :
    user_question = input_question_container.text_area(
    "Posez votre question ici 👇",
    value=result["text"],
    placeholder="Comment puis-je vous aider ?",
    key = "text",
    )
else: 
    user_question = input_question_container.text_area(
    "Posez votre question ici 👇",
    placeholder="Comment puis-je vous aider ?",
    key = "text"
    )

# Appeler la fonction pour Afficher les boutons
display_interactive_buttons(input_question_container, clear_text, clear_text_with_default)
setup_sidebar()
#display_summary_history()

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
from database import save_to_google_sheets , connect_to_google_sheets , create_new_sheet_from_user  
from init import app_init , init_input_user_container
import html  # Importer le module pour échapper les caractères spéciaux

st.set_page_config(layout="centered")


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
#                             Callbacks                                      #
##############################################################################
def start_discussion_callback():
    """Callback pour passer à l'étape 2."""
    st.session_state.current_step = 2


def submit_user_info_callback():
    """Callback pour soumettre les informations utilisateur."""
    first_name = st.session_state.get("first_name", "").strip()
    last_name = st.session_state.get("last_name", "").strip()
    email = st.session_state.get("email", "").strip()

    if not first_name or not last_name or not email:
        st.warning("Veuillez remplir tous les champs.")
    elif "@" not in email or "." not in email:
        st.error("Adresse e-mail invalide.")
    else:
        st.session_state.user_details = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }
        st.session_state.current_step = 3


def start_new_discussion_callback():
    """Callback pour démarrer une nouvelle discussion."""
    user_details = st.session_state.get("user_details", {})
    if user_details:
        start_new_discussion(
            user_details.get("email"),
            user_details.get("first_name"),
            user_details.get("last_name"),
        )
        st.session_state.current_step = 4


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

def start_new_discussion(email, first_name, last_name):
    """
    Démarre une nouvelle discussion en créant une nouvelle feuille et en initialisant l'historique.
    
    Args:
        email (str): Adresse e-mail de l'utilisateur.
        first_name (str): Prénom de l'utilisateur.
        last_name (str): Nom de l'utilisateur.
    """
    try:
        # Créer une nouvelle feuille avec les informations utilisateur
        user_sheet = create_new_sheet_from_user(email, first_name, last_name)
        
        # Mettre à jour la session avec la feuille actuelle
        st.session_state.current_sheet = user_sheet.title
        
        # Réinitialiser l'historique de la discussion
        st.session_state.chat_history = []
    except Exception as e:
        st.error(f"Erreur lors du démarrage de la discussion : {e}")

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
                
                save_to_google_sheets(user_input, response.content, st.session_state.current_section)

                
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
        color = "steelblue" if idx < current_index else "darkorange" if idx == current_index else "gray"
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
            historique_container.markdown(
                """
                <div style="
                    background-color: #EAF7FF; 
                    border: 1px solid #B3E5FC; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin-bottom: 15px; 
                    font-family: 'Arial', sans-serif; 
                    font-size: 16px; 
                    color: #01579B; 
                    box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); 
                    line-height: 1.4;
                ">
                    <p style="margin: 0; font-weight: bold; font-size: 18px; text-align: center;">
                        Merci pour votre confiance et d'avoir choisi <span style="color: #FF5722;">TEKIN</span> ! 😊
                    </p>
                    <p style="margin: 10px 0; text-align: center; font-size: 14px;">
                        Vous êtes déjà à la fin du processus. Si vous avez d'autres questions, n'hésitez pas à les poser !
                    </p>
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

##############################################################################
#                          Display Intro Message                            #
##############################################################################
def display_intro_message(historique_container):
    """
    Gère les étapes pour démarrer une nouvelle discussion.
    """
    # Initialisation par défaut
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1  

    if st.session_state.current_step == 1:
        # Étape 1 : Message d'accueil stylisé
        historique_container.markdown(
            """
            <style>
            .title {
                text-align: center;
                color: white;
                font-size: 20px;
                font-weight: bold;
                background: linear-gradient(90deg, #ff8c00, #ff5722);
                padding: 8px;
                border-radius: 8px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.15);
            }
            .content {
                font-size: 17px;
                color: white;
                line-height: 1.6;
                text-align: justify;
                padding: 5px;
                border-radius: 5px;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
                margin-top: 15px;
            }
            </style>
            <h4 class="title">👋 Bienvenue chez TEKIN !</h4>
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

        # Bouton avec callback
        historique_container.button(
            "🆕 Nouvelle discussion", 
            on_click=start_discussion_callback
        )

    elif st.session_state.current_step == 2:
        # Étape 2 : Formulaire pour les informations utilisateur
        historique_container.markdown(
            """
            <h5 style="text-align: center; color: #FF5722;">📝 Informations nécessaires</h5>
            <p style="text-align: center; color: white;">
                Avant de commencer, merci de renseigner vos informations.
            </p>
            """,
            unsafe_allow_html=True,
        )
        historique_container.text_input("Prénom", placeholder="Votre prénom", key="first_name")
        historique_container.text_input("Nom", placeholder="Votre nom", key="last_name")
        historique_container.text_input("Adresse e-mail", placeholder="exemple@domaine.com", key="email")
        historique_container.button(
            "Commencer",
            on_click=submit_user_info_callback,
        )

    elif st.session_state.current_step == 3:
        # Étape 3 : Confirmation
        user_details = st.session_state.get("user_details", {})

        if user_details:
            historique_container.markdown(
                f"""
                <h4 style="text-align: center; color: #FF5722;">Merci {user_details['first_name']} {user_details['last_name']} !</h4>
                <p style="text-align: center; color: white;">
                    Nous avons créé votre espace dédié.
                </p>
                <p style="text-align: center; color: white;">
                    Le cahier des charges sera envoyé à <strong>{user_details['email']}</strong> une fois complété.
                </p>
                """,
                unsafe_allow_html=True,
            )
            custom_button_style = """
                <style>
                    .custom-button {
                        display: block;
                        margin: 20px auto;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        color: white;
                        background: linear-gradient(90deg, #FF8C00, #FF5722);
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
                        transition: transform 0.2s, box-shadow 0.2s;
                    }
                    .custom-button:hover {
                        transform: scale(1.05);
                        box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.3);
                    }
                </style>
            """
            historique_container.markdown(custom_button_style, unsafe_allow_html=True)

            # Bouton pour démarrer la discussion
            historique_container.button(
                "🚀 Démarrer la discussion",
                on_click=start_new_discussion_callback,
            )

    elif st.session_state.current_step == 4:
        # Étape 4 : Démarrage de la discussion
        st.session_state.chat_history.append(
            {
                "human": None,
                "AI": """
                Bienvenue 👋! Je suis ravi de vous accompagner dans la création de votre cahier des charges IoT avec TEKIN. 
                Ce processus est structuré en plusieurs sections, chacune dédiée à un aspect spécifique de votre projet.  

                Je vous poserai des questions claires pour recueillir les informations essentielles. Une fois une section complétée, nous passerons à la suivante.  

                Appuyez sur "➡️ Prochaine section" pour continuer.
                """,
            }
        )
        display_historique(historique_container)

##############################################################################
#                               APP                                          #
##############################################################################  

# Initialisation 
title_container , historique_container , model_choice, memory_length, max_tokens , memory  , groq_chat , conversation , model  = app_init()

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

if 'history_summary' not in st.session_state:
    st.session_state.history_summary = [] 

if "current_step" not in st.session_state:
    st.session_state.current_step = 1  # Initialisation à l'étape 1

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
# Affichage du conteneur uniquement à l'étape 4
if st.session_state.current_step == 4:
    # Initialiser le conteneur
    input_question_container = init_input_user_container()

    # Champ de saisie pour la question utilisateur
    with input_question_container:
        if result["text"]:
            user_question = st.text_area(
                "Posez votre question ici 👇",
                value=result["text"],
                placeholder="Comment puis-je vous aider ?",
                key="text",
            )
        else:
            user_question = st.text_area(
                "Posez votre question ici 👇",
                placeholder="Comment puis-je vous aider ?",
                key="text",
            )

        # Afficher les boutons interactifs
        display_interactive_buttons(st, clear_text, clear_text_with_default)
setup_sidebar()
#display_summary_history()

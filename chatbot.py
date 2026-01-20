#chatbot.py
import streamlit as st
import os
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
import json
import tempfile
from buttons import display_interactive_buttons
from cahierDeCharge import section_prompts, system_prompt, generate_full_prompt , next_section , handle_token_limit_error_in_section
from cahierDeCharge import get_updated_prompt_template , display_summary_history , init , generate_summary_document
from database import save_to_google_sheets , connect_to_google_sheets , create_new_sheet_from_user 
from init import app_init , init_input_user_container
import html  

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






############# session per user #################
def get_user_email():
    """Retrieve the user email from session or assign 'guest'."""
    return st.session_state.get("user_details", {}).get("email", "guest")
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
        st.session_state.current_step = None  # Évitez les affichages inutiles d'étapes

        next_section()

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
        chat_key = f'chat_history_{email}'

        # Créer une nouvelle feuille avec les informations utilisateur
        user_sheet = create_new_sheet_from_user(email, first_name, last_name)
        
        # Mettre à jour la session avec la feuille actuelle
        st.session_state.current_sheet = user_sheet.title
        
        # Reset only the current user's chat history
        st.session_state[chat_key] = []

        # Reset the onboarding process
        st.session_state.current_step = 1  # Ensures UI resets properly

    except Exception as e:
        st.error(f"Erreur lors du démarrage de la discussion : {e}")
########################################################################################
#                               Fonction Utiles                                         #
########################################################################################
def get_user_email():
    """Retrieve the user email from session or assign 'guest'."""
    return st.session_state.get("user_details", {}).get("email", "guest")


def clear_text():
    """Generates a response only if user input is not empty, ensuring unique chat history per user."""
    user_input = st.session_state.get("text", "").strip()
    user_email = get_user_email()
    chat_key = f'chat_history_{user_email}'

    # Ensure chat history is initialized for this user
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Ignore if user input is empty
    if not user_input:
        historique_container.warning("Veuillez entrer un texte avant d'envoyer.", icon="⚠️")
        return

    try:
        # Convert chat history to LangChain-compatible format
        formatted_history = []
        for message in st.session_state[chat_key]:
            formatted_history.append({'role': 'user', 'content': message['human']})
            formatted_history.append({'role': 'assistant', 'content': message['AI']})

        # Format the prompt dynamically
        formatted_prompt = prompt_template.format_prompt(
            chat_history=formatted_history,  # User-specific chat history
            human_input=st.session_state["text"]  # Include the user's input
        ).to_messages()

        # Generate a response using the formatted prompt
        response = groq_chat(formatted_prompt)

        # Append user input and AI response to user-specific chat history
        st.session_state[chat_key].append({'human': st.session_state["text"], 'AI': response.content})

        # Save chat history to Google Sheets (optional)
        save_to_google_sheets(user_input, response.content, st.session_state.current_section)

        # Save to file if memory length is reached
        if len(st.session_state[chat_key]) % memory_length == 0:
            append_history_to_file(st.session_state[chat_key][-memory_length:], user_email)

    except Exception as e:
        # Handle token limit error
        if "rate_limit_exceeded" in str(e) or "Request too large" in str(e):
            st.session_state.current_section = "Génération de Cahier des Charges"

            # Append error message to history
            st.session_state[chat_key].append({
                'human': None,
                'AI': f"### {st.session_state.current_section}"
            })
            st.session_state[chat_key].append({
                'human': None,
                'AI': """
                ❌ **Vous avez atteint la limite de traitement.**  
                Vous êtes redirigé vers la dernière étape pour générer le cahier des charges basé sur les sections complétées.
                """
            })

            # Add download message
            st.session_state[chat_key].append({
                'human': None,
                'AI': '📥 [Cliquez ici pour télécharger le cahier de charge en format .txt]'
            })
        else:
            st.error(f"Erreur lors de la génération de la réponse : {str(e)}")

    # Clear user input field
    st.session_state["text"] = ""

def clear_text_with_default(default_input="Je ne sais pas"):
    """Génère une réponse avec une entrée utilisateur par défaut, en assurant un historique unique par utilisateur."""
    user_email = get_user_email()
    chat_key = f'chat_history_{user_email}'

    # Ensure chat history is initialized for this user
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    try:
        # Transform chat history to LangChain-compatible format
        formatted_history = []
        for message in st.session_state[chat_key]:
            formatted_history.append({'role': 'user', 'content': message['human']})
            formatted_history.append({'role': 'assistant', 'content': message['AI']})

        # Format the prompt dynamically with default input
        formatted_prompt = prompt_template.format_prompt(
            chat_history=formatted_history,
            human_input=default_input
        ).to_messages()

        # Generate a response using the formatted prompt
        response = groq_chat(formatted_prompt)

        # Append user input and AI response to user-specific chat history
        st.session_state[chat_key].append({'human': default_input, 'AI': response.content})

        # Save chat history if memory length is reached
        if len(st.session_state[chat_key]) % memory_length == 0:
            append_history_to_file(st.session_state[chat_key][-memory_length:], user_email)

    except Exception as e:
        # Gestion de l'erreur liée à la limite de tokens
        if "rate_limit_exceeded" in str(e) or "Request too large" in str(e):
            st.session_state.current_section = "Génération de Cahier des Charges"
            
            # Ajouter un message d'erreur à l'historique
            st.session_state[chat_key].append({
                'human': None,
                'AI': """
                ❌ **Vous avez atteint la limite de traitement.**  
                Vous êtes redirigé vers la dernière étape pour générer le cahier des charges basé sur les sections complétées.
                """
            })

            # Ajouter le message pour le bouton de téléchargement
            st.session_state[chat_key].append({
                'human': None,
                'AI': '📥 [Cliquez ici pour télécharger le cahier de charge en format .txt]'
            })
        else:
            st.error(f"Erreur lors de la génération de la réponse : {str(e)}")

#Enregistrer les données dans un fichier JSON 
HISTORY_FILE = "chat_history.json"

def save_history_to_file(history, user_email, filename="chat_history.json"):
    """Enregistre l'historique de la conversation pour un utilisateur spécifique dans un fichier JSON."""
    all_histories = load_all_histories(filename)
    all_histories[user_email] = history  # Store by email
    with open(filename, "w") as f:
        json.dump(all_histories, f, indent=4)

def append_history_to_file(new_messages, user_email, filename="chat_history.json"):
    """Ajoute de nouvelles conversations à l'historique spécifique d'un utilisateur."""
    history = load_history_from_file(user_email, filename)
    history.extend(new_messages)
    save_history_to_file(history, user_email, filename)

def load_history_from_file(user_email, filename="chat_history.json"):
    """Charge l'historique de conversation spécifique d'un utilisateur."""
    all_histories = load_all_histories(filename)
    return all_histories.get(user_email, [])  # Return only user's history

def load_all_histories(filename="chat_history.json"):
    """Charge tous les historiques de conversation depuis un fichier JSON."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}  # Return empty dict if file doesn't exist

def setup_sidebar():
    """Configure la barre latérale avec le logo, la progression des sections, et le bouton de réinitialisation."""
    user_email = get_user_email()
    chat_key = f'chat_history_{user_email}'

    # Display logo in sidebar
    st.sidebar.image('TEKIN logo 2019 couleur.png', use_container_width=True)
    
    # Display section progress
    display_section_progress()

    # Ensure user-specific chat history is initialized
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Reset conversation button
    if st.sidebar.button("🔄 Réinitialiser la conversation"):
        st.session_state[chat_key] = []  # Reset only the current user's chat history
        st.sidebar.success("Votre conversation a été réinitialisée.")

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
    """Displays the conversation history for the current user."""
    user_email = get_user_email()
    chat_key = f'chat_history_{user_email}'

    historique_container.subheader("📝 Conversation")

    # Ensure user-specific chat history is initialized
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    for message in st.session_state[chat_key]:  # Get user-specific chat history
        if message['human'] is None and message['AI'].startswith("Bienvenue 👋!"):
            # Welcome message with custom styling
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

        elif message['human'] is None and message['AI'].startswith("❌ **Vous avez atteint la limite de traitement.**"):
            # Display error messages with a specific style
            historique_container.error(message['AI'])

        elif message['human'] is None and message['AI'].startswith("###"):
            # Display section titles with a distinct style
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
            # Display thank-you message with styling
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
            # Generate and display Cahier des Charges download button
            cahier_content = generate_summary_document()

            # Save to Google Sheets
            save_to_google_sheets(None, None, None, cahier_content)

            historique_container.download_button(
                label="📥 Télécharger le cahier des charges",
                type="primary",
                data=cahier_content,
                file_name="cahier_des_charges.txt",
                mime="text/plain"
            )

        else:
            # Regular chat display (User & AI messages)
            with st.spinner("En écriture..."):
                if message["human"] and message["human"].strip():  # Ensure user message is not empty
                    historique_container.chat_message("user").write(message["human"])
                if message["AI"] and message["AI"].strip():  # Ensure AI response is not empty
                    historique_container.chat_message("assistant").write(message["AI"])

##############################################################################
#                          Display Intro Message                            #
##############################################################################
def display_intro_message(historique_container):
    """
    Gère les étapes pour démarrer une nouvelle discussion spécifique à l'utilisateur.
    """
    user_email = get_user_email()
    chat_key = f'chat_history_{user_email}'

    # Initialisation par défaut
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1  

    if st.session_state.current_step == 1:
        historique_container.markdown(
            """
            ## 👋 Bienvenue chez TEKIN !
            
            Nous sommes ravis de vous accompagner dans la réussite de votre projet IoT.
            
            ### 🔎 Comment ça fonctionne ?
            - Nous vous poserons des questions ciblées pour collecter toutes les informations nécessaires.
            - Chaque étape est dédiée à un aspect clé de votre projet.
            
            🎯 **Prêt à commencer ?**
            
            Cliquez sur le bouton ci-dessous pour débuter votre aventure avec TEKIN !
            """,
            unsafe_allow_html=False
        )

        col1, col2 = historique_container.columns(2)
        col1.button(
            "🆕 Nouvelle discussion",
            on_click=start_discussion_callback,
            use_container_width=True,
            type="primary"
        )

    elif st.session_state.current_step == 2:
        # Étape 2 : Formulaire pour les informations utilisateur
        historique_container.markdown(
            """
            ### 📝 Informations nécessaires
            
            Pour personnaliser votre expérience et vous permettre de télécharger le cahier des charges complet, nous avons besoin de quelques informations.
            
            **📧 Votre adresse e-mail est requise pour recevoir le document final.**
            """,
            unsafe_allow_html=False,
        )

        # Ajout des champs avec une indication claire des champs obligatoires
        first_name = historique_container.text_input(
            "Prénom *", 
            placeholder="Votre prénom", 
            key="first_name"
        )
        last_name = historique_container.text_input(
            "Nom *", 
            placeholder="Votre nom", 
            key="last_name"
        )
        email = historique_container.text_input(
            "Adresse e-mail *", 
            placeholder="exemple@domaine.com", 
            key="email"
        )

        # Affichage du bouton "Commencer" avec un rappel
        historique_container.button("Commencer", on_click=submit_user_info_callback, type="primary")

    elif st.session_state.current_step == 3:
        # Étape 3 : Confirmation
        user_details = st.session_state.get("user_details", {})

        if user_details:
            historique_container.markdown(
                f"""
                ## Merci {user_details['first_name']} {user_details['last_name']} !
                
                Nous avons créé votre espace dédié.
                
                Le cahier des charges sera envoyé à **{user_details['email']}** une fois complété.
                """,
                unsafe_allow_html=False,
            )

            # Bouton pour démarrer la discussion
            historique_container.button(
                "🚀 Démarrer la discussion",
                on_click=start_new_discussion_callback,
                type="primary"
            )

    elif st.session_state.current_step == 4:
        # Étape 4 : Démarrage de la discussion (par utilisateur)
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Vérifier que le message d'introduction n'a pas déjà été ajouté pour cet utilisateur
        if not any("Bienvenue 👋!" in msg['AI'] for msg in st.session_state[chat_key]):
            st.session_state[chat_key].append(
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

# Initialize user-specific chat history
user_email = get_user_email()

if f'chat_history_{user_email}' not in st.session_state:
    st.session_state[f'chat_history_{user_email}'] = []

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

user_email = get_user_email()
chat_key = f'chat_history_{user_email}'

if len(st.session_state.get(chat_key, [])) == 0:
    display_intro_message(historique_container)
else:
    display_historique(historique_container)



# Widget audio
#audio_input_widget()
# Affichage du conteneur uniquement à l'étape 4
if st.session_state.current_step == None:
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
                max_chars= 1000
                
            )
        else:
            user_question = st.text_area(
                "Posez votre question ici 👇",
                placeholder="Comment puis-je vous aider ?",
                key="text",
                max_chars= 1000
      
            )

        # Afficher les boutons interactifs
        display_interactive_buttons(st, clear_text, clear_text_with_default)
setup_sidebar()
#display_summary_history()

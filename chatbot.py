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
from cahierDeCharge import get_updated_prompt_template , display_summary_history , init

result = {
    "text": "",  # Chaîne de caractères pour le texte résultant
    "segments": [],  # Liste pour les détails au niveau des segments
    "language": None  # Langue détectée, initialement définie comme None
}
model = ""

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
# Charger le modèle Whisper avec mise en cache
@st.cache_resource
def load_model():
    return whisper.load_model("small" , device = "cpu") # Modèles possibles : tiny, base, small, medium, large

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

########################################################################################
#                               Fonction Utiles                                         #
########################################################################################
def clear_text():
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
#                               APP                                          #
##############################################################################  

title_container = st.container(border=False )
historique_container = st.container(border=True , height = 400)
input_question_container = st.container(border=True , height = 300)

title_container.title("🤖 TEKIN Assistant Chatbot !")
title_container.write("Bonjour ! Je suis ton assistant pour définir ton projet IOT et créer un premier cahier des charges.")


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

if 'history_summary' not in st.session_state:
    st.session_state.history_summary = [] 

init()
# Obtenir le prompt template mis à jour
prompt_template = get_updated_prompt_template()

model_choice = "llama3-70b-8192"
memory_length = 20
max_tokens = 8192

# Initialisation de la mémoire conversationnelle
memory = ConversationBufferWindowMemory(k=memory_length)

# Initialisation du chatbot Groq
groq_chat = ChatGroq(
    groq_api_key="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",
    model_name=model_choice,
    max_tokens = max_tokens
)

# Stocker groq_chat dans st.session_state
st.session_state.groq_chat = groq_chat

# Configuration de la chaîne de conversation
conversation = ConversationChain(
    llm=groq_chat,
    memory=memory
)

# Affichage de l'historique de la conversation
historique_container.subheader("Historique de la conversation")
for message in st.session_state.chat_history:
    with st.spinner("En écriture..."):
        historique_container.chat_message("user").write(message['human'])
        historique_container.chat_message("assistant").write(message['AI'])

# Charger le modèle Whisper
model = load_model()

# Widget audio
audio_input_widget()

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
display_summary_history()

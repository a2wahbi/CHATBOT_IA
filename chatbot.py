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
from speech_to_text import AudioInput

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

##############################################################################
#                               organisation                                 #
##############################################################################
title_container = st.container(border=False )
historique_container = st.container(border=True , height = 400)
input_question_container = st.container(border=True , height = 300)


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

def memory_status(history, memory_length):
    current_length = len(history)
    max_messages = 200 #limite maximale des messages 
    # Normaliser la progression entre 0 et 1 en fonction du maximum défini
    progress_value = min(current_length / max_messages, 1.0)

    messages_until_save = memory_length - (current_length % memory_length)

    st.sidebar.metric(
        label="Messages en mémoire",
        value=f"{current_length % memory_length}/{memory_length}",
        delta=f"Encore {messages_until_save} avant la sauvegarde"
    )

    st.sidebar.progress(progress_value, f"{current_length} messages sur {max_messages}")

    
#Confiuration de la SideBar
def setup_sidebar():
    """Configure la barre latérale Streamlit et retourne les options sélectionnées."""
    st.sidebar.image('TEKIN logo 2019 couleur.png', use_container_width=True)
    st.sidebar.write("## Options")
    
    # Sélection du modèle
    model_choice = st.sidebar.selectbox(
        "Choisissez un modèle :",
        ["llama3-70b-8192", "llama3-8b-8192"]
    )
    
    # Slider pour la longueur de la mémoire
    memory_length = st.sidebar.slider(
        "Longueur de mémoire conversationnelle :",
        min_value=3, max_value=20, value=10, step=2
    )

    #slider pour le nombre de tokens maximum
    max_tokens = st.sidebar.slider(
        "Nombre de tokens utiliser par l'assistant",
        min_value=50 , max_value= 8000 , value = 2000 , step = 100 
    )
    
    # Bouton pour réinitialiser la conversation
    if st.sidebar.button("Réinitialiser la conversation"):
        save_history_to_file([])  # Réinitialiser le fichier
        st.session_state.chat_history = []
        st.sidebar.success("Conversation réinitialisée.")
    
    # Affichage de l'état de la mémoire
    memory_status(st.session_state.chat_history, memory_length)


    st.sidebar.metric(
    label="Tokens sélectionnés",
    value=f"{max_tokens} tokens",
    )

    
    # Retourner les choix effectués
    return model_choice, memory_length , max_tokens


##############################################################################
#                               Prompting                                    #
##############################################################################

system_prompt = """
Tu es un assistant intelligent de l'entreprise TEKIN, spécialisée dans les projets IoT. Ta mission est d'interagir avec les clients pour :

1. **Comprendre les objectifs principaux de leur projet IoT** :
   - Identifie leurs attentes.
   - Détermine les problèmes qu'ils souhaitent résoudre.

2. **Définir les composants nécessaires** :
   - Capteurs, actionneurs, connectivité, et protocoles.

3. **Collecter les informations suivantes** :  
   - **Exigences fonctionnelles** :  
     - Fonctionnalités principales, collecte et traitement des données, communication, interface utilisateur.  
   - **Exigences non-fonctionnelles** :  
     - Performance, fiabilité, sécurité, consommation énergétique, durée de vie.  
   - **Exigences techniques** :  
     - Capteurs, spécifications matérielles, connectivité, portée, compatibilité, résistance environnementale.  
   - **Exigences réglementaires** :  
     - Normes, certifications, RGPD, cybersécurité.  
   - **Informations personnelles clés** :  
     - Numéro de téléphone, adresse e-mail.  

### Directives pour interagir avec le client :  
- Pose des **questions simples et précises**, basées sur les réponses précédentes.  
- Limite-toi à une **seule question à la fois** pour garantir la clarté.  
- Clarifie ou reformule les réponses ambiguës.  

### À la fin de la conversation :  
- Résume toutes les informations recueillies de manière structurée.  
- Prépare un **cahier des charges professionnel**, prêt à être transmis à l'équipe TEKIN.

**Ton attendu** :  
Professionnel, amical, et rassurant.

### Exemples de questions à poser :  
- Quels sont les principaux objectifs de votre projet ?  
- Quels types de capteurs envisagez-vous d'utiliser ?  
- Avez-vous des exigences spécifiques en matière de sécurité ?  

**Note** : Ce document est confidentiel et appartient à TEKIN. Ne pas reproduire sans autorisation.
"""

# Create the Chat Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{human_input}")
])

##############################################################################
#                               APP                                          #
##############################################################################  
title_container.title("🤖 TEKIN Assistant Chatbot !")
title_container.write("Bonjour ! Je suis ton assistant pour définir ton projet IOT et créer un premier cahier des charges.")


# Initialisation de l'historique de conversation dans la session
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = load_history_from_file()

model_choice , memory_length , max_tokens = setup_sidebar()
# Initialisation de la mémoire conversationnelle
memory = ConversationBufferWindowMemory(k=memory_length)

# Initialisation du chatbot Groq
groq_chat = ChatGroq(
    groq_api_key="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",
    model_name=model_choice,
    max_tokens = max_tokens
)

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

model = load_model()
audio_input_widget()
# Champ de saisie pour la question utilisateur

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
input_question_container.button("Envoyer" , type="secondary" , on_click= clear_text)

  


    
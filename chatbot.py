import streamlit as st
import os
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
import json


##############################################################################
#                               Styles                                       #
##############################################################################
# Charger le fichier CSS si le fichier existe
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

########################################################################################
#                               Fonction Utiles                                         #
########################################################################################
def clear_text(): 
    st.write(st.session_state["text"])  
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
        ["gemma2-9b-it", "gemma-7b-it", "llama3-70b-8192", "llama3-8b-8192"]
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
Tu es un assistant intelligent de l'entreprise TEKIN, spécialisée dans les projets IoT. Ta mission est d'interagir avec les clients pour :

1. Comprendre les objectifs principaux de leur projet IoT, en identifiant leurs attentes et les problèmes qu'ils souhaitent résoudre.

2. Déterminer les composants nécessaires :
   - Capteurs
   - Actionneurs
   - Connectivité
   - Protocoles de communication

3. Obtenir les informations suivantes : 

   ### Exigences fonctionnelles :
   - Fonctionnalités principales du produit
   - Capacités de collecte et de traitement des données
   - Modes de communication et protocoles utilisés
   - Interactions avec l'utilisateur et interface

   ### Exigences non-fonctionnelles :
   - Performance (temps de réponse, débit de données)
   - Fiabilité et disponibilité
   - Sécurité et confidentialité des données
   - Type d’alimentation
   - Consommation énergétique
   - Durée de vie de la batterie (si applicable)

   ### Exigences techniques :
   - Choix des capteurs et actionneurs
   - Spécifications du matériel (processeur, mémoire, stockage)
   - Connectivité sans fil (Wi-Fi, Bluetooth, LoRa, etc.)
   - Portée de la connectivité
   - Compatibilité avec les plateformes IoT existantes
   - Taille et forme du produit
   - Matériaux utilisés
   - Résistance environnementale (température, humidité, poussière)
   - Ergonomie et facilité d'utilisation

   ### Exigences réglementaires :
   - Conformité aux normes de sécurité
   - Certifications requises (CE, FCC, etc.)
   - Respect des réglementations sur la protection des données (RGPD)
   - Cybersécurité
   - Environnement spécifique (médical, aéronautique, etc.)

4. Collecter des informations personnelles clés :
   - Numéro de téléphone
   - Adresse e-mail

### Directives :

- À chaque étape :
  - Pose des questions claires et précises, adaptées aux réponses précédentes.
  - Limite-toi à une seule question à la fois pour faciliter la compréhension du client.
  - Reformule ou clarifie les réponses ambiguës pour garantir l'exactitude des informations.

- À la fin de la conversation :
  - Résume toutes les informations recueillies de manière structurée.
  - Prépare un cahier des charges clair et professionnel, prêt à être transmis à l'équipe TEKIN.

Adopte un ton professionnel, amical et rassurant pour mettre le client à l'aise et encourager un échange constructif.

Ce document confidentiel est la propriété de TEKIN et ne doit pas être reproduit ou communiqué sans autorisation.
"""


#Create the Chat Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content = system_prompt),
    MessagesPlaceholder(variable_name = "chat_history"),
    HumanMessagePromptTemplate.from_template("{human_input}")

]) 
##############################################################################
#                               APP                                          #
##############################################################################  
st.title("🤖 TEKIN Assistant Chatbot !")
st.write("Bonjour ! Je suis ton assistant pour définir ton projet IOT et créer un premier cahier des charges.")


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
st.subheader("Historique de la conversation")
for message in st.session_state.chat_history:
    st.chat_message("user").write(message['human'])
    st.chat_message("assistant").write(message['AI'])

# Champ de saisie pour la question utilisateur
with st.form("user_input_form"):
    user_question = st.text_input(
        "Posez votre question ici 👇",
        placeholder="Comment puis-je vous aider ?",
        key = "text"
    )
    col1, col2  = st.columns([10, 1])  # col1 est 3x plus large que col2
    with col1:
        submit_button = st.form_submit_button("Envoyer" , on_click = clear_text)
    with col2:
        micro_button = st.form_submit_button("🎤")
# Génération de la réponse IA et mise à jour de l'interface
if submit_button and user_question:
    with st.spinner("En écriture..."):
        try:
            # Transform chat history to LangChain-compatible format

            formatted_history = []
            for message in st.session_state.chat_history:
                formatted_history.append({'role': 'user', 'content': message['human']})
                formatted_history.append({'role': 'assistant', 'content': message['AI']})

            # Format the prompt dynamically
            formatted_prompt = prompt_template.format_prompt(
                chat_history=formatted_history,  # Pass the transformed chat history
                human_input=user_question  # Include the user's input
            ).to_messages()

            # Generate a response using the formatted prompt
            response = groq_chat(formatted_prompt)

            # Add the user input and AI response to the session's chat history
            st.session_state.chat_history.append({'human': user_question, 'AI': response.content})

            # Save to the file if memory length is reached
            if len(st.session_state.chat_history) % memory_length == 0:
                append_history_to_file(st.session_state.chat_history[-memory_length:])

            # Display the messages in the chat interface
            st.chat_message("user").write(user_question)
            st.chat_message("assistant").write(response.content)

            st.session_state["user_input"] = ""

        except Exception as e:
            st.error(f"Erreur lors de la génération de la réponse : {str(e)}") 
from layout import get_historique_container, get_title_container, get_input_question_container
from dotenv import load_dotenv
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
import streamlit as st
import whisper
from streamlit_extras.bottom_container import bottom
# Fonction pour initialiser tous les conteneurs
def init_container():
    title_container = get_title_container()
    historique_container = get_historique_container()
    with bottom():
        input_question_container = get_input_question_container()
    return title_container, historique_container, input_question_container

# Afficher les titres
def display_titles(title_container):
    title_container.title("🤖 TEKIN Assistant Chatbot !")
    title_container.write("Bonjour ! Je suis ton assistant pour définir ton projet IOT et créer un premier cahier des charges.")

# Charger les variables d'environnement
@st.cache_resource
def load_environment_variables():
    load_dotenv()

# Initialisation des paramètres pour le modèle IA
@st.cache_resource
def init_chat_parameters():
    model_choice = "llama3-70b-8192"
    memory_length = 20
    max_tokens = 8192
    return model_choice, memory_length, max_tokens

# Initialisation de la mémoire conversationnelle
@st.cache_resource
def init_configure_memory_buffer(memory_length):
    return ConversationBufferWindowMemory(k=memory_length)

# Initialisation du modèle IA
@st.cache_resource
def init_groq_chat(model_choice, max_tokens):
    return ChatGroq(
        groq_api_key="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",
        model_name=model_choice,
        max_tokens=max_tokens
    )

# Initialisation de la chaîne de conversation avec le modèle et la mémoire
def init_conversation_chain(groq_chat, memory):
    return ConversationChain(
        llm=groq_chat,
        memory=memory
    )

# Charger le modèle Whisper avec mise en cache
@st.cache_resource
def load_model_whisper():
    return whisper.load_model("small" , device = "cpu") # Modèles possibles : tiny, base, small, medium, large

# Fonction principale d'initialisation de l'application
def app_init():
    title_container , historique_container , input_question_container =  init_container()
    display_titles(title_container)
    load_environment_variables()
    model_choice, memory_length, max_tokens = init_chat_parameters()
    memory = init_configure_memory_buffer(memory_length)
    groq_chat = init_groq_chat(model_choice , max_tokens)
    conversation = init_conversation_chain(groq_chat , memory)
    model = load_model_whisper()
    return title_container , historique_container , input_question_container , model_choice, memory_length , max_tokens , memory , groq_chat , conversation , model 

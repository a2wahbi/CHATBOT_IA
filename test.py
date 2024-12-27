import streamlit as st
import os
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
import whisper
import tempfile

# Charger le modèle Whisper
@st.cache_resource
def load_model():
    return whisper.load_model("small", device="cpu")

def transcribe_audio(audio_data):
    """Transcrire l'audio en texte à l'aide de Whisper."""
    if audio_data is None:
        return ""
    model = load_model()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        audio_path = tmpfile.name
        try:
            tmpfile.write(audio_data.read())
            result = model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            st.error(f"Erreur pendant la transcription : {e}")
            return ""
        finally:
            os.unlink(audio_path)

# Initialisation de l'historique
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Interface utilisateur
st.title("🤖 TEKIN Assistant Chatbot !")
st.write("Bonjour ! Je suis là pour vous aider avec vos projets IoT.")

# Conteneur pour l'historique des messages
st.subheader("Historique de la conversation")
for message in st.session_state.chat_history:
    st.markdown(f"**Utilisateur :** {message['human']}")
    st.markdown(f"**Assistant :** {message['AI']}")

# Champ pour l'audio
st.write("### Saisissez une question ou utilisez un fichier audio")
audio_data = st.file_uploader("Téléchargez un fichier audio", type=["wav", "mp3"])

# Formulaire pour entrer du texte ou utiliser la transcription audio
with st.form("user_input_form"):
    # Transcrire l'audio si fourni
    transcribed_text = transcribe_audio(audio_data) if audio_data else ""
    
    # Champ texte avec remplissage automatique depuis l'audio
    user_input = st.text_input(
        "Votre question :",
        value=transcribed_text,
        placeholder="Écrivez ici ou utilisez un fichier audio pour transcrire.",
        key="user_input"
    )
    submit_button = st.form_submit_button("Envoyer")

# Traitement de l'entrée utilisateur
if submit_button and user_input.strip():
    # Ajouter la saisie de l'utilisateur dans l'historique
    st.session_state.chat_history.append({"human": user_input, "AI": "Réponse simulée de l'assistant."})
    # Afficher la réponse de l'IA (simulée ici)
    st.markdown(f"**Assistant :** Réponse simulée pour `{user_input}`")

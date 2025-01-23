#cahierDeCharge.py
import streamlit as st
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
from prompts import initial_questions, section_prompts , summary_sections , system_prompt , system_summary_prompt




def handle_token_limit_error_in_section(historique_container):
    """
    Gère les cas où la limite de tokens est atteinte dans une section.
    Affiche un message clair et ajoute un bouton pour aller directement à la dernière étape.
    """
    # Affiche un message d'erreur expliquant la situation
    historique_container.error(
        """
        ❌ **Limite atteinte : Données trop volumineuses**  
        L'IA a atteint sa limite de traitement pour cette section.  
        👉 **Veuillez continuer avec la section suivante** pour éviter de perdre des données.
        
        ⚠️ Note : Certaines parties de cette section pourraient ne pas être incluses dans le résumé final.
        """,
        icon="⚠️",
    )

    # Bouton pour aller directement à la dernière étape
    if historique_container.button(
        "📄 Aller à la dernière étape : Génération du cahier des charges", type="primary"
    ):
        # Mettre à jour la section actuelle
        st.session_state.current_section = "Génération de Cahier des Charges"

        # Ajouter un message de confirmation à l'historique
        st.session_state.chat_history.append({
            'human': None,
            'AI': """
            Vous avez choisi de passer directement à la dernière étape.  
            Vous pouvez maintenant générer le cahier des charges final.
            """
        })


         # Debug : vérifier l'historique
    st.write("État de l'historique après l'ajout :", st.session_state.chat_history)
##############################################################################
#                       FONCTIONS DE GÉNÉRATION DE PROMPTS                   # 
##############################################################################
def generate_full_prompt(current_section, previous_summaries):
    """
    Génère le prompt complet pour l'IA en combinant :
    - Le prompt général (system_prompt) : cadre global.
    - Le résumé des sections précédentes : contexte.
    - Le prompt spécifique à la section actuelle : objectif.

    Args:
        current_section (str): Nom de la section actuelle.
        previous_summaries (str): Résumé des sections précédentes.

    Returns:
        str: Prompt complet pour l'IA.
    """
    # Récupérer le prompt spécifique à la section actuelle
    section_prompt = section_prompts.get(current_section, "")
    
    # Combiner les différents éléments pour former le prompt complet
    full_prompt = f"""
    {system_prompt}
    
    ### Résumé des sections précédentes :
    {previous_summaries}
    
    ### Section actuelle : {current_section}
    {section_prompt}
    """
    return full_prompt

def generate_previous_summaries(completed_sections):
    """
    Combine tous les résumés déjà générés pour les sections complétées.
    Utilise les résumés réels stockés dans st.session_state.history_summary.
    """
    # Initialisation d’une liste pour stocker les résumés
    summaries = []
    
    # Parcourir les sections complétées
    for section in completed_sections:
        # Chercher le résumé correspondant dans l'historique
        summary = next(
            (entry['summary'] for entry in st.session_state.history_summary if entry['section'] == section),
            "(Résumé non disponible)"  # Par défaut si aucun résumé trouvé
        )
        # Ajouter le résumé formaté à la liste
        summaries.append(f"Résumé pour {section} : {summary}")
    
    # Combiner tous les résumés en un seul texte
    return "\n".join(summaries)


def generate_summary_prompt(system_summary_prompt, previous_summaries, section_name, summary_prompt):
    """
    Combine le system_summary_prompt, les résumés précédents, 
    et le prompt spécifique à la section actuelle pour créer un prompt complet.
    """
    return f"""
    {system_summary_prompt}
    
    ### Résumé des sections précédentes :
    {previous_summaries}
    
    ### Section actuelle : {section_name}
    {summary_prompt}
    """
    

    
##############################################################################
#                     FONCTIONS DE NAVIGATION ENTRE SECTIONS                 #
##############################################################################
def generate_summary_document():
    """Génère un document combinant tous les résumés en un seul fichier texte sans redondance."""
    summary_data = []

    for entry in st.session_state.history_summary:
        # Ajouter uniquement le contenu du résumé sans répéter le titre de la section
        summary_data.append(entry['summary'])
    
    return "\n\n".join(summary_data)

def next_section():
    """Passe à la section suivante ou propose de télécharger le résumé à la fin."""
    sections = list(section_prompts.keys())
    current_index = sections.index(st.session_state.current_section)

    # Générer le résumé pour la section actuelle
    generate_summary()

    if current_index < len(sections) - 1:
        # Passer à la section suivante
        st.session_state.current_section = sections[current_index + 1]

        # Ajouter le titre de la section à l'historique
        st.session_state.chat_history.append({
            'human': None,
            'AI': f"### {st.session_state.current_section}"
        })

        # Mettre à jour les prompts
        previous_summaries = generate_previous_summaries(sections[:current_index + 1])
        section_name = st.session_state.current_section
        summary_prompt = summary_sections.get(section_name, "Aucun prompt spécifique pour cette section.")
        st.session_state.full_summary_prompt = generate_summary_prompt(
            system_summary_prompt, 
            previous_summaries, 
            section_name, 
            summary_prompt
        )        
        st.session_state.full_prompt = generate_full_prompt(
            st.session_state.current_section, 
            previous_summaries
        )

        # Ajouter la question initiale de la section
        initial_question = initial_questions.get(section_name, "")
        if initial_question:
            st.session_state.chat_history.append({"human": "", "AI": initial_question})
            # Ajouter le message de fin et le bouton de téléchargement dans l'historique
        if st.session_state.current_section == "Génération de Cahier des Charges":

            final_message = """
            Félicitations 🎉 ! Vous avez terminé toutes les sections.  
            Vous pouvez maintenant télécharger le résumé complet en appuyant sur le bouton ci-dessous.
            """
            st.session_state.chat_history.append({
                'human': None,
                'AI': final_message
            })
            st.session_state.chat_history.append({
                'human': None,
                'AI': '📥 [Cliquez ici pour télécharger le résumé](download_link)'
            })  
    else:
         st.session_state.chat_history.append({
            'human': None,
            'AI': """
            Merci pour votre confiance et d'avoir choisi TEKIN. Vous êtes déjà à la fin du processus.
            Si vous avez d'autres questions, n'hésitez pas à les poser ! 😊
            """
        })
        
##############################################################################
#                     FONCTIONS DE GESTION DES RÉSUMÉS                       #
##############################################################################

def generate_summary():
    """Génère un résumé pour la section actuelle et l'ajoute à l'historique des résumés."""
    try:
        # Ignorer la section Accueil
        if st.session_state.current_section == "Accueil":
            return

        # Vérifier si 'groq_chat' est bien initialisé
        if 'groq_chat' not in st.session_state:
            st.error("groq_chat n'est pas initialisé. Assurez-vous que la configuration est correcte.")
            return

        # Vérifier que l'historique des conversations est non vide
        if not st.session_state.chat_history:
            st.warning("Aucune conversation disponible pour générer un résumé.")
            return

        # Transformer l'historique des conversations en format compatible LangChain
        formatted_history = [
            {'role': 'user', 'content': msg['human']} if idx % 2 == 0 else {'role': 'assistant', 'content': msg['AI']}
            for idx, msg in enumerate(st.session_state.chat_history)
        ]

        # Ajouter une consigne explicite pour forcer la structure
        section_prompt = summary_sections.get(st.session_state.current_section, "")
        structured_prompt = f"""
        Résume la section '{st.session_state.current_section}' en respectant strictement la structure suivante :
        
        {section_prompt}
        """

        # Construire le prompt
        summary_prompt = prompt_summary.format_prompt(
            chat_history=formatted_history,
            human_input=structured_prompt
        ).to_messages()

        # Appeler le modèle pour générer le résumé
        response = st.session_state.groq_chat(summary_prompt)

        # Ajouter le résumé généré à l'historique des résumés
        st.session_state.history_summary.append({
            'section': st.session_state.current_section,
            'summary': response.content
        })
    except Exception as e:
        st.error(f"Erreur lors de la génération du résumé : {str(e)}")

def display_summary_history():
    """Affiche l'historique des résumés dans l'interface Streamlit."""
    st.subheader("Historique des Résumés")
    if st.session_state.history_summary:
        for entry in st.session_state.history_summary:
            with st.expander(f"Résumé pour la section : {entry['section']}"):
                st.text_area("Résumé :", entry['summary'], height=150, key=f"summary_{entry['section']}")
    else:
        st.info("Aucun résumé disponible.")


##############################################################################
#                     5. FONCTIONS DE GESTION DES TEMPLATES DE PROMPTS       #
##############################################################################

def get_updated_internal_summary_prompt_template():
    """Retourne un template de prompt mis à jour pour les résumés internes."""
    full_summary_prompt = st.session_state.get("full_summary_prompt", "Default summary prompt")
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=full_summary_prompt),
        MessagesPlaceholder(variable_name="history_summary"),
        HumanMessagePromptTemplate.from_template("{human_input}")
    ])

# Fonction pour générer le Chat Prompt Template
def get_updated_prompt_template():
    """Retourne le prompt_template mis à jour avec le full prompt actuel."""
    full_prompt = st.session_state.get("full_prompt", "Default system prompt")
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=full_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}")
    ])

##############################################################################
#                            6. INITIALISATION                              #
##############################################################################
def init():
    """Initialise les variables globales nécessaires."""

    # Initialiser le full_summary_prompt avec system_summary_prompt
    st.session_state.full_summary_prompt = system_summary_prompt
    global prompt_summary
    prompt_summary = ChatPromptTemplate.from_messages([
        SystemMessage(content=st.session_state.full_summary_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{human_input}")
    ])


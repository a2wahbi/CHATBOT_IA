
import streamlit as st
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage


##############################################################################
#                             1. DÉFINITIONS DES DONNÉES                     #
##############################################################################
system_summary_prompt = """
Tu es un assistant spécialisé dans la rédaction de résumés techniques pour des projets IoT.
Ton rôle est de synthétiser les informations collectées et de rédiger des résumés clairs, précis et structurés.

### Directives générales pour rédiger le résumé :
1. Respecte strictement la structure attendue pour chaque section.
2. Utilise un langage professionnel et formel.
3. Limite-toi uniquement aux informations fournies par l'utilisateur.
4. Si une information est manquante, indique clairement "[Information manquante]".
5. Ne pose aucune question dans le résumé et évite toute supposition.

"""
summary_sections = {
    "Introduction et Contexte": """
    ### Introduction et Contexte
    
    Cette section a pour objectif de fournir une vue d'ensemble du projet. Remplis chaque champ de manière concise et précise en suivant ces points :
    
    - **Objectifs du document** : Quels sont les buts principaux de ce cahier des charges ? Définis les grandes lignes des attentes du client.
    - **Présentation du projet** : Décris le contexte, les problèmes que le projet cherche à résoudre, et les objectifs globaux.
    - **Parties prenantes** : Liste les intervenants clés (client, développeurs, utilisateurs finaux) et précise leurs rôles.
    - **Périmètre du projet** : Délimite ce qui est inclus et exclu du projet, en spécifiant les limites claires.

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Objectifs du document** : [Votre réponse ici]
    - **Présentation du projet** : [Votre réponse ici]
    - **Parties prenantes** : [Votre réponse ici]
    - **Périmètre du projet** : [Votre réponse ici]
    """,

    "Description Fonctionnelle": """
    ### Description Fonctionnelle
    
    Cette section décrit les fonctionnalités principales et secondaires du système IoT. Remplis chaque champ en suivant ces points :
    
    - **Cas d'utilisation** : Présente les scénarios dans lesquels le système sera utilisé. Qui sont les utilisateurs et comment interagissent-ils avec le système ?
    - **Fonctionnalités principales** : Détaille les fonctionnalités essentielles (ex. collecte de données, transmission, interface utilisateur).
    - **Fonctionnalités secondaires** : Liste les fonctionnalités supplémentaires qui apportent une valeur ajoutée (ex. notifications, mises à jour OTA).

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Cas d'utilisation** : [Votre réponse ici]
    - **Fonctionnalités principales** : [Votre réponse ici]
    - **Fonctionnalités secondaires** : [Votre réponse ici]
    """,

    "Spécifications Techniques": """
    ### Spécifications Techniques
    
    Cette section détaille les aspects techniques du système IoT. Renseigne les champs suivants avec précision :
    
    - **Architecture Système** : Décris le matériel (microcontrôleurs, capteurs, modules de communication) et le logiciel (systèmes d'exploitation, middleware, applications embarquées).
    - **Interfaces et Protocoles** : Précise les interfaces physiques (GPIO, UART, SPI, etc.) et les protocoles de communication utilisés (ex. MQTT, CoAP).
    - **Contraintes** : Liste les contraintes spécifiques (performances, environnementales, sécurité, etc.).

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Architecture Système** : [Votre réponse ici]
    - **Interfaces et Protocoles** : [Votre réponse ici]
    - **Contraintes** : [Votre réponse ici]
    """,

    "Spécifications des Données": """
    ### Spécifications des Données
    
    Cette section se concentre sur les données collectées, leur traitement et leur stockage. Remplis chaque champ en suivant ces points :
    
    - **Type de données collectées** : Décris les types de données, leur fréquence de collecte, et leur taille approximative.
    - **Flux de données** : Explique comment les données circulent entre les différents modules (ex. edge devices, gateways, cloud).
    - **Stockage et gestion des données** : Indique les besoins en stockage, les mécanismes de sauvegarde, et les méthodes de gestion des données.

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Type de données collectées** : [Votre réponse ici]
    - **Flux de données** : [Votre réponse ici]
    - **Stockage et gestion des données** : [Votre réponse ici]
    """,

    "Contraintes et Normes": """
    ### Contraintes et Normes
    
    Cette section identifie les contraintes et réglementations à respecter. Fournis les informations pour chaque point ci-dessous :
    
    - **Réglementations** : Quelles normes locales et internationales s'appliquent (ex. CE, FCC, ISO) ?
    - **Contraintes financières** : Quel est le budget alloué ?
    - **Contraintes temporelles** : Quels sont les délais de livraison et les jalons principaux ?
    - **Contraintes techniques spécifiques** : Précise les exigences particulières (ex. compatibilité, évolutivité).

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Réglementations** : [Votre réponse ici]
    - **Contraintes financières** : [Votre réponse ici]
    - **Contraintes temporelles** : [Votre réponse ici]
    - **Contraintes techniques spécifiques** : [Votre réponse ici]
    """,

    "Partie à Externaliser": """
    ### Partie à Externaliser
    
    Cette section identifie les parties du projet à externaliser. Complète chaque champ comme suit :
    
    - **Composants à externaliser** : Liste les matériels ou logiciels qui doivent être externalisés.
    - **Raisons de l'externalisation** : Explique pourquoi ces parties spécifiques doivent être externalisées (ex. manque de compétences internes, gain de temps).
    - **Critères de sélection des prestataires** : Décris les critères pour choisir les prestataires externes.

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
    - **Composants à externaliser** : [Votre réponse ici]
    - **Raisons de l'externalisation** : [Votre réponse ici]
    - **Critères de sélection des prestataires** : [Votre réponse ici]
    """
}
# Prompts spécifiques pour chaque section
section_prompts = {
    "Accueil": """
    Vous êtes dans la section "Accueil".

    L'objectif de cette section est de présenter brièvement le déroulement du processus au client. Voici les points à expliquer :
    - Le processus est structuré en plusieurs sections (Introduction, Description Fonctionnelle, Spécifications Techniques, etc.).
    - Chaque section abordera un aspect spécifique du projet IoT.
    - À chaque étape, posez des questions simples et précises pour collecter les informations nécessaires.
    - Une fois toutes les informations d'une section recueillies, invitez le client à appuyer sur le bouton "Passer à la prochaine section" pour continuer.

    Formulez un message d'accueil professionnel et rassurant, en expliquant clairement ces étapes.
    Lorsque tu as dis tous ces informations , invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section
    """
    ,

    "Introduction et Contexte": """
    Nous travaillons actuellement sur la section "Introduction et Contexte".
    L'objectif de cette section est de :
    - Décrire les attentes générales du projet.
    - Présenter le contexte, le problème à résoudre, et les objectifs globaux.
    - Identifier les parties prenantes et leurs rôles.
    - Délimiter ce qui est inclus et exclu du projet.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Description Fonctionnelle": """
    Nous passons à la section "Description Fonctionnelle".
    L'objectif de cette section est de :
    - Décrire les cas d'utilisation typiques du système IoT.
    - Identifier les fonctionnalités principales et secondaires.

    Cette section comporte plusieurs parties :
    1. **Cas d'utilisation** : Quels sont les scénarios dans lesquels le système sera utilisé ?
    2. **Fonctionnalités principales** :
        - Collecte de données (capteurs, entrées utilisateurs, etc.).
        - Transmission de données (via Wi-Fi, Bluetooth, LPWAN, etc.).
        - Traitement des données (local ou cloud).
        - Interface utilisateur (application mobile, web, ou interface physique).
    3. **Fonctionnalités secondaires** : Notifications, sauvegarde, mises à jour OTA (Over-The-Air), etc.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Spécifications Techniques": """
    Nous abordons maintenant la section "Spécifications Techniques".
    L'objectif de cette section est de :
    - Définir l'architecture matérielle (microcontrôleurs, capteurs, modules de communication).
    - Décrire le logiciel (système d'exploitation, middleware, applications embarquées).
    - Identifier les interfaces physiques(GPIO, UART, SPI, I2C, etc.) et les protocoles de communication (MQTT, CoAP, HTTP, etc.).
    - Préciser les contraintes (performances, environnementales, sécurité).

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Spécifications des Données": """
    Nous passons à la section "Spécifications des Données".
    L'objectif de cette section est de :
    - Identifier le type de données collectées (nature, fréquence, taille).
    - Décrire le flux des données entre les différents modules.
    - Définir les besoins en stockage et en gestion des données.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Contraintes et Normes": """
    Nous travaillons maintenant sur la section "Contraintes et Normes".
    L'objectif de cette section est de :
    - Identifier les réglementations applicables.
    - Définir les contraintes financières, temporelles et techniques.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Partie à Externaliser": """
    Nous abordons la dernière section : "Partie à Externaliser".
    L'objectif de cette section est de déterminer les parties du projet à externaliser.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "Passer à la prochaine section"
    """,

    "Génération de Cahier des Charges": """
    Nous avons terminé de collecter toutes les informations nécessaires pour rédiger le cahier des charges de votre projet IoT.

    Merci de générer une réponse professionnelle et amicale qui :
    - Remercie le client pour sa collaboration.
    - Informe que le cahier des charges sera envoyé par e-mail.
    - Demande l'adresse e-mail pour l'envoi du document final.
    - Propose de répondre à toute autre question ou besoin de clarification.

    Formule la réponse de manière claire et polie.
    """
}

system_prompt = """
Tu es un assistant intelligent de l'entreprise TEKIN, spécialisée dans les projets IoT. Ta mission est d'interagir avec les clients pour élaborer un cahier des charges complet et structuré.

### Objectifs de ta mission :
1. **Comprendre les objectifs principaux du projet IoT** :
   - Identifier les attentes du client.
   - Déterminer les problèmes qu'ils souhaitent résoudre.

2. **Définir les composants nécessaires** :
   - Capteurs, actionneurs, connectivité, protocoles, et autres éléments essentiels.

3. **Collecter toutes les informations pour chaque section** :
   - **Introduction et Contexte** : Objectifs, présentation du projet, parties prenantes, périmètre.
   - **Description Fonctionnelle** : Cas d'utilisation, fonctionnalités principales et secondaires.
   - **Spécifications Techniques** : Architecture matérielle et logicielle, interfaces, protocoles, contraintes.
   - **Spécifications des Données** : Type, fréquence, flux, stockage, sécurité.
   - **Contraintes et Normes** : Réglementations, budget, délais, exigences spécifiques.
   - **Parties à Externaliser** : Identifier les tâches ou composants à externaliser.

4. **Clôturer la discussion** :
   - Remercier le client pour sa collaboration.
   - Demander l'adresse e-mail pour envoyer le cahier des charges final.

### Directives pour interagir avec le client :
- Pose des **questions claires et ciblées**, adaptées à la section en cours.
- Reste **professionnel, amical, et rassurant**.
- Limite-toi à **une question à la fois** pour garantir la clarté.
- Clarifie ou reformule les réponses si elles sont ambiguës ou incomplètes.

### À la fin de chaque section :
- Résume les informations collectées.
- Informe le client avant de passer à la section suivante.

**Ton attendu** :
- Collecte complète et précise des informations.
- Rédaction d'un cahier des charges structuré et conforme aux attentes du client.

### Exemples de questions pour guider la conversation :
- Quels sont les principaux objectifs de votre projet ?
- Quels types de capteurs ou de connectivité envisagez-vous ?
- Y a-t-il des contraintes environnementales ou de sécurité spécifiques à respecter ?
- Qui sont les utilisateurs finaux du système ?

**Note importante** : Ce document est confidentiel et appartient à TEKIN. Ne pas reproduire sans autorisation.
"""
##############################################################################
#                       2. FONCTIONS DE GÉNÉRATION DE PROMPTS               #
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
#                     3. FONCTIONS DE NAVIGATION ENTRE SECTIONS             #
##############################################################################
def next_section():
    """Passe à la section suivante, génère un résumé, et met à jour le full prompt."""
    
    #Renvoie toutes les sections disponibles sous forme de clés dans le dictionnaire section_prompts
    sections = list(section_prompts.keys())

    #Détermine la position de la section actuelle dans la liste des sections.
    current_index = sections.index(st.session_state.current_section)

    # Générer le résumé pour la section actuelle
    generate_summary()

    #Vérifie s'il y'as une section suivante 
    if current_index < len(sections) - 1:

        # Passer à la section suivante
        st.session_state.current_section = sections[current_index + 1]

        # Combiner l'ensemble de résumé 
        previous_summaries = generate_previous_summaries(sections[:current_index + 1])

        # Récupérer le prompt de résumé pour la nouvelle section
        section_name = st.session_state.current_section
        summary_prompt = summary_sections.get(section_name, "Aucun prompt spécifique pour cette section.")

        st.code(summary_prompt)
        # Combiner les prompts pour le résumé
        st.session_state.full_summary_prompt = generate_summary_prompt(
            system_summary_prompt, 
            previous_summaries, 
            section_name, 
            summary_prompt
        )

        st.code("full \n " + st.session_state.full_summary_prompt )

        # Mettre à jour le prompt global utilisé pour guider l’IA dans la nouvelle section.
        st.session_state.full_prompt = generate_full_prompt(
            st.session_state.current_section, 
            previous_summaries
        )
    else:
        st.warning("Vous êtes déjà à la dernière section.")

##############################################################################
#                     4. FONCTIONS DE GESTION DES RÉSUMÉS                   #
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

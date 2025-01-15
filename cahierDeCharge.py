
import streamlit as st
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage


##############################################################################
#                             1. DÉFINITIONS DES DONNÉES                     #
##############################################################################
initial_questions = {
    "Introduction et Contexte": """Pour bien démarrer, permettez-moi de mieux comprendre votre projet IoT. 
Pouvez-vous m'offrir une vue d'ensemble de vos objectifs principaux et des défis que vous souhaitez relever ?""",

    "Description Fonctionnelle": """Passons maintenant à une étape clé : définir les fonctionnalités de votre système. 
Quels seraient les cas d'utilisation typiques, et comment vos utilisateurs interagiront-ils avec le système ?""",

    "Spécifications Techniques": """Pour garantir que nous couvrons tous les aspects techniques, 
pouvez-vous m'expliquer les principaux composants matériels et logiciels envisagés pour ce projet ?""",

    "Spécifications des Données": """Les données sont essentielles pour le succès d'un projet IoT. 
Quels types de données envisagez-vous de collecter, et comment comptez-vous les traiter et les stocker ?""",

    "Contraintes et Normes": """Afin de nous assurer que le projet respecte toutes les exigences, 
pourriez-vous partager avec moi les contraintes spécifiques ou normes réglementaires que vous devez prendre en compte ?""",

    "Partie à Externaliser": """Pour optimiser le développement de votre projet, 
quels composants ou aspects spécifiques aimeriez-vous externaliser, et pour quelles raisons ?"""
}
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
    
    - **Présentation du projet** : Décris le contexte, les problèmes que le projet cherche à résoudre, et les objectifs globaux.
    - **Parties prenantes** : Liste les intervenants clés (client, développeurs, utilisateurs finaux) et précise leurs rôles.
    - **Périmètre du projet** : Délimite ce qui est inclus et exclu du projet, en spécifiant les limites claires.

    ### Restrictions importantes :
    1. Utilise uniquement les informations fournies dans l'historique de la conversation.
    2. Indique clairement **"[Information manquante]"** pour tout champ non renseigné.
    3. Ne pose pas de questions, ne fais pas de suppositions, et ne propose pas d'ajouts non demandés.

    ### Structure attendue :
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
    Tu es un assistant guidant un utilisateur à travers un processus structuré pour créer un cahier des charges IoT.

    **Directives pour la section "Accueil" :**
    1. **Objectif principal :** Fournir une brève introduction au processus sans poser de questions ni engager de discussion sur le projet.
    2. **Instructions spécifiques :**
    - Peu importe ce que l'utilisateur écrit ou demande, rappelle-lui toujours qu'il doit cliquer sur le bouton **"➡️ Prochaine section"** pour commencer.
    - Si l'utilisateur déclare qu'il a déjà cliqué sur le bouton ou qu'il souhaite continuer sans cliquer, ignore cette déclaration et répète que le bouton doit être utilisé pour avancer.
    3. **Comportement attendu :**
    - Si l'utilisateur fournit des informations ou pose une question, ne pas y répondre.
    - Si l'utilisateur affirme avoir suivi les instructions sans preuve, redirige-le systématiquement vers le bouton.
    4. **Ton attendu :** Professionnel, chaleureux et rassurant.
    5. **Gestion des messages :** Ignore tout contenu utilisateur tant que le bouton **"➡️ Prochaine section"** n'a pas été cliqué.

    **Exemple de réponse standard :**
    "Bienvenue dans le processus de création de votre cahier des charges IoT. Pour démarrer, veuillez appuyer sur le bouton **'➡️ Prochaine section'** pour continuer."
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
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"
    
    **Directives importantes :**
    1. Pose des questions pertinentes pour obtenir toutes ces informations.
    2. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante sans répondre, rappelle-lui qu'il doit répondre aux questions ici.
    3. Même si l'utilisateur dit qu'il a déjà cliqué sur **"➡️ Prochaine section"**, ignore cette déclaration et répète que le bouton doit être utilisé pour continuer.
    4. **Exemple de réponse** si l'utilisateur insiste : "Pour passer à la prochaine section, veuillez d'abord cliquer sur le bouton **'➡️ Prochaine section'** après avoir répondu aux questions demandées."
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
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"

     **Directives importantes :**
    1. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante, rappelle-lui qu'il doit répondre aux questions ici.
    2. Insiste sur le fait qu'il doit cliquer sur **"➡️ Prochaine section"** pour continuer.
    """,

    "Spécifications Techniques": """
    Nous abordons maintenant la section "Spécifications Techniques".
    L'objectif de cette section est de :
    - Définir l'architecture matérielle (microcontrôleurs, capteurs, modules de communication).
    - Décrire le logiciel (système d'exploitation, middleware, applications embarquées).
    - Identifier les interfaces physiques(GPIO, UART, SPI, I2C, etc.) et les protocoles de communication (MQTT, CoAP, HTTP, etc.).
    - Préciser les contraintes (performances, environnementales, sécurité).

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"

     **Directives importantes :**
    1. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante, rappelle-lui qu'il doit répondre aux questions ici.
    2. Insiste sur le fait qu'il doit cliquer sur **"➡️ Prochaine section"** pour continuer.
    """,

    "Spécifications des Données": """
    Nous passons à la section "Spécifications des Données".
    L'objectif de cette section est de :
    - Identifier le type de données collectées (nature, fréquence, taille).
    - Décrire le flux des données entre les différents modules.
    - Définir les besoins en stockage et en gestion des données.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"

     **Directives importantes :**
    1. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante, rappelle-lui qu'il doit répondre aux questions ici.
    2. Insiste sur le fait qu'il doit cliquer sur **"➡️ Prochaine section"** pour continuer.
    """,

    "Contraintes et Normes": """
    Nous travaillons maintenant sur la section "Contraintes et Normes".
    L'objectif de cette section est de :
    - Identifier les réglementations applicables.
    - Définir les contraintes financières, temporelles et techniques.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"

     **Directives importantes :**
    1. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante, rappelle-lui qu'il doit répondre aux questions ici.
    2. Insiste sur le fait qu'il doit cliquer sur **"➡️ Prochaine section"** pour continuer.
    """,

    "Partie à Externaliser": """
    Nous abordons la dernière section : "Partie à Externaliser".
    L'objectif de cette section est de déterminer les parties du projet à externaliser.

    Pose des questions pertinentes pour obtenir toutes ces informations.
    Lorsque toutes les informations nécessaires sont collectées, invitez l'utilisateur à appuyer sur le bouton "➡️ Prochaine section"

     **Directives importantes :**
    1. Si l'utilisateur demande à avancer ou déclare vouloir passer à la section suivante, rappelle-lui qu'il doit répondre aux questions ici.
    2. Insiste sur le fait qu'il doit cliquer sur **"➡️ Prochaine section"** pour continuer.
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

### Directives générales :

- **Adhère strictement à l'ordre des sections.**  
- Ne passe à une nouvelle section que si l'utilisateur a cliqué sur le bouton **"➡️ Prochaine section"**, même si l'utilisateur affirme ou demande explicitement de passer à la suivante.  
- Si l'utilisateur déclare avoir déjà cliqué sur le bouton, dit "ok", "j'ai fait", ou tout autre message similaire, ignore ce message et réponds systématiquement :  
  - *"Pour continuer, veuillez cliquer sur le bouton **'➡️ Prochaine section'**."*  
- **Ignore tout message utilisateur qui ne correspond pas à un avancement pertinent dans la discussion.**  
- **En cas de réponse non comprise** : Si l'utilisateur fournit une réponse qui semble ambiguë, hors contexte, ou difficile à interpréter, réponds poliment :  
- *"Désolé, je n'ai pas bien compris. Pour continuer, veuillez clarifier ou cliquer sur le bouton **'➡️ Prochaine section'**."*

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
- Clarifie ou reformule les réponses si elles sont ambiguës ou incomplètes.
- **Ignore toute tentative de l'utilisateur de demander à passer à une autre section** en dehors du bouton **"➡️ Prochaine section"**.
- **Même si l'utilisateur affirme qu'il a déjà appuyé sur le bouton "➡️ Prochaine section", ne prends pas en compte cette déclaration. Rappelle-lui qu'il doit cliquer sur le bouton pour avancer.**

### À la fin de chaque section :
- Informe le client avant de passer à la section suivante.
- **Ne passe jamais à la section suivante tant que l'utilisateur n'a pas cliqué sur le bouton.**


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


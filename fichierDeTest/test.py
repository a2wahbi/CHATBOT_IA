def display_intro_message(Historique_container):
    """
    Gère les étapes pour démarrer une nouvelle discussion.
    """
    # Initialisation par défaut
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1  


    if st.session_state.current_step == 1:
        # Message d'accueil stylisé
        Historique_container.markdown(
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
        Historique_container.button("🆕 Nouvelle discussion" , on_click = start_discussion_callback , )

    elif st.session_state.current_step == 2:
                    
                    # Étape 2 : Formulaire pour les informations utilisateur
                    Historique_container.markdown(
                            """
                            <h5 style="text-align: center; color: #FF5722;">📝 Informations nécessaires</h5>
                            <p style="text-align: center; color: white;">
                                Avant de commencer, merci de renseigner vos informations.
                            </p>
                            """,
                            unsafe_allow_html=True,
                        )
                    first_name = historique_container.text_input("Prénom", placeholder="Votre prénom", key="first_name")
                    last_name = historique_container.text_input("Nom", placeholder="Votre nom", key="last_name")
                    email = historique_container.text_input("Adresse e-mail", placeholder="exemple@domaine.com", key="email")

                    historique_container.button(
                                            "Commencer",
                                            on_click=submit_user_info_callback,
                                            )

    elif st.session_state.current_step == 3:
        # Étape 3 : Confirmation
        user_details = st.session_state.get("user_details", {})

        if user_details:
            Historique_container.markdown(
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
        Historique_container.markdown(custom_button_style, unsafe_allow_html=True)

        # Bouton Streamlit avec style appliqué
        Historique_container.button("🚀 Démarrer la discussion", key="start_discussion_button", use_container_width=True , on_click = start_discussion_callback,)


    elif st.session_state.current_step == 4:
        # Étape 4 : Démarrage de la discussion
        st.session_state.chat_history.append({
            'human': None,
            'AI': """
            Bienvenue 👋! Je suis ravi de vous accompagner dans la création de votre cahier des charges IoT avec TEKIN. 
            Ce processus est structuré en plusieurs sections, chacune dédiée à un aspect spécifique de votre projet.  

            Je vous poserai des questions claires pour recueillir les informations essentielles. Une fois une section complétée, nous passerons à la suivante.  

            Appuyez sur "➡️ Prochaine section" pour continuer.
            """
        })
        display_historique(Historique_container)

        # Réinitialisation pour les prochaines discussions
        st.session_state.current_step = 1
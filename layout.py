import streamlit as st

def get_title_container():
    return st.container(border=False )

def get_historique_container():
    return st.container(border=True , height = 400)

def get_input_question_container():
    return st.container(border=True , height = 300)

# Initialisation des conteneurs
title_container = get_title_container()
historique_container = get_historique_container()
input_question_container = get_input_question_container()
import streamlit as st 


class TitlesView: 
    """ Manage the widgets in titles container """
    def __init__(self, border):
        self.border = border
        pass


    def build_titles_with_container(self):
       with st.container(border=self.border):
           st.title("🤖 TEKIN Assistant Chatbot !")
           st.write("Bonjour ! Je suis ton assistant pour définir ton projet IOT et créer un premier cahier des charges.")


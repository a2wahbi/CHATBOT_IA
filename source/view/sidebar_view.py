import streamlit as st 


class SideBarView: 
    """ Manage the widgets in the side bar: logo , the progress of the sections and  """
    def __init__(self):
        self.logo = '/Users/ahmedaminewahbi/Documents/tekin /PROJET_IA/chatbot_ia_origin/images/TEKIN logo 2019 couleur.png'
        pass


    def display_Logo(self , use_container_width):
        st.sidebar.image(self.logo, use_container_width= use_container_width )
    
    def display_Section_Progress(self):
        st.sidebar.markdown("## Progression")


sidebar_display = SideBarView()
sidebar_display.display_Logo(True)
sidebar_display.display_Section_Progress()
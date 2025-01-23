import streamlit as st 


class SideBarView: 
    """ Manage the widgets in the side bar: logo , the progress of the sections and  """
    def __init__(self):
        self.logo = '/Users/ahmedaminewahbi/Documents/tekin /PROJET_IA/chatbot_ia_origin/images/TEKIN logo 2019 couleur.png'
        self.sections = ["Accueil" , "Introduction et Contexte" , "Description Fonctionnelle" , "Spécifications Techniques" , "Spécifications des Données" , "Contraintes et Normes" , "Partie à Externaliser" ,"Génération de Cahier des Charges"]
        pass


    def display_Logo(self , use_container_width):
        st.sidebar.image(self.logo, use_container_width= use_container_width )
    
    def display_Section_Progress(self , current_section):
        st.sidebar.markdown("## Progression des sections")
        sections = self.sections
        current_index = sections.index(current_section)
        total_sections = len(sections)
        progress_value = (current_index + 1) / total_sections

        st.sidebar.progress(progress_value , text=f"Section {current_index + 1} sur {total_sections}")
        for idx, section in enumerate(sections):
            icon = "✅" if idx < current_index else "🚀" if idx == current_index else "⏳"
            color = "steelblue" if idx < current_index else "darkorange" if idx == current_index else "gray"
            st.sidebar.markdown(f"{icon} <span style='color: {color}; font-weight: bold;'>{section}</span>", unsafe_allow_html=True)


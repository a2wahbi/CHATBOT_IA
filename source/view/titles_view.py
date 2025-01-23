import streamlit as st 


class TitlesView: 
    """ Manage the widgets in an historic container """
    def __init__(self, border):
        self.border = border
        pass


    def build_title_container(self):
        st.container(border=self.border)

titles_container = TitlesView(True)
titles_container.build_title_container()

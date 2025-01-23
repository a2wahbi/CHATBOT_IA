import streamlit as st 


class HistoricView: 
    """ Manage the widgets in an historic container """
    def __init__(self , border , height ):
        self.border = border
        self.height = height
        pass


    def build_Historic_Container(self):
        st.container(border=self.border , height= self.height)
        st.write("test")


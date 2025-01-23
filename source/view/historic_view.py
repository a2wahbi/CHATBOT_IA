import streamlit as st 


class HistoricView: 
    """ Manage the widgets in an historic container """
    def __init__(self , border , height):
        self.border = border
        self.height = height
        pass


    def buildHistoricContainer(self):
        st.container(border=self.border , height= self.height)

historic_container = HistoricView(True , 470)
historic_container.buildHistoricContainer()

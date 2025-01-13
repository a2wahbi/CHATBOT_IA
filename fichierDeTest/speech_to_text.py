import streamlit as st

class AudioInput:
    def __init__(self):
        self._user_input_audio = ""
    
    @property
    def userInputAudio(self):
        return self._user_input_audio
    
    @userInputAudio.setter
    def userInputAudio(self , new_user_audio):
        self._user_input_audio = new_user_audio
        self.on_change(new_user_audio)

    def on_change(self , new_user_audio):
        st.write("enter there")
        st.write(new_user_audio) 

import streamlit as st


form = st.form("my_form")
form.slider("Inside the form")
st.slider("Outside the form")

# Now add a submit button to the form:
submitted = form.form_submit_button("Submit")
if submitted:
    st.write("submiteed ")
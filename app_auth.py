import streamlit as st

def set_auth():
    profile = {}
    with st.form('login form'):
        st.write('Mohon masukkan data pada kolom yang disediakan')
        username = st.text_input('USERNAME')
        password = st.text_input('PASSWORD', type='password')
        email = st.text_input('EMAIL')
        profile['username'] = username
        profile['password'] = password
        profile['email'] = email
        submit = st.form_submit_button('SUBMIT')
    
    return profile

import streamlit as st
import json
import os
from deep_translator import GoogleTranslator
import speech_recognition as sr
from gtts import gTTS
import streamlit.components.v1 as components
from io import BytesIO
import base64
from langdetect import detect  # Import the language detection library

# --------------------- Helpers ---------------------

def save_user(user_data):
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            users = json.load(file)
    else:
        users = {}
    users[user_data["username"]] = user_data
    with open("users.json", "w") as file:
        json.dump(users, file)

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

def validate_signup(name, email, username, password, confirm_password):
    errors = []
    if not name or not email or not username or not password or not confirm_password:
        errors.append("All fields are required.")
    if "@" not in email:
        errors.append("Invalid email format.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if username in load_users():
        errors.append("Username already exists.")
    return errors

def validate_login(username, password):
    users = load_users()
    if username in users and users[username]["password"] == password:
        return []
    return ["Invalid username or password."]

def speak(text, lang):
    tts = gTTS(text=text, lang=lang)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio = mp3_fp.read()
    b64 = base64.b64encode(audio).decode()
    return f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak Now!")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            detected_lang = detect(text)  # Detect the language of the spoken text
            st.session_state.detected_lang = detected_lang  # Store detected language in session state
            return text
        except:
            return "Sorry, could not recognize speech."

# --------------------- Pages ---------------------

def signup_page():
    st.title("Sign Up")
    name = st.text_input("Name")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        errors = validate_signup(name, email, username, password, confirm_password)
        if errors:
            for error in errors:
                st.error(error)
        else:
            save_user({"name": name, "email": email, "username": username, "password": password})
            st.success("Account created successfully! Please Login.")
            st.session_state.page = "login"

    # Link to login page
    if st.button("Already have an account? Login here"):
        st.session_state.page = "login"

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        errors = validate_login(username, password)
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.success("Login successful!")
            st.session_state.user = username
            st.session_state.page = "home"

    # Link to signup page
    if st.button("Don't have an account? Sign up here"):
        st.session_state.page = "signup"

def home_page():
    st.title(f"Welcome {st.session_state.user} to Language Translator!")
    st.write("👉 **First select the source language, then speak or type, select the target language, and finally click 'Translate'.**")

    st.subheader("Select Input Method")

    # Initialize session state for input storage
    if 'text_input' not in st.session_state:
        st.session_state.text_input = ""
    if 'detected_lang' not in st.session_state:
        st.session_state.detected_lang = None

    # Expanded list of languages including Indian languages
    language_options = {
        "English": "en",
        "Hindi (हिन्दी)": "hi",
        "Marathi (मराठी)": "mr",
        "Tamil (தமிழ்)": "ta",
        "Telugu (తెలుగు)": "te",
        "Kannada (ಕನ್ನಡ)": "kn",
        "Gujarati (ગુજરાતી)": "gu",
        "Bengali (বাংলা)": "bn",
        "Punjabi (ਪੰਜਾਬੀ)": "pa",
        "Urdu (اردو)": "ur",
        "French (Français)": "fr",
        "Spanish (Español)": "es",
        "German (Deutsch)": "de",
        "Russian (Русский)": "ru",
        "Japanese (日本語)": "ja",
        "Chinese (中文)": "zh-CN",
    }

    # Select source language
    source_lang = st.selectbox("Select Source Language (Language you will speak in)", options=list(language_options.keys()), key="source_lang_selector")

    # Option to choose between Speak or Type
    input_method = st.radio("Choose input method:", ("Type", "Speak"), horizontal=True)

    if input_method == "Type":
        st.session_state.text_input = st.text_input("Enter text to translate", value=st.session_state.text_input)
    elif input_method == "Speak":
        if st.button("Speak Now"):
            spoken_text = listen()
            st.session_state.text_input = spoken_text
        st.write("You said:", st.session_state.text_input)
        if st.session_state.detected_lang:
            st.write(f"Detected Language: {st.session_state.detected_lang}")

    # Select target language
    target_lang = st.selectbox("Select Target Language (Language to translate into)", options=list(language_options.keys()), key="target_lang_selector")

    # Translation and audio output
    if st.button("Translate"):
        if st.session_state.text_input.strip() == "" or st.session_state.text_input == "Sorry, could not recognize speech.":
            st.error("❗ Please provide valid input by speaking or typing.")
        else:
            source_lang_code = language_options[source_lang]
            target_lang_code = language_options[target_lang]
            result = GoogleTranslator(source=source_lang_code, target=target_lang_code).translate(st.session_state.text_input)
            st.success("Translation Successful!")
            st.write("**Translated Text:**", result)
            st.markdown("### 🔊 Listen to the Translation")
            components.html(speak(result, target_lang_code), height=80)

# --------------------- Main ---------------------

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'signup'
    if st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'home':
        home_page()

if __name__ == "__main__":
    main()
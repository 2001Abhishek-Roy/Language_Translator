import mysql.connector
from mysql.connector import Error
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import streamlit.components.v1 as components
from io import BytesIO
import base64
import requests


# Connect to MySQL Database
def create_connection():
    try:
        # Update the connection parameters with your MySQL details
        connection = mysql.connector.connect(
            host='localhost',
            user='root',           # Your MySQL username
            password='abhishek',  # Your MySQL password
            database='languagetranslator', # The database name
            port=3306
        )
        if connection.is_connected():
            print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

# Create tables if not exist
def create_tables():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                username VARCHAR(255) UNIQUE,
                password VARCHAR(255)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                code VARCHAR(10)
            );
        """)
        connection.commit()
        connection.close()

# Save user details into MySQL database
def save_user(user_data):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, username, password)
            VALUES (%s, %s, %s, %s);
        """, (user_data['name'], user_data['email'], user_data['username'], user_data['password']))
        connection.commit()
        connection.close()

# Load users from MySQL database
def load_users():
    connection = create_connection()
    users = {}
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        for row in rows:
            users[row['username']] = row
        connection.close()
    return users

# Validate sign-up details (e.g., check if username already exists)
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

# Validate login details
def validate_login(username, password):
    users = load_users()
    print("Users:", users)
    if username in users and users[username]["password"] == password:
        return []
    return ["Invalid username or password."]

# Save language to MySQL database
def save_language(language, code):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO languages (name, code) 
            VALUES (%s, %s);
        """, (language, code))
        connection.commit()
        connection.close()

def remove_language(language, code):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM languages WHERE name=%s and code=%s;
        """, (language, code))
        connection.commit()
        connection.close()

# Load all languages from MySQL database
def load_languages():
    connection = create_connection()
    languages = {}
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM languages")
        rows = cursor.fetchall()
        for row in rows:
            languages[row['name']] = row['code']
        connection.close()
    return languages

# --------------------- Speech to Text Functions ---------------------
def speak(text, lang):
    tts = gTTS(text=text, lang=lang)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio = mp3_fp.read()
    b64 = base64.b64encode(audio).decode()
    return f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

def listen(language_code):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak Now!")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio, language=language_code)
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


    language_options = load_languages()  # Get languages from the MySQL database

    print("language_options", language_options)
    # Select source language
    source_lang = st.selectbox("Select Source Language", options=list(language_options.keys()))

    # Input method (Type or Speak)
    input_method = st.radio("Choose input method:", ("Type", "Speak"))

    if input_method == "Type":
        st.session_state.text_input = st.text_input("Enter text to translate", value=st.session_state.text_input)
    elif input_method == "Speak":
        if st.button("Speak Now"):
            language_code = language_options[source_lang]
            spoken_text = listen(language_code)
            st.session_state.text_input = spoken_text
        st.write("You said:", st.session_state.text_input)

    # Select target language
    target_lang = st.selectbox("Select Target Language", options=list(language_options.keys()))

    # Translation and audio output
    if st.button("Translate"):
        if st.session_state.text_input.strip() == "":
            st.error("❗ Please provide valid input by speaking or typing.")
        else:
            source_lang_code = language_options[source_lang]
            target_lang_code = language_options[target_lang]

            result = translate_text_with_custom_session(st.session_state.text_input, source_lang_code, target_lang_code)
            # result = GoogleTranslator(source=source_lang_code, target=target_lang_code).translate(st.session_state.text_input)
            st.success("Translation Successful!")
            st.write("**Translated Text:**", result)
            st.markdown("### 🔊 Listen to the Translation")
            components.html(speak(result, target_lang_code), height=80)

def translate_text_with_custom_session(text, source_lang, target_lang):
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={text}"

    # Create a session and disable SSL verification
    session = requests.Session()
    session.verify = False  # Disable SSL verification

    try:
        response = session.get(url)
        response.raise_for_status()
        translation = response.json()[0][0][0]  # Extract translation from the response
        return translation
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'signup'
    if st.session_state.page == 'signup':
        signup_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'home':
        home_page()

def init_language():
    #Expanded list of languages including Indian languages
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

    for lang, code in language_options.items():
        try:
            save_language(lang,code)
        #   remove_language(lang, code)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    create_tables()  # Create tables if they don't exist
    init_language()

    main()

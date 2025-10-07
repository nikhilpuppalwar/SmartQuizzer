import streamlit as st
import sqlite3
import time
import random
import pandas as pd
import json # <-- ADDED: Needed for parsing the LLM's JSON string output
from llm_generator import generate_questions

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Quizzer",
    page_icon="🧠",
    layout="wide"
)

# ---------------- DATABASE FUNCTIONS ----------------
def init_db():
    """Initializes the SQLite database with necessary tables."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            topic TEXT,
            score INTEGER,
            total_questions INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, email, password):
    """Adds a new user to the database."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    conn.commit()
    conn.close()

def validate_user(username, password):
    """Validates user credentials."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE (username=? OR email=?) AND password=?", (username, username, password))
    result = c.fetchone()
    conn.close()
    return result is not None

def reset_password(username_or_email, new_password):
    """Resets the user's password if username/email exists."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? OR email=?", (username_or_email, username_or_email))
    result = c.fetchone()
    if result:
        c.execute("UPDATE users SET password=? WHERE username=? OR email=?", (new_password, username_or_email, username_or_email))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def save_quiz_performance(username, topic, score, total_questions):
    """Saves quiz results to the performance table."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("INSERT INTO performance (username, topic, score, total_questions) VALUES (?, ?, ?, ?)",
              (username, topic, score, total_questions))
    conn.commit()
    conn.close()

def get_user_performance(username):
    """Retrieves all performance records for a given user."""
    conn = sqlite3.connect("quiz_app.db")
    c = conn.cursor()
    c.execute("SELECT topic, score, total_questions, timestamp FROM performance WHERE username=? ORDER BY timestamp DESC", (username,))
    results = c.fetchall()
    conn.close()
    return results

# ---------------- APP PAGES ----------------
def login_page():
    """Renders the login page."""
    st.title("🔑 User Login")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            # Ensure we default to username if session state is not yet set
            username_or_email = st.text_input("Username or Email", placeholder="johndoe")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Log In", use_container_width=True)

        if login_button:
            if validate_user(username_or_email, password):
                st.success("✅ Login successful! Redirecting...")
                time.sleep(1)
                st.session_state['logged_in'] = True
                # Use the provided input for username, as the DB validation uses both
                st.session_state['username'] = username_or_email 
                st.session_state['page'] = 'Home'
                st.rerun()
            else:
                st.error("❌ Invalid username, email, or password.")

    st.markdown("---")
    if st.button("Forgot Password?", use_container_width=True):
        st.session_state['page'] = 'ForgotPassword'
        st.rerun()

def signup_page():
    """Renders the user registration page."""
    st.title("📝 Create a New Account")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username", placeholder="johndoe")
            new_email = st.text_input("Enter your Email", placeholder="your@email.com")
            new_password = st.text_input("Create a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_button = st.form_submit_button("Sign Up", use_container_width=True)

        if signup_button:
            if not new_username or not new_email or not new_password or not confirm_password:
                st.error("⚠️ Please fill out all fields.")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords do not match.")
            else:
                try:
                    add_user(new_username, new_email, new_password)
                    st.success("✅ Registration successful! You can now log in.")
                    time.sleep(1)
                    st.session_state['page'] = 'Login'
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ Username or email already exists. Please choose a different one.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

def forgot_password_page():
    """Renders the password reset page."""
    st.title("🔐 Forgot Password")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("forgot_password_form"):
            username_or_email = st.text_input("Enter your Username or Email", placeholder="johndoe or your@email.com")
            new_password = st.text_input("Enter New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            reset_button = st.form_submit_button("Reset Password", use_container_width=True)

        if reset_button:
            if not username_or_email or not new_password or not confirm_password:
                st.error("⚠️ Please fill out all fields.")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords do not match.")
            else:
                success = reset_password(username_or_email, new_password)
                if success:
                    st.success("✅ Password reset successful! You can now log in with your new password.")
                    time.sleep(1.5)
                    st.session_state['page'] = 'Login'
                    st.rerun()
                else:
                    st.error("❌ No user found with that username or email.")

    if st.button("⬅ Back to Login", use_container_width=True):
        st.session_state['page'] = 'Login'
        st.rerun()

def home_page():
    """Displays the main menu page."""
    st.title("🧠 Welcome to Smart Quizzer!")
    st.markdown(
        f"<h3 style='text-align: center;'>Hello, {st.session_state.get('username', 'Guest')} 👋</h3>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3 style='text-align: center;'>📘 Take a Quiz</h3>", unsafe_allow_html=True)
        if st.button("🚀 Start Quiz", key="btn_quiz", use_container_width=True):
            st.session_state['page'] = 'QuizSetup'
            st.rerun()

    with col2:
        st.markdown("<h3 style='text-align: center;'>📊 View Performance</h3>", unsafe_allow_html=True)
        if st.button("📈 View Performance", key="btn_performance", use_container_width=True):
            st.session_state['page'] = 'Performance'
            st.rerun()

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

def quiz_setup_page():
    """Quiz setup page."""
    st.header("🎯 Get Ready to Quiz!")

    if st.button("⬅ Back to Home", key="back_to_home_btn"):
        st.session_state['page'] = 'Home'
        st.rerun()

    st.markdown("---")

    with st.form("quiz_setup_form"):
        st.text_input("Enter your name", value=st.session_state.get('username', ''), disabled=True)
        topic = st.text_input("📘 Topic", placeholder="e.g. Triangles, Photosynthesis, Computer Networks")
        
        col1, col2 = st.columns(2)
        with col1:
            skill_level = st.selectbox("🎯 Skill Level", ["Beginner", "Intermediate", "Advanced"])
        with col2:
            class_level = st.selectbox(
                "🏫 Class (Optional)",
                ["None", "1st", "2nd", "3rd", "4th", "5th",
                 "6th", "7th", "8th", "9th", "10th",
                 "11th", "12th", "Undergraduate", "Post Graduation"]
            )
            if class_level == "None":
                class_level = None

        num_questions = st.slider("🧾 Number of Questions", 1, 20, 5)
        
        start_quiz_button = st.form_submit_button("✨ Generate and Start Quiz", use_container_width=True)

    if start_quiz_button:
        if not topic.strip():
            st.error("⚠️ Please enter a topic.")
        else:
            with st.spinner("🤖 Generating your quiz... Please wait ⏳"):
                try:
                    # 1. Call the LLM generator, which returns a raw JSON string
                    questions_json_str = generate_questions(
                        st.session_state.get('username', 'Guest'), 
                        topic, 
                        skill_level, 
                        num_questions, 
                        class_level
                    )
                    
                    if questions_json_str:
                        # 2. Parse the JSON string into a Python list of dictionaries (THE FIX!)
                        questions = json.loads(questions_json_str)
                        
                        if isinstance(questions, list) and questions:
                            st.session_state['quiz_topic'] = topic
                            st.session_state['quiz_questions'] = questions
                            st.session_state['current_question_idx'] = 0
                            st.session_state['score'] = 0
                            st.session_state['page'] = 'Quiz'
                            st.rerun()
                        else:
                            st.error("❌ The generated quiz was empty or not in the expected format (a list of questions). Please try again with a clearer topic.")
                    else:
                        st.error("❌ Failed to generate questions (empty response from LLM). Please try again.")

                except json.JSONDecodeError:
                    st.error("❌ Error: Failed to parse the model's response. The response was not valid JSON. This sometimes happens with complex prompts. Please try a different topic or refresh.")
                except Exception as e:
                    # Catch other potential errors, like API key issues
                    st.error(f"❌ An unexpected error occurred while generating the quiz: {e}")

def quiz_page():
    """Quiz question display."""
    st.header(f"🧠 {st.session_state['quiz_topic']} Quiz")
    current_question_idx = st.session_state['current_question_idx']
    questions = st.session_state['quiz_questions']
    
    # Check if questions list is available and indexed correctly
    if not isinstance(questions, list) or current_question_idx >= len(questions):
         st.error("Quiz data is missing or corrupted. Returning to setup.")
         st.session_state['page'] = 'QuizSetup'
         st.rerun()
         return
         
    current_question_data = questions[current_question_idx]

    progress_value = (current_question_idx + 1) / len(questions)
    st.progress(progress_value, text=f"Question {current_question_idx + 1} of {len(questions)}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"**Question {current_question_idx + 1}:** {current_question_data['question']}")
        
        # Shuffle options to make the quiz more engaging
        options_key = f"options_{current_question_idx}"
        if options_key not in st.session_state:
            shuffled_options = current_question_data['options'].copy()
            random.shuffle(shuffled_options)
            st.session_state[options_key] = shuffled_options

        with st.form("quiz_form"):
            user_answer = st.radio(
                "Choose your answer:", 
                st.session_state[options_key], 
                index=None, 
                key=f"radio_{current_question_idx}" # Unique key for radio button
            )
            submit_button = st.form_submit_button("Submit Answer", use_container_width=True)

        if submit_button:
            if user_answer is None:
                st.warning("⚠️ Please select an answer.")
            else:
                correct_answer = current_question_data['answer']
                
                # Check for answer match
                if user_answer.strip().lower() == correct_answer.strip().lower():
                    st.session_state['score'] += 1
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. Correct answer: **{correct_answer}**")

                time.sleep(1.5)
                if current_question_idx + 1 < len(questions):
                    st.session_state['current_question_idx'] += 1
                    # Remove the unique options key for the next question to be shuffled again
                    del st.session_state[options_key]
                    st.rerun()
                else:
                    st.session_state['page'] = 'QuizResult'
                    st.rerun()

def quiz_result_page():
    """Shows quiz results."""
    st.title("🎉 Quiz Completed!")
    score = st.session_state.get('score', 0)
    total_questions = len(st.session_state.get('quiz_questions', []))
    topic = st.session_state.get('quiz_topic', 'Unknown Topic')
    
    # Calculate percentage safely
    if total_questions > 0:
        percentage = round((score / total_questions) * 100, 2)
    else:
        percentage = 0

    st.balloons()
    st.markdown(f"""
        <div style="text-align: center; background-color: #f0f2f6; padding: 20px; border-radius: 15px;">
            <h1 style="color: #6c5ce7;">Your Score: {score} / {total_questions}</h1>
            <h2>{percentage}% Correct!</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Save performance only if a username is available and there were questions
    if st.session_state.get('username') and total_questions > 0:
        save_quiz_performance(st.session_state['username'], topic, score, total_questions)
        st.success("Performance recorded successfully!")
    else:
        st.warning("Quiz performance not recorded (not logged in or no questions generated).")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Another Quiz", use_container_width=True):
            st.session_state['page'] = 'QuizSetup'
            st.rerun()
    with col2:
        if st.button("📈 View Your Performance", use_container_width=True):
            st.session_state['page'] = 'Performance'
            st.rerun()

def performance_page():
    """Displays performance history."""
    st.header("📊 Your Performance History")
    if st.button("⬅ Back to Home"):
        st.session_state['page'] = 'Home'
        st.rerun()

    records = get_user_performance(st.session_state.get('username'))
    if not records:
        st.info("No records found. Take a quiz to start tracking!")
    else:
        df = pd.DataFrame(records, columns=["Topic", "Score", "Total Questions", "Timestamp"])
        # Calculate percentage safely
        df['Percentage'] = (df['Score'] / df['Total Questions'] * 100).round(2).astype(str) + '%'
        
        st.dataframe(
            df.set_index('Timestamp'), 
            use_container_width=True,
            column_order=["Topic", "Score", "Total Questions", "Percentage"]
        )
        
        # Add a visual chart for quick review
        st.line_chart(df['Percentage'].str.replace('%', '').astype(float).reset_index(drop=True))
        
        st.markdown("---")
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False),
            file_name="quiz_performance.csv",
            mime="text/csv"
        )

# ---------------- MAIN LOGIC ----------------
init_db()

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None

if not st.session_state['logged_in']:
    st.sidebar.title("Smart Quizzer")
    st.sidebar.markdown("---")
    
    # Non-logged-in routes (Login/Signup/Forgot)
    if st.session_state['page'] == 'ForgotPassword':
        forgot_password_page()
    else:
        page_selection = st.sidebar.radio("Go to", ["Login", "Sign Up"], index=0 if st.session_state['page'] == 'Login' else 1)
        
         # Update the session state based on the radio button selection
        if page_selection == "Login":
            st.session_state['page'] = 'Login'
        elif page_selection == "Sign Up":
            st.session_state['page'] = 'SignUp'

        # Render the page based on the single, updated session state value
        if st.session_state['page'] == 'Login':
            login_page()
        elif st.session_state['page'] == 'SignUp':
            signup_page()

else:
    # Logged-in routes
    if st.session_state['page'] == 'Home':
        home_page()
    elif st.session_state['page'] == 'QuizSetup':
        quiz_setup_page()
    elif st.session_state['page'] == 'Quiz':
        quiz_page()
    elif st.session_state['page'] == 'QuizResult':
        quiz_result_page()
    elif st.session_state['page'] == 'Performance':
        performance_page()
    # Default to home if state is corrupted
    else:
        st.session_state['page'] = 'Home'
        st.rerun()

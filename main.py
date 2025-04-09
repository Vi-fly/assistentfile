import streamlit as st
from ui_components import (
    home_page,
    contacts_page,
    tasks_page,
    gantt_page,
    email_page,
    resource_bot_page,
    data_view_page,
    discussions_page,
    attendance_page 
)

# Page Configuration
st.set_page_config(
    page_title="Task Manager Pro",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1E88E5;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #1565C0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    /* Form elements */
    .stTextInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    
    .stSelectbox>div>div>select {
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    
    /* Cards */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Tables */
    .dataframe {
        border-radius: 5px;
        overflow: hidden;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #E8F5E9;
        border-radius: 5px;
        padding: 1rem;
    }
    
    /* Error messages */
    .stError {
        background-color: #FFEBEE;
        border-radius: 5px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'target_page' not in st.session_state:
    st.session_state.target_page = "🏠 Home"

# Navigation
st.sidebar.title("Navigation")
page_options = [
    "🏠 Home",
    "📝 New Contact",
    "✅ New Task",
    "📅 Gantt Chart",
    "📧 Send Email",
    "🤖 Resource Bot",
    "📊 View All Data",
    "💬 Discussions",
    "📌 Attendance"
]

# Page selection
if st.session_state.target_page != "🏠 Home":
    page = st.session_state.target_page
else:
    page = st.sidebar.radio("Go to", page_options)

# Page routing
if page == "🏠 Home":
    home_page()
elif page == "📝 New Contact":
    contacts_page()
elif page == "✅ New Task":
    tasks_page()
elif page == "📅 Gantt Chart":
    gantt_page()
elif page == "📧 Send Email":
    email_page()
elif page == "🤖 Resource Bot":
    resource_bot_page()
elif page == "📊 View All Data":
    data_view_page()
elif page == "💬 Discussions": 
    discussions_page()
elif page == "📌 Attendance": 
    attendance_page()

# Sidebar Examples Guide
with st.sidebar.expander("📚 Examples Guide", expanded=False):
    st.markdown("""
    ### Add Data Examples
    - "Add new contact: John, 5551234567, john@email.com, London"
    - "Create task: Project Setup, Initialize repo, 2024-12-31, 5551234567"
    
    ### View Data Examples
    - "Show contacts from Delhi"
    - "List ongoing tasks for John"
    - "Display completed tasks"
    
    ### Update Data Examples
    - "Change John's email to new@email.com"
    - "Mark task 5 as completed"
    - "Update task 3's due date to tomorrow"
    """)

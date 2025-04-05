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

# Set page config for dark theme
st.set_page_config(
    page_title="Task Manager Pro",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        padding: 2rem 1rem;
        border-right: 1px solid #333333;
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        background-color: transparent;
    }
    
    /* App Logo */
    .app-logo {
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #333333;
    }
    
    .app-logo h2 {
        color: #4A90E2;
        font-size: 1.8rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .app-logo p {
        color: #AAAAAA;
        font-size: 0.9rem;
        margin-bottom: 0;
    }
    
    /* Navigation Links */
    .stButton > button {
        background-color: transparent;
        color: #CCCCCC;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        text-align: left;
        font-weight: 500;
        width: 100%;
        box-shadow: none;
    }
    
    .stButton > button:hover {
        background-color: rgba(74, 144, 226, 0.2);
        color: #4A90E2;
        transform: translateX(5px);
    }
    
    .stButton > button:focus {
        box-shadow: none;
        border: none;
    }
    
    /* Examples Guide Styling */
    .examples-guide {
        background-color: #252525;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 2rem;
        border: 1px solid #333333;
    }
    
    .examples-guide h3 {
        color: #4A90E2;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
    }
    
    .examples-guide h3:before {
        content: "💡";
        margin-right: 8px;
    }
    
    .examples-guide .section {
        margin-bottom: 1.2rem;
    }
    
    .examples-guide .section-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #CCCCCC;
    }
    
    .examples-guide code {
        background-color: #333333;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.85em;
        color: #4A90E2;
        display: block;
        margin: 0.3rem 0;
    }
    
    /* Footer */
    .sidebar-footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #333333;
        font-size: 0.8rem;
        color: #AAAAAA;
    }
    
    /* Active navigation item */
    .stButton > button[kind="primary"] {
        background-color: #4A90E2;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #357ABD;
        color: white;
    }
    
    /* Main content area */
    .main .block-container {
        background-color: #0E1117;
        padding-top: 2rem;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #4A90E2;
    }
    
    /* Text inputs */
    .stTextInput > div > div > input {
        background-color: #252525;
        color: #FAFAFA;
        border: 1px solid #333333;
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        background-color: #252525;
        color: #FAFAFA;
        border: 1px solid #333333;
    }
    
    /* Select boxes */
    .stSelectbox > div > div > select {
        background-color: #252525;
        color: #FAFAFA;
        border: 1px solid #333333;
    }
    
    /* Date inputs */
    .stDateInput > div > div > input {
        background-color: #252525;
        color: #FAFAFA;
        border: 1px solid #333333;
    }
    
    /* Time inputs */
    .stTimeInput > div > div > input {
        background-color: #252525;
        color: #FAFAFA;
        border: 1px solid #333333;
    }
    
    /* Sliders */
    .stSlider > div > div > div {
        background-color: #252525;
    }
    
    /* Tables */
    .stDataFrame {
        background-color: #252525;
        border: 1px solid #333333;
    }
    
    /* Cards */
    .stCard {
        background-color: #252525;
        border: 1px solid #333333;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: #252525;
        border: 1px solid #333333;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #1E4620;
        color: #A8E6A9;
    }
    
    /* Error messages */
    .stError {
        background-color: #4A1E1E;
        color: #E6A8A8;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #1E3A4A;
        color: #A8D1E6;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #4A3E1E;
        color: #E6D1A8;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'target_page' not in st.session_state:
    st.session_state.target_page = "🏠 Home"

# Sidebar Navigation
st.sidebar.markdown("""
    <div class='app-logo'>
        <h2>Task Manager Pro</h2>
        <p>Your Project Management Hub</p>
    </div>
""", unsafe_allow_html=True)

# Navigation options with icons and descriptions
page_options = [
    {
        "icon": "🏠",
        "title": "Home",
        "description": "Dashboard Overview"
    },
    {
        "icon": "📝",
        "title": "New Contact",
        "description": "Add Team Members"
    },
    {
        "icon": "✅",
        "title": "New Task",
        "description": "Create Tasks"
    },
    {
        "icon": "📅",
        "title": "Gantt Chart",
        "description": "Project Timeline"
    },
    {
        "icon": "📧",
        "title": "Send Email",
        "description": "Team Communications"
    },
    {
        "icon": "🤖",
        "title": "Resource Bot",
        "description": "AI Assistant"
    },
    {
        "icon": "📊",
        "title": "View All Data",
        "description": "Analytics Dashboard"
    },
    {
        "icon": "💬",
        "title": "Discussions",
        "description": "Team Collaboration"
    },
    {
        "icon": "📌",
        "title": "Attendance",
        "description": "Team Tracking"
    }
]

# Create navigation items manually instead of using radio
st.sidebar.markdown("### Navigation")
for option in page_options:
    nav_item = f"{option['icon']} {option['title']}"
    is_active = st.session_state.target_page == nav_item
    if st.sidebar.button(
        f"{option['icon']} {option['title']}",
        key=f"nav_{option['title'].lower().replace(' ', '_')}",
        use_container_width=True,
        type="primary" if is_active else "secondary"
    ):
        st.session_state.target_page = nav_item
        st.rerun()

# Examples Guide with enhanced styling
st.sidebar.markdown("""
    <div class='examples-guide'>
        <h3>Quick Guide</h3>
        
        <div class='section'>
            <div class='section-title'>Add Data:</div>
            <code>Add new contact: John, 5551234567, john@email.com, London</code>
            <code>Create task: Project Setup, Initialize repo, 2024-12-31</code>
        </div>
        
        <div class='section'>
            <div class='section-title'>View Data:</div>
            <code>Show contacts from Delhi</code>
            <code>List ongoing tasks for John</code>
        </div>
        
        <div class='section'>
            <div class='section-title'>Update Data:</div>
            <code>Change John's email to new@email.com</code>
            <code>Mark task 5 as completed</code>
        </div>
    </div>
    
    <div class='sidebar-footer'>
        © 2024 Task Manager Pro
    </div>
""", unsafe_allow_html=True)

# Page routing
page = st.session_state.target_page
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

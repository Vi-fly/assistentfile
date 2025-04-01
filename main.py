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
    "📌 Attendance"# ✅ New Page
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
st.sidebar.markdown("### Examples Guide")
st.sidebar.markdown("""
**Add Data Examples:**
- "Add new contact: John, 5551234567, john@email.com, London"
- "Create task: Project Setup, Initialize repo, 2024-12-31, 5551234567"

**View Data Examples:**
- "Show contacts from Delhi"
- "List ongoing tasks for John"
- "Display completed tasks"

**Update Data Examples:**
- "Change John's email to new@email.com"
- "Mark task 5 as completed"
- "Update task 3's due date to tomorrow"
""")

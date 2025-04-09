import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os
import json
import tempfile
import time
import openai
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
from langchain_groq import ChatGroq
from bson.son import SON
from pymongo import MongoClient
from bson.objectid import ObjectId
import plotly.express as px

from discussions import (
    get_all_posts, 
    add_post, 
    add_like, 
    add_comment,
    delete_post
)
from db_handler import (
    get_db_connection,
    execute_query,
    get_contacts,
    get_total_tasks,
    get_overdue_tasks
)
from ai_helper import (
    generate_task_details,
    generate_sql_query,
    classify_action
)
from email_handler import send_task_email
from task_utils import calculate_initial_date, create_gantt_chart

# Constants
CHAT_HISTORY_DIR = "chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

def home_page():
    st.header("💬 Database Chat Assistant")

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Main chat logic
    if prompt := st.chat_input("What would you like to do?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Check if it's a task creation command
        if any(keyword in prompt.lower() for keyword in ["add task", "create task", "new task"]):
            # Parse parameters and redirect to task page
            params = generate_task_details(prompt)
            if params:
                st.session_state.prefill_task = {
                    'title': params.get('title', ''),
                    'description': params.get('description', ''),
                    'category': params.get('category', 'Work'),
                    'priority': params.get('priority', 'Medium'),
                    'deadline': params.get('deadline', ''),
                    'assigned_to': params.get('assigned_to', ''),
                    'status': params.get('status', 'Not Started'),
                    'estimated_time': params.get('estimated_time', ''),
                    'required_resources': params.get('required_resources', ''),
                    'dependencies': params.get('dependencies', ''),
                    'instructions': params.get('instructions', ''),
                    'review_process': params.get('review_process', ''),
                    'performance_metrics': params.get('performance_metrics', ''),
                    'notes': params.get('notes', '')
                }
                st.session_state.target_page = "✅ New Task"
                st.rerun()
            else:
                st.error("Could not parse task details from your request")
        else:
            # Existing classification and SQL handling
            action_type = classify_action(prompt)
            sql_query = generate_sql_query(prompt, action_type)
            
            if sql_query:
                # Execute query
                columns, result = execute_query(sql_query)

                # Format response
                if action_type == "view" and columns:
                    df = pd.DataFrame(result, columns=columns)
                    response = f"🔍 Found {len(result)} results:\n\n{df.to_markdown(index=False)}"
                elif action_type in ["add", "update"]:
                    response = f"✅ Successfully {'added' if action_type == 'add' else 'updated'} {result} record(s)"
                else:
                    response = "❌ No results found or invalid query"

                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

def contacts_page():
    st.header("📝 Create New Contact")
    
    # Create a card-like container
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        with st.form("contact_form", clear_on_submit=True):
            # Use columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Personal Information")
                name = st.text_input("👤 Full Name*", help="Required field")
                phone = st.text_input("📱 Phone Number*", max_chars=10, help="10 digits without country code")
                skills = st.text_input("🔧 Skills", help="e.g., Python, Project Management")
            
            with col2:
                st.markdown("### Contact Details")
                email = st.text_input("📧 Email Address*", help="Required field")
                address = st.text_input("📍 Physical Address", help="Optional field")
            
            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Submit button with icon
            submitted = st.form_submit_button("💾 Save Contact", use_container_width=True)
            
            if submitted:
                if not all([name, phone, email]):
                    st.error("⚠️ Please fill in all required fields (*)")
                elif not phone.isdigit() or len(phone) != 10:
                    st.error("⚠️ Phone number must be exactly 10 digits")
                else:
                    try:
                        sql = """INSERT INTO CONTACTS (NAME, PHONE, EMAIL, ADDRESS, SKILLS) 
                                VALUES (%s, %s, %s, %s, %s)"""
                        params = (name.strip(), int(phone), email.strip(), address.strip(), skills.strip() or None)
                        _, affected = execute_query(sql, params)
                        if affected:
                            st.success("✅ Contact created successfully!")
                            st.balloons()
                        else:
                            st.error("❌ Error creating contact")
                    except Exception as e:
                        st.error(f"❌ Database error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a preview section
        with st.expander("👥 Recent Contacts", expanded=False):
            try:
                conn = get_db_connection()
                df = pd.read_sql("SELECT NAME, PHONE, EMAIL FROM CONTACTS ORDER BY ID DESC LIMIT 5", conn)
                st.dataframe(df, use_container_width=True)
                conn.close()
            except Exception as e:
                st.error(f"Error loading recent contacts: {str(e)}")

def tasks_page():
    st.header("✅ Create New Task")

    # Initialize prefill_task if not exists
    if 'prefill_task' not in st.session_state:
        st.session_state.prefill_task = {}

    # Get contacts for assignment
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT ID, NAME FROM CONTACTS ORDER BY NAME')
    contacts = cur.fetchall()
    contact_names = [name for _, name in contacts]
    contact_dict = {name: id for id, name in contacts}
    cur.close()
    conn.close()

    # Create main container
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        with st.form("task_form", clear_on_submit=True):
            # Basic Info Section
            st.markdown("### 📋 Basic Information")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                title = st.text_input("📝 Task Title*", 
                                    value=st.session_state.prefill_task.get('title', ''),
                                    help="Enter a clear, descriptive title")
                description = st.text_area("📄 Detailed Description", 
                                         value=st.session_state.prefill_task.get('description', ''),
                                         height=100,
                                         help="Provide detailed information about the task")
            
            with col2:
                deadline_input = st.session_state.prefill_task.get('deadline', '')
                default_date = datetime.today()

                if deadline_input:
                    try:
                        if 'tomorrow' in deadline_input.lower():
                            default_date += timedelta(days=1)
                        elif 'next week' in deadline_input.lower():
                            default_date += timedelta(weeks=1)
                        elif 'in 2 days' in deadline_input.lower():
                            default_date += timedelta(days=2)
                    except Exception:
                        pass

                st.markdown("#### ⏰ Deadline")
                deadline_date = st.date_input("Date*", 
                                            min_value=datetime.today(),
                                            value=default_date)
                deadline_time = st.time_input("Time*", datetime.now().time())
            
            # Task Details Section
            st.markdown("### 🎯 Task Details")
            cols = st.columns(3)
            
            with cols[0]:
                category_options = ["Work", "Personal", "Project", "Other"]
                category = st.selectbox("📑 Category", 
                                      category_options,
                                      index=category_options.index(
                                          st.session_state.prefill_task.get('category', 'Work')))
                priority = st.select_slider("⚡ Priority*", 
                                          options=["Low", "Medium", "High"],
                                          value=st.session_state.prefill_task.get('priority', 'Medium'))
                expected_outcome = st.text_input("🎯 Expected Outcome", 
                                               value=st.session_state.prefill_task.get('expected_outcome', ''),
                                               help="What should be achieved?")
            
            with cols[1]:
                assigned_to_index = 0
                if st.session_state.prefill_task.get('assigned_to'):
                    lower_names = [name.lower() for name in contact_names]
                    try:
                        assigned_to_index = lower_names.index(
                            st.session_state.prefill_task['assigned_to'].lower())
                    except ValueError:
                        assigned_to_index = 0
                
                assigned_to = st.selectbox("👤 Assign To*", 
                                         options=contact_names,
                                         index=assigned_to_index)
                
                status_options = ["Not Started", "In Progress", "On Hold", "Completed"]
                status_index = status_options.index(
                    st.session_state.prefill_task.get('status', 'Not Started'))
                status = st.selectbox("📊 Status*", 
                                    status_options, 
                                    index=status_index)
                
                support_index = 0
                if st.session_state.prefill_task.get('support_contact'):
                    try:
                        support_index = contact_names.index(
                            st.session_state.prefill_task['support_contact'])
                    except ValueError:
                        support_index = 0
                
                support_contact = st.selectbox("🤝 Support Contact", 
                                             options=contact_names,
                                             index=support_index)
            
            with cols[2]:
                estimated_time = st.text_input("⏱️ Estimated Time", 
                                             value=st.session_state.prefill_task.get('estimated_time', ''),
                                             help="e.g., 2 hours, 1 day")
                required_resources = st.text_input("🛠️ Required Resources",
                                                 value=st.session_state.prefill_task.get('required_resources', ''),
                                                 help="e.g., Laptop, Software")
            
            # Additional Information Section
            st.markdown("### 📌 Additional Information")
            col1, col2 = st.columns(2)
            
            with col1:
                dependencies = st.text_area("🔗 Dependencies", 
                                          value=st.session_state.prefill_task.get('dependencies', ''),
                                          help="What does this task depend on?")
                instructions = st.text_area("📝 Instructions", 
                                          value=st.session_state.prefill_task.get('instructions', ''),
                                          help="Step-by-step instructions")
            
            with col2:
                review_process = st.text_area("👀 Review Process", 
                                            value=st.session_state.prefill_task.get('review_process', ''),
                                            help="Steps for reviewing the task")
                performance_metrics = st.text_area("📊 Success Metrics",
                                                 value=st.session_state.prefill_task.get('performance_metrics', ''),
                                                 help="How will success be measured?")
            
            # Submit button
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("💾 Save Task", use_container_width=True)
            
            if submitted:
                if not all([title, priority, assigned_to, status, deadline_date]):
                    st.error("Please fill required fields (*)")
                else:
                    try:
                        deadline = datetime.combine(deadline_date, deadline_time).strftime("%Y-%m-%d %H:%M:%S")
                        sql = """INSERT INTO TASKS (
                            TITLE, DESCRIPTION, CATEGORY, PRIORITY, EXPECTED_OUTCOME,
                            DEADLINE, ASSIGNED_TO, DEPENDENCIES, REQUIRED_RESOURCES,
                            ESTIMATED_TIME, INSTRUCTIONS, REVIEW_PROCESS, PERFORMANCE_METRICS,
                            SUPPORT_CONTACT, NOTES, STATUS, STARTED_AT, COMPLETED_AT
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                        
                        params = (
                            title.strip(),
                            description.strip(),
                            category,
                            priority,
                            expected_outcome.strip(),
                            deadline,
                            contact_dict[assigned_to],
                            dependencies.strip(),
                            required_resources.strip(),
                            estimated_time.strip(),
                            instructions.strip(),
                            review_process.strip(),
                            performance_metrics.strip(),
                            contact_dict.get(support_contact, None),
                            None,  # NOTES
                            status,
                            None,  # STARTED_AT
                            None   # COMPLETED_AT
                        )
                        
                        _, affected = execute_query(sql, params)
                        if affected:
                            st.session_state.task_status = f"✅ Task '{title.strip()}' created successfully!"
                            st.session_state.target_page = "🏠 Home"
                            if 'prefill_task' in st.session_state:
                                del st.session_state.prefill_task
                            st.rerun()
                        else:
                            st.error("Error creating task")
                    except Exception as e:
                        st.error(f"Database error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a preview section
        with st.expander("📋 Recent Tasks", expanded=False):
            try:
                conn = get_db_connection()
                df = pd.read_sql("""
                    SELECT T.TITLE, T.STATUS, T.PRIORITY, C.NAME AS ASSIGNED_TO 
                    FROM TASKS T 
                    LEFT JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID 
                    ORDER BY T.ID DESC LIMIT 5
                """, conn)
                st.dataframe(df, use_container_width=True)
                conn.close()
            except Exception as e:
                st.error(f"Error loading recent tasks: {str(e)}")

def gantt_page():
    st.header("📅 Gantt Chart")
    
    # Create main container
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.multiselect(
                "📊 Filter by Status",
                options=["Not Started", "In Progress", "On Hold", "Completed"],
                default=["Not Started", "In Progress"]
            )
        
        with col2:
            priority_filter = st.multiselect(
                "⚡ Filter by Priority",
                options=["Low", "Medium", "High"],
                default=["Low", "Medium", "High"]
            )
        
        with col3:
            category_filter = st.multiselect(
                "📑 Filter by Category",
                options=["Work", "Personal", "Project", "Other"],
                default=["Work", "Personal", "Project", "Other"]
            )
        
        # Get Gantt chart data
        fig, df = create_gantt_chart()
        
        if fig is not None and df is not None:
            # Apply filters
            if status_filter:
                df = df[df["STATUS"].isin(status_filter)]
            if priority_filter:
                df = df[df["PRIORITY"].isin(priority_filter)]
            if category_filter:
                df = df[df["CATEGORY"].isin(category_filter)]
            
            # Update figure with filtered data
            fig = px.timeline(
                df,
                x_start="START_DATE",
                x_end="DEADLINE",
                y="TITLE",
                color="PRIORITY",
                color_discrete_map={
                    "High": "#FF4B4B",
                    "Medium": "#FFA500",
                    "Low": "#00CC96"
                },
                title="Task Schedule Overview",
                labels={"TITLE": "Task Name"},
                hover_data=["STATUS", "CATEGORY"]
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                xaxis_title="Timeline",
                yaxis_title="Tasks",
                showlegend=True,
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis={'categoryorder': 'total ascending'},
                font=dict(
                    family="Segoe UI",
                    size=12
                ),
                title_font=dict(
                    family="Segoe UI",
                    size=20
                )
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Add task summary
            st.markdown("### 📊 Task Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_tasks = len(df)
                st.metric("Total Tasks", total_tasks)
            
            with col2:
                completed_tasks = len(df[df["STATUS"] == "Completed"])
                st.metric("Completed", completed_tasks)
            
            with col3:
                in_progress = len(df[df["STATUS"] == "In Progress"])
                st.metric("In Progress", in_progress)
            
            with col4:
                overdue = len(df[df["DEADLINE"] < pd.Timestamp.now()])
                st.metric("Overdue", overdue, delta=f"-{overdue}")
            
            # Display task details
            with st.expander("📋 Task Details", expanded=False):
                st.dataframe(
                    df[["TITLE", "STATUS", "PRIORITY", "CATEGORY", "DEADLINE"]],
                    use_container_width=True
                )
        else:
            st.error("❌ Error loading Gantt chart data")
        
        st.markdown('</div>', unsafe_allow_html=True)

import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage  # ✅ Added required import
def email_page():
    st.header("📧 Send Email to Assigned Contacts")

    # Get all tasks and their assigned contacts
    try:
        conn = get_db_connection()
        tasks_df = pd.read_sql("""
            SELECT T.ID, T.TITLE, T.DESCRIPTION, C.NAME, C.EMAIL 
            FROM TASKS T 
            JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID
        """, conn)
        conn.close()
        
        # Debugging prints
        print("🔍 Retrieved Dataframe Columns:", tasks_df.columns.tolist())
        print("📊 Sample Data:\n", tasks_df.head())

        # Normalize column names (remove spaces, make uppercase)
        tasks_df.columns = tasks_df.columns.str.upper().str.strip()
    
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        print(f"❌ Error fetching data: {e}")  # Debugging
        tasks_df = pd.DataFrame()

    if tasks_df.empty:
        st.warning("No tasks with assigned contacts found.")
    else:
        try:
            # Ensure required columns exist
            required_columns = {"ID", "TITLE", "DESCRIPTION", "NAME", "EMAIL"}
            missing_columns = required_columns - set(tasks_df.columns)
            if missing_columns:
                raise KeyError(f"Missing columns: {missing_columns}")

            # Generate task options safely
            task_options = [
                f"{row['TITLE']} (Assigned to: {row['NAME']})" 
                for _, row in tasks_df.iterrows()
            ]

            # Debugging output
            print("✅ Task options generated successfully.")

        except KeyError as e:
            st.error(f"Column Error: {e}")
            print(f"❌ Column Error: {e}")  # Debugging
            return
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
            print(f"❌ Unexpected Error: {e}")  # Debugging
            return

        # Handle empty task options safely
        if not task_options:
            st.warning("No valid tasks available.")
            return

        selected_task = st.selectbox("Select a Task", task_options)

        if selected_task:
            # Extract task details
            selected_index = task_options.index(selected_task)
            try:
                task_id = tasks_df.iloc[selected_index]['ID']
                task_title = tasks_df.iloc[selected_index]['TITLE']
                task_description = tasks_df.iloc[selected_index]['DESCRIPTION']
                recipient_name = tasks_df.iloc[selected_index]['NAME']
                recipient_email = tasks_df.iloc[selected_index]['EMAIL']
            except Exception as e:
                st.error(f"Error extracting task details: {e}")
                print(f"❌ Error extracting task details: {e}")  # Debugging
                return

            st.subheader("Email Details", divider="rainbow")
            st.write(f"*Recipient:* {recipient_name} ({recipient_email})")
            st.write(f"*Task:* {task_title}")

            # Generate email content using LLM
            if st.button("\u2728 Generate Email Content"):
                with st.spinner("Generating email content..."):
                    try:
                        system_prompt = """You are an AI assistant that writes professional emails. 
                        Write a concise email to remind the recipient about their assigned task. 
                        Include the task title, description, and a polite reminder to complete it on time."""

                        messages = [
                            SystemMessage(content=system_prompt),
                            HumanMessage(content=f"Task: {task_title}\nDescription: {task_description}")
                        ]
                        
                        llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
                        response = llm.invoke(messages)
                        email_content = response.content.strip()
                        st.session_state.email_content = email_content
                    except Exception as e:
                        st.error(f"Error generating email content: {str(e)}")
                        print(f"❌ Error generating email content: {e}")  # Debugging

            # Display and edit email content
            if 'email_content' in st.session_state:
                email_content = st.text_area("Email Content", 
                                           value=st.session_state.email_content,
                                           height=200)

                # Send email
                if st.button("📤 Send Email"):

                    try:
                        send_task_email(
                            recipient_email=recipient_email,
                            subject=f"Reminder: {task_title}",
                            message=email_content
                        )
                        st.success(f"Email sent to {recipient_name} ({recipient_email})")
                        del st.session_state.email_content
                    except Exception as e:
                        st.error(f"Failed to send email: {str(e)}")
                        print(f"❌ Failed to send email: {e}")  # Debugging



def resource_bot_page():
    st.header("🤖 Resource Manager & Chat History")
    
    tab1, tab2 = st.tabs(["Chatbot", "Chat History"])
    
    with tab1:
        # Chatbot Section
        with st.container(border=True):
            st.subheader("Task Assistant", divider="rainbow")
            user_input = st.text_input("Enter a task (e.g., website development, marketing campaign):")
            
            if st.button("Get Suggestions", use_container_width=True):
                if user_input:
                    with st.spinner("Analyzing task and resources..."):
                        if "chat_history" not in st.session_state:
                            st.session_state.chat_history = []
                            
                        prompt = generate_prompt(user_input)
                        bot_response = query_groq(prompt)
                        
                        MAX_HISTORY = 3  
                        if len(st.session_state.chat_history) > MAX_HISTORY:
                            st.session_state.chat_history.pop(0)
                            
                        st.session_state.chat_history.append({"user": user_input, "bot": bot_response})
                        st.session_state.current_suggestion = bot_response
                else:
                    st.warning("Please enter a task description")
            
            if "current_suggestion" in st.session_state:
                with st.expander("Current Suggestion", expanded=True):
                    st.write(st.session_state.current_suggestion)
                    
                if st.button("Save to History", use_container_width=True):
                    if user_input and "current_suggestion" in st.session_state:
                        save_suggestion(user_input, st.session_state.current_suggestion)
                        st.rerun()
            
            # Show recent conversations
            if "chat_history" in st.session_state and st.session_state.chat_history:
                st.subheader("Recent Conversations", divider="gray")
                for chat in reversed(st.session_state.chat_history):
                    with st.expander(f"Task: {chat['user'][:50]}...", expanded=False):
                        st.text_area("You asked:", chat["user"], height=70, disabled=True)
                        st.text_area("Bot response:", chat["bot"], height=150, disabled=True)
    
    with tab2:
        # Chat History Section
        with st.container(border=True):
            st.subheader("Saved Suggestions", divider="rainbow")
            chat_files = list_saved_chats()
            
            if chat_files:
                selected_file = st.selectbox("Select saved suggestion:", chat_files)
                
                cols = st.columns([1, 4])
                with cols[0]:
                    if st.button("Load Selected", help="Load this suggestion into the assistant"):
                        try:
                            with open(os.path.join(CHAT_HISTORY_DIR, selected_file), "r", encoding="utf-8") as file:
                                content = file.read().strip()
                            st.session_state.current_suggestion = content
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading file: {e}")
                
                with cols[1]:
                    if selected_file:
                        try:
                            with open(os.path.join(CHAT_HISTORY_DIR, selected_file), "r", encoding="utf-8") as file:
                                content = file.read().strip()
                            st.text_area("Suggestion Content", value=content, height=200, key=f"view_{selected_file}")
                        except Exception as e:
                            st.error(f"Error reading file: {e}")
            else:
                st.info("No saved suggestions yet. Get some recommendations first!")

def data_view_page():
    st.header("📊 View All Database Records")
    
    try:
        conn = get_db_connection()
        
        # Contacts Table
        st.subheader("👥 Contacts", divider="rainbow")
        df_contacts = pd.read_sql("SELECT * FROM CONTACTS ORDER BY NAME", conn)
        if not df_contacts.empty:
            st.dataframe(
                df_contacts,
                column_config={
                    "PHONE": st.column_config.NumberColumn(format="%d")
                },
                use_container_width=True
            )
            st.download_button(
                label="📥 Export Contacts",
                data=df_contacts.to_csv(index=False),
                file_name="contacts.csv",
                mime="text/csv"
            )
        else:
            st.warning("No contacts found in database")

        # Tasks Table
        st.subheader("✅ Tasks", divider="rainbow")
        df_tasks = pd.read_sql("""SELECT 
            T.ID,
            T.TITLE,
            T.DESCRIPTION,
            T.CATEGORY,
            T.PRIORITY,
            T.STATUS,
            T.DEADLINE,
            C.NAME AS ASSIGNED_TO
            FROM TASKS T
            LEFT JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID
            ORDER BY DEADLINE""", conn)
        
        if not df_tasks.empty:
            st.dataframe(
                df_tasks,
                column_config={
                    "DEADLINE": st.column_config.DatetimeColumn(),
                    "PRIORITY": st.column_config.SelectboxColumn(options=["Low", "Medium", "High"])
                },
                use_container_width=True
            )
            st.download_button(
                label="📥 Export Tasks",
                data=df_tasks.to_csv(index=False),
                file_name="tasks.csv",
                mime="text/csv"
            )
        else:
            st.warning("No tasks found in database")

    except Exception as e:
        st.error(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

# Helper functions for resource bot
def save_suggestion(task, suggestion):
    """Save the AI suggestion to a text file."""
    filename = os.path.join(CHAT_HISTORY_DIR, f"{task.replace(' ', '_')}.txt")
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(suggestion.strip())
        st.success(f"Suggestion saved: {filename}")
    except Exception as e:
        st.error(f"Error saving suggestion: {e}")

def list_saved_chats():
    """List all saved chat history files."""
    try:
        return [f for f in os.listdir(CHAT_HISTORY_DIR) if f.endswith(".txt")]
    except Exception as e:
        st.error(f"Error loading chat history: {e}")
        return []

def query_groq(prompt):
    """Send a query to the Groq API and get the response."""
    client = openai.Client(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_prompt(task):
    """Generate a prompt to ask Groq for resource suggestions."""
    contacts = get_contacts()
    skills_dict = {name: skills for name, skills in contacts}
    prompt = f"For the task '{task}', suggest required resources like budget, tools, and storage. "
    prompt += "Also, suggest suitable employees based on these available skills: "
    prompt += ", ".join([f"{name} ({skills})" for name, skills in skills_dict.items()])
    prompt += " If employees with necessary skills are not available, ask to hire employees with necessary skills."
    return prompt

from discussions import get_all_posts, add_post, add_like, add_comment, delete_post
import streamlit as st

def discussions_page():
    """Render the Community Discussions Page."""
    st.title("💬 Community Discussions")

    # Button to show post creation form
    if "show_post_form" not in st.session_state:
        st.session_state.show_post_form = False

    with st.sidebar:  # Keep the post button and form always visible in the sidebar
        if st.button("📝 Share a Post"):
            st.session_state.show_post_form = True
            st.rerun()
        
        if st.session_state.show_post_form:
            with st.form("create_post"):
                username = st.text_input("👤 Your Name")
                content = st.text_area("📝 Say something...")
                image = st.file_uploader("📷 Upload Image", type=["png", "jpg"])
                video = st.file_uploader("🎥 Upload Video", type=["mp4"])
                
                col1, col2 = st.columns(2)
                submitted = col1.form_submit_button("📢 Post")
                canceled = col2.form_submit_button("❌ Cancel")
                
                if submitted:
                    if not username.strip() and not content.strip() and not image and not video:
                        st.warning("⚠ Please fill in at least one field before posting.")
                    else:
                        image_data = image.read() if image else None
                        video_data = video.read() if video else None
                        add_post(username, content, image_data, video_data)
                        st.success("Post shared!")
                        st.session_state.show_post_form = False
                        st.rerun()
                
                if canceled:
                    st.session_state.show_post_form = False
                    st.rerun()
        st.markdown("---")

    # ---- Display Posts ----
    posts = get_all_posts()
    for post in posts:
        st.subheader(f"{post['username']}")
        st.write(post['content'])

        if 'image' in post and post['image']:
            st.image(post['image'])
        if 'video' in post and post['video']:
            st.video(post['video'])

        # Likes
        if st.button(f"👍 Like ({post['likes']})", key=f"like_{post['_id']}"):
            add_like(post['_id'])
            st.rerun()

        # Comments
        comment = st.text_input("Add comment", key=f"comment_input_{post['_id']}")
        if st.button("💬 Comment", key=f"submit_comment_{post['_id']}"):
            add_comment(post['_id'], comment)
            st.rerun()

        # Show existing comments
        if post.get("comments"):
            st.markdown("*Comments:*")
            for c in post["comments"]:
                st.markdown(f"- {c}")

        # Delete Post
        if st.button("🗑 Delete Post", key=f"delete_{post['_id']}"):
            delete_post(post['_id'])
            st.success("Post deleted.")
            st.rerun()

        st.markdown("---")
        
def attendance_page():
    st.header("🚀 Performance Tracking Dashboard")
    
    # Add meta tag for redirection with delay
    st.markdown("""
    <meta http-equiv="refresh" content="0; url='https://docs.google.com/forms/d/e/1FAIpQLSc8kHkCHt-8Zxs3TJGknYFyfrW9B-zEd9yJTlTMLtATg8ZZhA/viewform?usp=dialog'">
    """, unsafe_allow_html=True)
    
    # Show loading message
    
    # Fallback link
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <h3>⏳ Redirecting to Attendance Form</h3>
        <p>If you're not redirected automatically, click below:</p>
        <a href="https://docs.google.com/forms/d/e/1FAIpQLSc8kHkCHt-8Zxs3TJGknYFyfrW9B-zEd9yJTlTMLtATg8ZZhA/viewform?usp=dialog" target="_blank">
            <button style="
                background: #FF4B4B;
                color: white;
                padding: 1em 2em;
                border: none;
                border-radius: 10px;
                font-size: 1.2rem;
                cursor: pointer;
                margin-top: 1rem;">
                🔥 Open Attendance Form
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)

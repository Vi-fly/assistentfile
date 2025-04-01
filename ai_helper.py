import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import streamlit as st

load_dotenv()

# Initialize ChatGroq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")

def generate_task_details(description: str) -> dict:
    """Generate detailed task parameters from description"""
    system_prompt = """Analyze the task description and generate detailed task parameters. Return STRICTLY ONLY VALID JSON with:
    {
        "title": "string",
        "description": "string",
        "category": "Work|Personal|Project|Other",
        "priority": "Low|Medium|High",
        "deadline": "natural language date",
        "assigned_to": "string",
        "status": "Not Started|In Progress|On Hold|Completed",
        "dependencies": "string",
        "required_resources": "string",
        "expected_outcome": "string",
        "review_process": "string",
        "performance_metrics": "string",
        "estimated_time": "string",
        "instructions": "string"
    }
    
    Example Input: "Develop login page with Auth0 by next week, assign to John"
    Example Output:
    {
        "title": "Develop Login Page",
        "description": "Implement secure authentication using Auth0",
        "category": "Work",
        "priority": "High",
        "deadline": "next week",
        "assigned_to": "John",
        "status": "Not Started",
        "dependencies": "Auth0 API access, design mockups",
        "required_resources": "React, Node.js, Auth0 SDK",
        "expected_outcome": "Secure user login system",
        "review_process": "1. Code review\\n2. Security audit",
        "performance_metrics": "Load time <2s, 100% test coverage",
        "estimated_time": "3 days",
        "instructions": "1. Create UI components\\n2. Integrate Auth0"
    }""" 
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=description)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_response = response.content.strip()
        
        # Enhanced cleaning process
        def clean_json_response(text):
            if text.startswith('n'):
                text = text[1:]
            text = text.replace('```json', '').replace('```', '')
            start_idx = text.find('{')
            if start_idx > 0:
                text = text[start_idx:]
            return text.strip()
        
        cleaned_response = clean_json_response(raw_response)
        
        # Debugging output
        st.write("Raw LLM Response:", raw_response)
        st.write("Cleaned Response:", cleaned_response)
        
        parsed = json.loads(cleaned_response)
        
        # Validate and default missing fields
        return {
            "title": parsed.get("title", "Unnamed Task"),
            "description": parsed.get("description", ""),
            "category": parsed.get("category", "Work"),
            "priority": parsed.get("priority", "Medium"),
            "deadline": parsed.get("deadline", ""),
            "assigned_to": parsed.get("assigned_to", ""),
            "status": parsed.get("status", "Not Started"),
            "dependencies": parsed.get("dependencies", ""),
            "required_resources": parsed.get("required_resources", ""),
            "expected_outcome": parsed.get("expected_outcome", ""),
            "review_process": parsed.get("review_process", ""),
            "performance_metrics": parsed.get("performance_metrics", ""),
            "estimated_time": parsed.get("estimated_time", "1 day"),
            "instructions": parsed.get("instructions", "")
        }
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format in response: {e}\nRaw LLM response: {raw_response}")
        return {}
    except Exception as e:
        st.error(f"Error parsing task parameters: {str(e)}")
        return {}

def generate_sql_query(prompt: str, action: str) -> str:
    """Generate SQL query based on selected action and user input"""
    system_prompts = {
        "add": (
    "You are an expert in generating SQL INSERT statements for a contacts database in PostgreSQL (Neon Database). "
    "The database has one table: CONTACTS.\n\n"
    "CONTACTS Table Structure:\n"
    "- ID (SERIAL PRIMARY KEY)\n"
    "- NAME (VARCHAR NOT NULL)\n"
    "- PHONE (BIGINT UNIQUE NOT NULL CHECK (LENGTH(PHONE::TEXT) = 10))\n"
    "- EMAIL (VARCHAR UNIQUE NOT NULL)\n"
    "- ADDRESS (TEXT)\n\n"
    "Rules for INSERT Statements:\n"
    "1. For CONTACTS: INSERT INTO CONTACTS (NAME, PHONE, EMAIL, ADDRESS) VALUES (...);\n"
    "2. Phone numbers must be 10-digit integers.\n"
    "3. Use single quotes for string values.\n"
    "4. Ensure queries are compatible with PostgreSQL.\n"
    "5. Return only the SQL query, no explanations.\n\n"
    "Examples:\n"
    "1. Add new contact: INSERT INTO CONTACTS (NAME, PHONE, EMAIL, ADDRESS) VALUES ('John Doe', 5551234567, 'john@email.com', '123 Main St');\n"
    "2. Add another contact: INSERT INTO CONTACTS (NAME, PHONE, EMAIL, ADDRESS) VALUES ('Jane Smith', 9876543210, 'jane@email.com', '456 Oak Ave');"
    ),
    "view": (
    "You are an expert in generating SQL SELECT queries with JOINs for a contacts and tasks database in PostgreSQL (Neon Database).\n\n"
    "Rules for SELECT Statements:\n"
    "1. Always use LEFT JOINs when showing tasks to include assignee names.\n"
    "2. Use ILIKE and Use LOWER() for case-insensitive comparisons and matching in WHERE clauses.\n"
    "3. Use proper table aliases (C for CONTACTS, T for TASKS).\n"
    "4. Return only the SQL query, no explanations.\n\n"
    "Examples:\n"
    "1. Show all tasks: SELECT T.ID, T.TITLE, T.DESCRIPTION, T.CATEGORY, T.PRIORITY, T.STATUS, C.NAME AS ASSIGNEE FROM TASKS T LEFT JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID;\n"
    "2. Find contacts from Delhi: SELECT * FROM CONTACTS WHERE ADDRESS ILIKE '%delhi%';\n"
    "3. Show ongoing tasks for John: SELECT T.ID, T.TITLE, T.DEADLINE FROM TASKS T JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID WHERE C.NAME ILIKE 'John Doe' AND T.STATUS = 'In Progress';\n"
    "4. Display task 1: SELECT T.* FROM TASKS T JOIN CONTACTS C ON T.ASSIGNED_TO = C.ID WHERE T.ID = 1;"
    "5. List completed tasks: SELECT T.ID, T.TITLE, T.STATUS FROM TASKS T WHERE T.STATUS = 'Completed';"
    "6. view Contact vivek choudhary: SELECT * FROM CONTACTS WHERE LOWER(NAME) = 'vivek choudhary';"
    ),
    "update": (
    "You are an expert in generating SQL UPDATE statements for a contacts and tasks database in PostgreSQL (Neon Database).\n\n"
    "Rules for UPDATE Statements:\n"
    "1. For contacts, use ID as the identifier in WHERE clause.\n"
    "2. For tasks, use ID as the identifier in WHERE clause.\n"
    "3. Use single quotes for string values.\n"
    "4. Ensure queries follow PostgreSQL syntax.\n"
    "5. Return only the SQL query, no explanations.\n\n"
    "Examples:\n"
    "1. Update contact email: UPDATE CONTACTS SET EMAIL = 'new@email.com' WHERE ID = 2;\n"
    "2. Mark task as completed: UPDATE TASKS SET STATUS = 'Completed' WHERE ID = 5;\n"
    "3. Change task deadline: UPDATE TASKS SET DEADLINE = '2024-12-31 23:59' WHERE ID = 3;\n"
    "4. Reassign task: UPDATE TASKS SET ASSIGNED_TO = (SELECT ID FROM CONTACTS WHERE NAME ILIKE 'Vivek') WHERE ID = 10;\n"
    "5. Update contact based on name: UPDATE CONTACTS SET ADDRESS = 'New Address' WHERE NAME ILIKE 'John Doe';\n"
    "6. Update task status based on title: UPDATE TASKS SET STATUS = 'Reviewed & Approved' WHERE TITLE ILIKE 'Project Planning';"
    ),
    }
    
    messages = [
        SystemMessage(content=system_prompts[action]),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        sql_query = response.content.strip()
        
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:-3].strip()
        elif sql_query.startswith("```"):
            sql_query = sql_query[3:-3].strip()
            
        return sql_query
    except Exception as e:
        st.error(f"Error generating SQL query: {e}")
        return ""

def classify_action(prompt: str) -> str:
    """Classify user intent into add/view/update actions using LLM"""
    system_prompt = "Classify the user's database request into one of: add, view, or update..."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    try:
        response = llm.invoke(messages)
        action = response.content.strip().lower()
        return action if action in ['add', 'view', 'update'] else 'view'
    except Exception as e:
        st.error(f"Error classifying action: {e}")
        return 'view'
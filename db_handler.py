import os
import psycopg2
from psycopg2 import pool
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Connection pooling
conn_pool = None

def init_db_pool():
    global conn_pool

    DB_USER = st.secrets.get("DB_USER", os.getenv("DB_USER", "neondb_owner"))
    DB_PASSWORD = st.secrets.get("DB_PASSWORD", os.getenv("DB_PASSWORD", "npg_LgZ4en1QpsyD"))
    DB_HOST = st.secrets.get("DB_HOST", os.getenv("DB_HOST", "ep-broad-bush-a5xjz0wm-pooler.us-east-2.aws.neon.tech"))
    DB_NAME = st.secrets.get("DB_NAME", os.getenv("DB_NAME", "neondb"))
    DB_PORT = st.secrets.get("DB_PORT", os.getenv("DB_PORT", "5432"))

    POSTGRES_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

    conn_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=POSTGRES_URI)

def get_db_connection():
    """Create a new PostgreSQL connection"""
    if hasattr(st, 'secrets'):
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            database=st.secrets["DB_NAME"], 
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            port=st.secrets["DB_PORT"],
            sslmode='require'
        )
    else:
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            sslmode='require'
        )

def execute_query(sql_query: str, params=None):
    """Execute a SQL query with connection pooling"""
    conn = None
    cur = None
    try:
        conn = conn_pool.getconn()
        cur = conn.cursor()

        if sql_query.strip().upper().startswith("SELECT"):
            cur.execute(sql_query, params or ())
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            return columns, rows
        else:
            cur.execute(sql_query, params or ())
            affected_rows = cur.rowcount
            conn.commit()
            return None, affected_rows
            
    except psycopg2.Error as e:
        st.error(f"SQL error: {e}")
        return None, None
    finally:
        if cur:
            cur.close()
        if conn:
            conn_pool.putconn(conn)

def get_contacts():
    """Fetch name and skills from Contacts table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT NAME, SKILLS FROM CONTACTS;")
    contacts = cursor.fetchall()
    conn.close()
    return contacts

def get_total_tasks():
    try:
        columns, data = execute_query("SELECT COUNT(*) FROM TASKS")
        return data[0][0] if data else 0
    except Exception as e:
        st.error(f"Error getting task count: {str(e)}")
        return 0

def get_overdue_tasks():
    try:
        conn = get_db_connection()
        result = pd.read_sql(
            "SELECT COUNT(*) FROM TASKS WHERE DEADLINE < CURRENT_TIMESTAMP", 
            conn
        )
        return result.iloc[0,0]
    except Exception as e:
        st.error(f"Error fetching overdue tasks: {str(e)}")
        return 0

# Initialize connection pool when module loads
init_db_pool()

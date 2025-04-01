from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from db_handler import get_db_connection

def calculate_initial_date(deadline_input: str) -> datetime:
    """Convert natural language deadline into a datetime object"""
    default_date = datetime.today()
    if not deadline_input:
        return default_date
        
    deadline_input = deadline_input.lower()
    
    if 'tomorrow' in deadline_input:
        return default_date + timedelta(days=1)
    elif 'next week' in deadline_input:
        return default_date + timedelta(weeks=1)
    elif 'in 2 days' in deadline_input:
        return default_date + timedelta(days=2)
    elif 'in 3 days' in deadline_input:
        return default_date + timedelta(days=3)
    elif 'next month' in deadline_input:
        return default_date + timedelta(days=30)
    else:
        return default_date

def create_gantt_chart():
    """Create Gantt chart visualization"""
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                title AS "TITLE", 
                deadline AS "DEADLINE",
                status AS "STATUS",
                priority AS "PRIORITY",
                category AS "CATEGORY"
            FROM tasks
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        df["DEADLINE"] = pd.to_datetime(df["DEADLINE"], errors='coerce')
        df = df.dropna(subset=["DEADLINE"])
        df["START_DATE"] = df["DEADLINE"] - pd.Timedelta(days=5)
        
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

        fig.update_layout(
            height=600,
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            showlegend=True,
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig, df
        
    except Exception as e:
        print(f"Error creating Gantt chart: {str(e)}")
        return None, None
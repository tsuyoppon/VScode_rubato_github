# access_log.py - Simple access logging for Streamlit app
import sqlite3
import datetime
import streamlit as st
import os
from pathlib import Path

# Database file path
DB_PATH = Path("logs/access_log.sqlite3")

def init_db():
    """Initialize the access log database"""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_ip TEXT,
            session_id TEXT,
            action TEXT,
            details TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def log_access(action: str, details: str = None):
    """Log an access event"""
    if not DB_PATH.parent.exists():
        init_db()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get user info from Streamlit session
        session_id = st.session_state.get("session_id", "unknown")
        user_ip = st.session_state.get("user_ip", "unknown")
        
        cursor.execute("""
            INSERT INTO access_logs (user_ip, session_id, action, details)
            VALUES (?, ?, ?, ?)
        """, (user_ip, session_id, action, details))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Silent fail - don't break the app if logging fails
        pass

def get_access_stats():
    """Get basic access statistics"""
    if not DB_PATH.exists():
        return {"total_visits": 0, "unique_sessions": 0}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total visits
        cursor.execute("SELECT COUNT(*) FROM access_logs WHERE action = 'page_view'")
        total_visits = cursor.fetchone()[0]
        
        # Unique sessions
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM access_logs")
        unique_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_visits": total_visits,
            "unique_sessions": unique_sessions
        }
        
    except Exception as e:
        return {"total_visits": 0, "unique_sessions": 0}

# Initialize database on import
if __name__ != "__main__":
    init_db()

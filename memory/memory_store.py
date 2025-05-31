import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ActivityLog(BaseModel):
    source: str
    timestamp: str
    classification: Dict
    extracted_fields: Dict
    action_triggered: Optional[str] = None
    agent_trace: List[str]

class MemoryStore:
    def __init__(self, db_path: str = None):
        # Use remote database URL from environment if available
        self.db_path = db_path or os.getenv('DATABASE_URL', 'memory/activity_log.db')
        self._initialize_db()

    def _get_connection(self):
        """Get database connection with appropriate configuration."""
        if self.db_path.startswith('http'):
            # For remote SQLite (like SQLite Online)
            # You would need to implement proper connection handling here
            # This is a placeholder for demonstration
            raise NotImplementedError("Remote SQLite connection not implemented yet")
        else:
            # Local SQLite connection
            return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        """Initialize the SQLite database with required tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                classification TEXT NOT NULL,
                extracted_fields TEXT NOT NULL,
                action_triggered TEXT,
                agent_trace TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def log_activity(self, activity: ActivityLog) -> int:
        """Log an activity to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity (
                source, timestamp, classification, 
                extracted_fields, action_triggered, agent_trace
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            activity.source,
            activity.timestamp,
            json.dumps(activity.classification),
            json.dumps(activity.extracted_fields),
            activity.action_triggered,
            json.dumps(activity.agent_trace)
        ))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return activity_id

    def get_activity(self, activity_id: int) -> Optional[ActivityLog]:
        """Retrieve a specific activity by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM activity WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return ActivityLog(
            source=row[1],
            timestamp=row[2],
            classification=json.loads(row[3]),
            extracted_fields=json.loads(row[4]),
            action_triggered=row[5],
            agent_trace=json.loads(row[6])
        )

    def get_all_activities(self) -> List[ActivityLog]:
        """Retrieve all activities from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM activity ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            ActivityLog(
                source=row[1],
                timestamp=row[2],
                classification=json.loads(row[3]),
                extracted_fields=json.loads(row[4]),
                action_triggered=row[5],
                agent_trace=json.loads(row[6])
            )
            for row in rows
        ]

# Create a singleton instance
memory_store = MemoryStore() 
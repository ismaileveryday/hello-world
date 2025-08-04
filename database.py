import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "data/tool_versions.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create submissions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    current_version TEXT NOT NULL,
                    email TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP,
                    is_outdated BOOLEAN DEFAULT 0,
                    latest_version TEXT,
                    notification_sent BOOLEAN DEFAULT 0
                )
            """)
            
            # Create version_sources table for tracking where to get latest versions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT UNIQUE NOT NULL,
                    source_type TEXT NOT NULL,  -- 'github', 'official_site', 'api'
                    source_url TEXT NOT NULL,
                    version_pattern TEXT,  -- regex pattern to extract version
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            self._populate_default_sources()
    
    def _populate_default_sources(self):
        """Populate default version sources for common tools"""
        default_sources = [
            ("SQL Server", "official_site", "https://docs.microsoft.com/en-us/sql/sql-server/", r"SQL Server (\d+)"),
            ("Python", "github", "https://api.github.com/repos/python/cpython/releases/latest", None),
            ("Node.js", "github", "https://api.github.com/repos/nodejs/node/releases/latest", None),
            ("Java", "official_site", "https://www.oracle.com/java/technologies/downloads/", r"Java (\d+)"),
            (".NET Framework", "github", "https://api.github.com/repos/dotnet/core/releases/latest", None),
            ("Oracle Database", "official_site", "https://www.oracle.com/database/", r"Oracle Database (\d+c)"),
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for tool_name, source_type, source_url, pattern in default_sources:
                cursor.execute("""
                    INSERT OR IGNORE INTO version_sources 
                    (tool_name, source_type, source_url, version_pattern)
                    VALUES (?, ?, ?, ?)
                """, (tool_name, source_type, source_url, pattern))
            conn.commit()
    
    def add_submission(self, tool_name: str, version: str, email: str) -> int:
        """Add a new tool version submission"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (tool_name, current_version, email)
                VALUES (?, ?, ?)
            """, (tool_name, version, email))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_submissions(self) -> List[Dict]:
        """Get all submissions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM submissions ORDER BY submitted_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_checks(self) -> List[Dict]:
        """Get submissions that need version checking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE last_checked IS NULL 
                   OR datetime(last_checked) < datetime('now', '-1 day')
                ORDER BY submitted_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_version_check(self, submission_id: int, latest_version: str, is_outdated: bool):
        """Update the version check results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions 
                SET latest_version = ?, is_outdated = ?, last_checked = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (latest_version, is_outdated, submission_id))
            conn.commit()
    
    def mark_notification_sent(self, submission_id: int):
        """Mark that notification has been sent for this submission"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions 
                SET notification_sent = 1
                WHERE id = ?
            """, (submission_id,))
            conn.commit()
    
    def get_version_source(self, tool_name: str) -> Optional[Dict]:
        """Get version source information for a tool"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM version_sources WHERE tool_name = ?
            """, (tool_name,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_outdated_submissions(self) -> List[Dict]:
        """Get submissions that are outdated and haven't been notified"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM submissions 
                WHERE is_outdated = 1 AND notification_sent = 0
                ORDER BY submitted_at ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

# Create global database instance
db = DatabaseManager()
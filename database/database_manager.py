"""
Database manager for JUSTLearn Bot SQLite implementation.
Handles all database operations
"""
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = 'data/justlearn.db'):
        """Initialize database manager."""
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Get database connection with error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mcqs'")
            if not cursor.fetchone():
                # Database doesn't exist, create it
                self._create_schema(conn)
            conn.commit()
    
    def _create_schema(self, conn):
        """Create database schema inline."""
        schema = '''
        -- MCQs table
        CREATE TABLE mcqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question TEXT NOT NULL,
            choices_json TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Users table
        CREATE TABLE users (
            user_id TEXT PRIMARY KEY,
            language TEXT DEFAULT 'en',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- User sessions table
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_data TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        -- User tests table
        CREATE TABLE user_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            test_type TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            score TEXT NOT NULL,
            weak_topics_json TEXT,
            questions_json TEXT,
            answers_json TEXT,
            correct_count INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            topics_selected_json TEXT,
            passed_topics_json TEXT,
            needs_more_training_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        -- User progress table
        CREATE TABLE user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            score REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        -- User weak topics pool
        CREATE TABLE user_weak_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, topic)
        );

        -- User needs more training pool
        CREATE TABLE user_needs_training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, topic)
        );

        -- Recommendations table
        CREATE TABLE recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL UNIQUE,
            youtube_url TEXT,
            resource_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- User reminder settings
        CREATE TABLE user_reminders (
            user_id TEXT PRIMARY KEY,
            enabled BOOLEAN DEFAULT FALSE,
            time_str TEXT,
            timezone TEXT DEFAULT 'Asia/Amman',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );

        -- Indexes
        CREATE INDEX idx_mcqs_topic ON mcqs(topic);
        CREATE INDEX idx_mcqs_difficulty ON mcqs(difficulty);
        CREATE INDEX idx_mcqs_topic_difficulty ON mcqs(topic, difficulty);
        CREATE INDEX idx_user_tests_user_id ON user_tests(user_id);
        CREATE INDEX idx_user_tests_date ON user_tests(date);
        CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
        CREATE INDEX idx_user_progress_date ON user_progress(date);
        CREATE INDEX idx_user_weak_topics_user_id ON user_weak_topics(user_id);
        CREATE INDEX idx_user_needs_training_user_id ON user_needs_training(user_id);
        '''
        conn.executescript(schema)
    
    # ===== MCQ OPERATIONS =====
    
    def load_mcqs(self) -> List[Dict]:
        """Load all MCQs from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic, difficulty, question, choices_json, correct_answer, explanation
                FROM mcqs
                ORDER BY id
            ''')
            
            mcqs = []
            for row in cursor.fetchall():
                mcq = {
                    'topic': row['topic'],
                    'difficulty': row['difficulty'],
                    'question': row['question'],
                    'choices': json.loads(row['choices_json']),
                    'correct_answer': row['correct_answer'],
                    'explanation': row['explanation']
                }
                mcqs.append(mcq)
            
            return mcqs
    
    def insert_mcqs(self, mcqs: List[Dict]):
        """Insert MCQs into database from JSON format."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for mcq in mcqs:
                cursor.execute('''
                    INSERT INTO mcqs (topic, difficulty, question, choices_json, correct_answer, explanation)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    mcq['topic'],
                    mcq['difficulty'],
                    mcq['question'],
                    json.dumps(mcq['choices']),
                    mcq['correct_answer'],
                    mcq['explanation']
                ))
            
            conn.commit()
    
    def get_mcqs_by_topic_and_difficulty(self, topics: List[str], difficulty: str = None) -> List[Dict]:
        """Get MCQs filtered by topics and difficulty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT topic, difficulty, question, choices_json, correct_answer, explanation
                FROM mcqs
                WHERE topic IN ({})
            '''.format(','.join('?' * len(topics)))
            
            params = topics[:]
            
            if difficulty:
                query += ' AND difficulty = ?'
                params.append(difficulty)
            
            cursor.execute(query, params)
            
            mcqs = []
            for row in cursor.fetchall():
                mcq = {
                    'topic': row['topic'],
                    'difficulty': row['difficulty'],
                    'question': row['question'],
                    'choices': json.loads(row['choices_json']),
                    'correct_answer': row['correct_answer'],
                    'explanation': row['explanation']
                }
                mcqs.append(mcq)
            
            return mcqs
    
    def get_all_topics(self) -> List[str]:
        """Get all unique topics from MCQs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT topic FROM mcqs ORDER BY topic')
            return [row['topic'] for row in cursor.fetchall()]
    
    # ===== USER OPERATIONS =====
    
    def ensure_user_exists(self, user_id: str, language: str = 'en'):
        """Ensure user exists in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, language)
                VALUES (?, ?)
            ''', (user_id, language))
            conn.commit()
    
    def get_user_language(self, user_id: str) -> str:
        """Get user's language preference."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['language'] if row else 'en'
    
    def set_user_language(self, user_id: str, language: str):
        """Set user's language preference."""
        self.ensure_user_exists(user_id, language)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET language = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (language, user_id))
            conn.commit()
    
    # ===== USER SESSION OPERATIONS =====
    
    def save_user_session(self, user_id: str, session_data: Dict):
        """Save user session data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Remove existing session
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            # Insert new session if data is not None
            if session_data is not None:
                # Convert any sets to lists before JSON serialization
                clean_session_data = self._convert_sets_to_lists(session_data)
                cursor.execute('''
                    INSERT INTO user_sessions (user_id, session_data)
                    VALUES (?, ?)
                ''', (user_id, json.dumps(clean_session_data)))
            
            conn.commit()
    
    def load_user_session(self, user_id: str) -> Optional[Dict]:
        """Load user session data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_data FROM user_sessions 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row['session_data'])
            return None
    
    def clear_user_session(self, user_id: str):
        """Clear user session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # ===== USER TESTS OPERATIONS =====
    
    def save_user_test(self, user_id: str, test_data: Dict):
        """Save user test result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_tests (
                    user_id, test_type, date, time, score,
                    weak_topics_json, questions_json, answers_json,
                    correct_count, total_questions,
                    topics_selected_json, passed_topics_json, needs_more_training_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                test_data.get('test_type', ''),
                test_data.get('date', ''),
                test_data.get('time', ''),
                test_data.get('score', ''),
                json.dumps(test_data.get('weak_topics', [])),
                json.dumps(test_data.get('questions', [])),
                json.dumps(test_data.get('answers', [])),
                test_data.get('correct_count', 0),
                len(test_data.get('questions', [])),
                json.dumps(test_data.get('topics_selected', [])),
                json.dumps(test_data.get('passed_topics', [])),
                json.dumps(test_data.get('needs_more_training', []))
            ))
            conn.commit()
    
    def get_user_tests(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get user's test history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT test_type, date, time, score, weak_topics_json,
                       questions_json, answers_json, correct_count,
                       topics_selected_json, passed_topics_json, needs_more_training_json
                FROM user_tests
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            tests = []
            for row in cursor.fetchall():
                test = {
                    'test_type': row['test_type'],
                    'date': row['date'],
                    'time': row['time'],
                    'score': row['score'],
                    'weak_topics': json.loads(row['weak_topics_json'] or '[]'),
                    'questions': json.loads(row['questions_json'] or '[]'),
                    'answers': json.loads(row['answers_json'] or '[]'),
                    'correct_count': row['correct_count']
                }
                
                # Add adaptive test specific fields if they exist
                if row['topics_selected_json']:
                    test['topics_selected'] = json.loads(row['topics_selected_json'])
                if row['passed_topics_json']:
                    test['passed_topics'] = json.loads(row['passed_topics_json'])
                if row['needs_more_training_json']:
                    test['needs_more_training'] = json.loads(row['needs_more_training_json'])
                
                tests.append(test)
            
            return tests
    
    # ===== USER PROGRESS OPERATIONS =====
    
    def save_user_progress(self, user_id: str, score: float):
        """Save user progress entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_progress (user_id, date, score)
                VALUES (?, ?, ?)
            ''', (user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), score))
            conn.commit()
    
    def get_user_progress(self, user_id: str) -> List[Dict]:
        """Get user's progress data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, score FROM user_progress
                WHERE user_id = ?
                ORDER BY created_at
                LIMIT 50
            ''', (user_id,))
            
            return [{'date': row['date'], 'score': row['score']} for row in cursor.fetchall()]
    
    # ===== WEAK TOPICS OPERATIONS =====
    
    def add_weak_topic(self, user_id: str, topic: str):
        """Add topic to user's weak topics pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_weak_topics (user_id, topic)
                VALUES (?, ?)
            ''', (user_id, topic))
            conn.commit()
    
    def get_weak_topics(self, user_id: str) -> List[str]:
        """Get user's weak topics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic FROM user_weak_topics
                WHERE user_id = ?
                ORDER BY created_at
            ''', (user_id,))
            
            return [row['topic'] for row in cursor.fetchall()]
    
    def add_needs_training_topic(self, user_id: str, topic: str):
        """Add topic to user's needs more training pool."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_needs_training (user_id, topic)
                VALUES (?, ?)
            ''', (user_id, topic))
            conn.commit()
    
    def get_needs_training_topics(self, user_id: str) -> List[str]:
        """Get user's needs more training topics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic FROM user_needs_training
                WHERE user_id = ?
                ORDER BY created_at
            ''', (user_id,))
            
            return [row['topic'] for row in cursor.fetchall()]
    
    # ===== RECOMMENDATIONS OPERATIONS =====
    
    def load_recommendations(self) -> Dict:
        """Load recommendations from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT topic, youtube_url, resource_url
                FROM recommendations
            ''')
            
            recommendations = {}
            for row in cursor.fetchall():
                recommendations[row['topic']] = {
                    'youtube': row['youtube_url'],
                    'resource': row['resource_url']
                }
            
            return recommendations
    
    def insert_recommendations(self, recommendations: Dict):
        """Insert recommendations into database from JSON format."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for topic, data in recommendations.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO recommendations (topic, youtube_url, resource_url)
                    VALUES (?, ?, ?)
                ''', (topic, data.get('youtube'), data.get('resource')))
            
            conn.commit()
    
    # ===== REMINDER OPERATIONS =====
    
    def save_user_reminder_settings(self, user_id: str, settings: Dict):
        """Save user reminder settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_reminders 
                (user_id, enabled, time_str, timezone, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                settings.get('enabled', False),
                settings.get('time'),
                settings.get('timezone', 'Asia/Amman')
            ))
            conn.commit()
    
    def get_user_reminder_settings(self, user_id: str) -> Dict:
        """Get user reminder settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT enabled, time_str, timezone
                FROM user_reminders
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                settings = {
                    'enabled': bool(row['enabled']),
                    'timezone': row['timezone']
                }
                if row['time_str']:
                    settings['time'] = row['time_str']
                return settings
            
            return {'enabled': False, 'timezone': 'Asia/Amman'}
    
    def get_all_users_with_reminders(self) -> List[Tuple[str, Dict]]:
        """Get all users with enabled reminders."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, time_str, timezone
                FROM user_reminders
                WHERE enabled = 1 AND time_str IS NOT NULL
            ''')
            
            return [(row['user_id'], {
                'time': row['time_str'],
                'timezone': row['timezone']
            }) for row in cursor.fetchall()]
        
    def _convert_sets_to_lists(self, data):
        """Convert any sets in data to lists for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._convert_sets_to_lists(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_sets_to_lists(item) for item in data]
        elif isinstance(data, set):
            return list(data)
        else:
            return data

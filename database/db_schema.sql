-- Database schema for JUSTLearn Bot 
-- MCQs table - stores all multiple choice questions
CREATE TABLE mcqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question TEXT NOT NULL,
    choices_json TEXT NOT NULL, -- JSON string of choices object {"A": "...", "B": "..."}
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Users table - stores user basic info
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    language TEXT DEFAULT 'en',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table - stores current test session data
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_data TEXT NOT NULL, -- JSON string of complete session data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- User tests table - stores all completed test results
CREATE TABLE user_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    test_type TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    score TEXT NOT NULL,
    weak_topics_json TEXT, -- JSON array of weak topics
    questions_json TEXT, -- JSON array of complete questions
    answers_json TEXT, -- JSON array of user answers
    correct_count INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    topics_selected_json TEXT, -- JSON array for adaptive tests
    passed_topics_json TEXT, -- JSON array for adaptive tests
    needs_more_training_json TEXT, -- JSON array for adaptive tests
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- User progress table - stores individual progress entries for charts
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    score REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- User weak topics pool - stores persistent weak topics
CREATE TABLE user_weak_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE(user_id, topic)
);

-- User needs more training pool - stores topics needing advanced practice
CREATE TABLE user_needs_training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE(user_id, topic)
);

-- Recommendations table - stores topic recommendations
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL UNIQUE,
    youtube_url TEXT,
    resource_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User reminder settings - stores reminder preferences
CREATE TABLE user_reminders (
    user_id TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    time_str TEXT,
    timezone TEXT DEFAULT 'Asia/Amman',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Indexes for optimal performance
CREATE INDEX idx_mcqs_topic ON mcqs(topic);
CREATE INDEX idx_mcqs_difficulty ON mcqs(difficulty);
CREATE INDEX idx_mcqs_topic_difficulty ON mcqs(topic, difficulty);
CREATE INDEX idx_user_tests_user_id ON user_tests(user_id);
CREATE INDEX idx_user_tests_date ON user_tests(date);
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX idx_user_progress_date ON user_progress(date);
CREATE INDEX idx_user_weak_topics_user_id ON user_weak_topics(user_id);
CREATE INDEX idx_user_needs_training_user_id ON user_needs_training(user_id);

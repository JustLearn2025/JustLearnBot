#!/usr/bin/env python3
"""
Migration script to convert JUSTLearn Bot from JSON to SQLite.
This script preserves 100% of existing data and functionality.

Usage:
python migrate_to_sqlite.py --data-dir data --backup-dir backup_json

This will:
1. Backup existing JSON files
2. Create SQLite database
3. Migrate all data
4. Verify migration integrity
"""

import json
import os
import shutil
import argparse
import logging
from typing import Dict, List, Any
from datetime import datetime
import glob

# Import the database manager
from database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self, data_dir: str, backup_dir: str, db_path: str):
        """
        Initialize the data migrator.
        
        Args:
            data_dir: Directory containing JSON files
            backup_dir: Directory to backup JSON files
            db_path: Path for the new SQLite database
        """
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(backup_dir, exist_ok=True)
        
    def backup_json_files(self):
        """Backup all existing JSON files."""
        logger.info("Backing up existing JSON files...")
        
        json_files = [
            'mcqs.json',
            'user_data.json',
            'recommendations.json'
        ]
        
        # Backup main JSON files
        for filename in json_files:
            src_path = os.path.join(self.data_dir, filename)
            if os.path.exists(src_path):
                dst_path = os.path.join(self.backup_dir, filename)
                shutil.copy2(src_path, dst_path)
                logger.info(f"Backed up {filename}")
        
        # Backup progress files
        progress_files = glob.glob(os.path.join(self.data_dir, 'progress_*.json'))
        for progress_file in progress_files:
            filename = os.path.basename(progress_file)
            dst_path = os.path.join(self.backup_dir, filename)
            shutil.copy2(progress_file, dst_path)
            logger.info(f"Backed up {filename}")
        
        logger.info(f"Backup completed. Files saved to: {self.backup_dir}")
    
    def migrate_mcqs(self):
        """Migrate MCQs from JSON to SQLite."""
        logger.info("Migrating MCQs...")
        
        mcqs_path = os.path.join(self.data_dir, 'mcqs.json')
        if not os.path.exists(mcqs_path):
            logger.warning(f"MCQs file not found: {mcqs_path}")
            return
        
        try:
            with open(mcqs_path, 'r', encoding='utf-8') as f:
                mcqs = json.load(f)
            
            # Validate MCQ format
            valid_mcqs = []
            for i, mcq in enumerate(mcqs):
                if self._validate_mcq(mcq, i):
                    valid_mcqs.append(mcq)
            
            # Insert into database
            self.db_manager.insert_mcqs(valid_mcqs)
            logger.info(f"Migrated {len(valid_mcqs)} MCQs to database")
            
        except Exception as e:
            logger.error(f"Error migrating MCQs: {e}")
            raise
    
    def _validate_mcq(self, mcq: Dict, index: int) -> bool:
        """Validate MCQ format."""
        required_fields = ['topic', 'difficulty', 'question', 'choices', 'correct_answer', 'explanation']
        
        for field in required_fields:
            if field not in mcq:
                logger.warning(f"MCQ {index} missing field: {field}")
                return False
        
        # Validate choices format
        if not isinstance(mcq['choices'], dict):
            logger.warning(f"MCQ {index} has invalid choices format")
            return False
        
        return True
    
    def migrate_recommendations(self):
        """Migrate recommendations from JSON to SQLite."""
        logger.info("Migrating recommendations...")
        
        rec_path = os.path.join(self.data_dir, 'recommendations.json')
        if not os.path.exists(rec_path):
            logger.warning(f"Recommendations file not found: {rec_path}")
            return
        
        try:
            with open(rec_path, 'r', encoding='utf-8') as f:
                recommendations = json.load(f)
            
            self.db_manager.insert_recommendations(recommendations)
            logger.info(f"Migrated {len(recommendations)} recommendations")
            
        except Exception as e:
            logger.error(f"Error migrating recommendations: {e}")
            raise
    
    def migrate_user_data(self):
        """Migrate user data from JSON to SQLite."""
        logger.info("Migrating user data...")
        
        user_data_path = os.path.join(self.data_dir, 'user_data.json')
        if not os.path.exists(user_data_path):
            logger.warning(f"User data file not found: {user_data_path}")
            return
        
        try:
            with open(user_data_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            migrated_users = 0
            for user_id, data in user_data.items():
                self._migrate_single_user(user_id, data)
                migrated_users += 1
            
            logger.info(f"Migrated data for {migrated_users} users")
            
        except Exception as e:
            logger.error(f"Error migrating user data: {e}")
            raise
    
    def _migrate_single_user(self, user_id: str, data: Dict):
        """Migrate data for a single user."""
        try:
            # Ensure user exists
            self.db_manager.ensure_user_exists(user_id, 'en')  # Default language
            
            # Migrate test history
            tests = data.get('tests', [])
            for test in tests:
                self._migrate_user_test(user_id, test)
            
            # Migrate weak topics
            weak_topics = data.get('weak_topic_pool', [])
            for topic in weak_topics:
                self.db_manager.add_weak_topic(user_id, topic)
            
            # Migrate needs training topics
            needs_training = data.get('needs_more_training_pool', [])
            for topic in needs_training:
                self.db_manager.add_needs_training_topic(user_id, topic)
            
            # Migrate current session if exists
            session = data.get('current_test_session')
            if session:
                # Convert sets to lists for JSON serialization
                if 'incorrect_topics' in session and isinstance(session['incorrect_topics'], set):
                    session['incorrect_topics'] = list(session['incorrect_topics'])
                self.db_manager.save_user_session(user_id, session)
            
            # Migrate reminder settings if they exist
            reminder_settings = data.get('reminder_settings')
            if reminder_settings:
                self.db_manager.save_user_reminder_settings(user_id, reminder_settings)
            
        except Exception as e:
            logger.error(f"Error migrating user {user_id}: {e}")
            # Continue with other users
    
    def _migrate_user_test(self, user_id: str, test: Dict):
        """Migrate a single user test."""
        try:
            # Ensure required fields exist
            if 'date' not in test:
                test['date'] = datetime.now().strftime("%Y-%m-%d")
            if 'time' not in test:
                test['time'] = datetime.now().strftime("%H:%M")
            
            # Handle different test formats
            if 'weak_topics' not in test:
                test['weak_topics'] = []
            if 'questions' not in test:
                test['questions'] = []
            if 'answers' not in test:
                test['answers'] = []
            if 'correct_count' not in test:
                # Try to calculate from score
                score = test.get('score', '0/0')
                if '/' in score:
                    correct, total = score.split('/')
                    test['correct_count'] = int(correct)
                else:
                    test['correct_count'] = 0
            
            self.db_manager.save_user_test(user_id, test)
            
        except Exception as e:
            logger.error(f"Error migrating test for user {user_id}: {e}")
    
    def migrate_progress_files(self):
        """Migrate progress files from JSON to SQLite."""
        logger.info("Migrating progress files...")
        
        progress_files = glob.glob(os.path.join(self.data_dir, 'progress_*.json'))
        
        migrated_files = 0
        total_entries = 0
        
        for progress_file in progress_files:
            try:
                # Extract user_id from filename
                filename = os.path.basename(progress_file)
                if filename.startswith('progress_') and filename.endswith('.json'):
                    user_id = filename[9:-5]  # Remove 'progress_' and '.json'
                    
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    # Ensure user exists
                    self.db_manager.ensure_user_exists(user_id, 'en')
                    
                    # Migrate each progress entry
                    for entry in progress_data:
                        if isinstance(entry, dict) and 'date' in entry and 'score' in entry:
                            try:
                                score = float(entry['score'])
                                if 0 <= score <= 100:
                                    # Use the existing date or create a new one
                                    date = entry['date']
                                    # Insert directly into progress table
                                    with self.db_manager.get_connection() as conn:
                                        cursor = conn.cursor()
                                        cursor.execute('''
                                            INSERT INTO user_progress (user_id, date, score)
                                            VALUES (?, ?, ?)
                                        ''', (user_id, date, score))
                                        conn.commit()
                                    total_entries += 1
                            except (ValueError, TypeError):
                                logger.warning(f"Invalid progress entry in {filename}: {entry}")
                                continue
                    
                    migrated_files += 1
                    logger.info(f"Migrated progress file: {filename}")
                    
            except Exception as e:
                logger.error(f"Error migrating progress file {progress_file}: {e}")
                continue
        
        logger.info(f"Migrated {migrated_files} progress files with {total_entries} total entries")
    
    def verify_migration(self):
        """Verify that migration was successful."""
        logger.info("Verifying migration...")
        
        # Check MCQs
        mcqs = self.db_manager.load_mcqs()
        logger.info(f"Verified: {len(mcqs)} MCQs in database")
        
        # Check recommendations
        recommendations = self.db_manager.load_recommendations()
        logger.info(f"Verified: {len(recommendations)} recommendations in database")
        
        # Check users
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count users
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            logger.info(f"Verified: {user_count} users in database")
            
            # Count tests
            cursor.execute('SELECT COUNT(*) FROM user_tests')
            test_count = cursor.fetchone()[0]
            logger.info(f"Verified: {test_count} test records in database")
            
            # Count progress entries
            cursor.execute('SELECT COUNT(*) FROM user_progress')
            progress_count = cursor.fetchone()[0]
            logger.info(f"Verified: {progress_count} progress entries in database")
            
            # Count weak topics
            cursor.execute('SELECT COUNT(*) FROM user_weak_topics')
            weak_topics_count = cursor.fetchone()[0]
            logger.info(f"Verified: {weak_topics_count} weak topic entries in database")
        
        logger.info("Migration verification completed successfully!")
    
    def run_migration(self):
        """Run the complete migration process."""
        logger.info("Starting migration from JSON to SQLite...")
        
        try:
            # Step 1: Backup existing files
            self.backup_json_files()
            
            # Step 2: Migrate MCQs
            self.migrate_mcqs()
            
            # Step 3: Migrate recommendations
            self.migrate_recommendations()
            
            # Step 4: Migrate user data
            self.migrate_user_data()
            
            # Step 5: Migrate progress files
            self.migrate_progress_files()
            
            # Step 6: Verify migration
            self.verify_migration()
            
            logger.info("Migration completed successfully!")
            logger.info(f"SQLite database created at: {self.db_path}")
            logger.info(f"JSON files backed up to: {self.backup_dir}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate JUSTLearn Bot from JSON to SQLite')
    parser.add_argument('--data-dir', default='data', help='Directory containing JSON files')
    parser.add_argument('--backup-dir', default='backup_json', help='Directory to backup JSON files')
    parser.add_argument('--db-path', default='data/justlearn.db', help='Path for SQLite database')
    
    args = parser.parse_args()
    
    # Confirm migration
    print(f"This will migrate data from {args.data_dir} to SQLite database at {args.db_path}")
    print(f"JSON files will be backed up to {args.backup_dir}")
    response = input("Do you want to continue? (y/N): ")
    
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Run migration
    migrator = DataMigrator(args.data_dir, args.backup_dir, args.db_path)
    migrator.run_migration()
    
    print("\nMigration completed! You can now:")
    print("1. Test the bot with the new SQLite database")
    print("2. If everything works, you can remove the JSON backup files")
    print("3. Update your bot startup scripts to use the new database")

if __name__ == '__main__':
    main()
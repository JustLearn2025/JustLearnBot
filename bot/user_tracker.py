"""
User tracking module for JUSTLearn Bot.
Handles user session data, test results, and performance analytics.

"""
import json
import os
import pytz
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from database.database_manager import DatabaseManager

class UserTracker:
    def __init__(self, db_path: str = 'data/justlearn.db'):
        """
        Initialize the user tracker with SQLite database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_manager = DatabaseManager(db_path)
        # Cache for user data to maintain performance
        self._user_cache = {}
    
    def _get_user_data_from_db(self, user_id: str) -> Dict:
        """Load user data from database."""
        self.db_manager.ensure_user_exists(user_id)
        
        # Get basic user info
        user_data = {
            "tests": self.db_manager.get_user_tests(user_id, limit=5),
            "adaptive_tests": [],  # Will be populated from tests
            "weak_topic_pool": self.db_manager.get_weak_topics(user_id),
            "needs_more_training_pool": self.db_manager.get_needs_training_topics(user_id),
            "current_test_session": self.db_manager.load_user_session(user_id)
        }
        
        # Extract adaptive tests from tests history
        for test in user_data["tests"]:
            if test.get("test_type") == "Adaptive Test":
                user_data["adaptive_tests"].append(test)
        
        # Limit adaptive tests to 5
        user_data["adaptive_tests"] = user_data["adaptive_tests"][:5]
        
        return user_data
    
    def _save_user_data_to_db(self, user_id: str, user_data: Dict) -> None:
        """Save user data to database."""
        # Save session if it exists
        if "current_test_session" in user_data:
            self.db_manager.save_user_session(user_id, user_data["current_test_session"])
        
        # Save weak topics
        if "weak_topic_pool" in user_data:
            for topic in user_data["weak_topic_pool"]:
                self.db_manager.add_weak_topic(user_id, topic)
        
        # Save needs training topics
        if "needs_more_training_pool" in user_data:
            for topic in user_data["needs_more_training_pool"]:
                self.db_manager.add_needs_training_topic(user_id, topic)
    
    def get_user_data(self, user_id: str) -> Dict:
        """Get data for a specific user"""
        # Check cache first
        if user_id not in self._user_cache:
            self._user_cache[user_id] = self._get_user_data_from_db(user_id)
        
        return self._user_cache[user_id]
    
    def _update_cache(self, user_id: str):
        """Update cache from database."""
        self._user_cache[user_id] = self._get_user_data_from_db(user_id)
    
    def start_test_session(self, user_id: str, test_type: str, questions: List[Dict]) -> None:
        """
        Start a new test session for the user.
    
        Args:
            user_id: Telegram user ID
            test_type: Type of test (First Exam, Second Exam, Final Exam, Mini Test)
            questions: List of questions for the test
        """
        user_data = self.get_user_data(user_id)
    
        # Initialize a new test session with all required fields
        session_data = {
            "test_type": test_type,  # Preserve the exact test type
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "questions": questions,
            "current_question_index": 0,
            "correct_answers": 0,
            "incorrect_topics": [],  # Use list instead of set for JSON serialization
            "user_answers": []  # Initialize empty answers list
        }
        
        user_data["current_test_session"] = session_data
        self.db_manager.save_user_session(user_id, session_data)
        
        print(f"Starting test session for user {user_id} with type: {test_type}")
        print(f"Number of questions: {len(questions)}")
    
    def get_current_question(self, user_id: str) -> Optional[Dict]:
        """
        Get the current question for the user's active test session.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Current question dictionary or None if no active session
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")
        
        if not session:
            return None
            
        index = session.get("current_question_index", 0)
        questions = session.get("questions", [])
        
        if index < len(questions):
            return questions[index]
        else:
            return None
    
    def process_answer(self, user_id: str, answer: str) -> Dict:
        """
        Process user's answer to current question.
    
        Args:
            user_id: Telegram user ID
            answer: User's answer (A, B, C, or D)
        
        Returns:
            Dictionary with results
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")
    
        if not session:
            return {"error": "No active test session"}
        
        current_index = session.get("current_question_index", 0)
        questions = session.get("questions", [])
    
        if current_index >= len(questions):
            return {"error": "No more questions in this test"}
        
        question = questions[current_index]
        is_correct = answer.upper() == question["correct_answer"]
    
        # Create answers array if it doesn't exist
        if "user_answers" not in session:
            session["user_answers"] = []
    
        # Store the user's answer
        session["user_answers"].append(answer.upper())
    
        # Update session data
        if is_correct:
            session["correct_answers"] += 1
        else:
            # Add to incorrect topics (as a list to avoid serialization issues)
            if "incorrect_topics" not in session:
                session["incorrect_topics"] = []
            if isinstance(session["incorrect_topics"], set):
                session["incorrect_topics"] = list(session["incorrect_topics"])
            
            topic = question["topic"]
            if topic not in session["incorrect_topics"]:
                session["incorrect_topics"].append(topic)
    
        # Move to next question
        session["current_question_index"] += 1
        
        # Save updated session
        self.db_manager.save_user_session(user_id, session)
        user_data["current_test_session"] = session
    
        # Check if test is completed
        test_completed = session["current_question_index"] >= len(questions)
        test_results = None
    
        if test_completed:
            # Save a backup of the session before completing (for answer recovery)
            user_data["session_backup"] = session.copy()
            test_results = self.complete_test_session(user_id)
    
        return {
            "correct": is_correct,
            "question": question,
            "correct_answer": question["correct_answer"],
            "explanation": question["explanation"],
            "test_completed": test_completed,
            "test_results": test_results
        }

    def complete_test_session(self, user_id: str) -> Dict:
        """
        Complete the current test session and save results.
     
        Args:
            user_id: Telegram user ID
        
        Returns:
            Test results summary 
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")

        if not session:
            return {"error": "No active test session"}

        # Calculate score
        total_questions = len(session["questions"])
        correct_answers = session.get("correct_answers", 0)
        score = f"{correct_answers}/{total_questions}"

        # Convert incorrect_topics to list if it's a set
        if isinstance(session["incorrect_topics"], set):
            weak_topics = list(session["incorrect_topics"])
        else:
            weak_topics = session["incorrect_topics"]

        # Get user answers if available
        user_answers = session.get("user_answers", [])

        # Create test result entry
        jordan_tz = pytz.timezone('Asia/Amman')
        now = datetime.now(jordan_tz)

        test_result = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "test_type": session["test_type"],
            "score": score,
            "weak_topics": weak_topics,
            "questions": session["questions"],
            "correct_count": correct_answers,
            "answers": user_answers
        }

        # Save test to database
        self.db_manager.save_user_test(user_id, test_result)

        # Update weak topic pool
        for topic in weak_topics:
            self.db_manager.add_weak_topic(user_id, topic)

        # Record progress for visual tracking
        try:
            # Calculate normalized score for progress
            if total_questions > 0:
                normalized_score = (correct_answers / total_questions) * 100
                self.db_manager.save_user_progress(user_id, normalized_score)
        except Exception as e:
            print(f"Error recording progress: {e}")

        # Clear current test session
        user_data["current_test_session"] = None
        self.db_manager.clear_user_session(user_id)
        
        # Update cache
        self._update_cache(user_id)

        print(f"Test completed for user {user_id}, type: {test_result['test_type']}")
        print(f"Score: {score}")

        return test_result
    
    def get_weak_topics(self, user_id: str) -> List[str]:
        """
        Get weak topics for a user based on test history.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of weak topic names
        """
        return self.db_manager.get_weak_topics(user_id)
    
    def has_active_test(self, user_id: str) -> bool:
        """
        Check if user has an active test session.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Boolean indicating if user has an active test
        """
        user_data = self.get_user_data(user_id)
        return user_data.get("current_test_session") is not None
    
    def is_adaptive_test(self, user_id: str) -> bool:
        """
        Check if the current test is an adaptive test.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Boolean indicating if current test is adaptive
        """
        user_data = self.get_user_data(str(user_id))
        session = user_data.get("current_test_session")
        return session is not None and session.get("test_type") == "Adaptive Test"
    
    def is_exam_test(self, user_id: str) -> bool:
        """
        Check if the current test is an exam.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Boolean indicating if current test is an exam
        """
        user_data = self.get_user_data(str(user_id))
        session = user_data.get("current_test_session")
        
        if not session:
            return False
            
        test_type = session.get("test_type", "")
        return any(exam_type in test_type for exam_type in ["First Exam", "Second Exam", "Final Exam"])
    
    def start_adaptive_test_session(self, user_id: str, topics: List[str]) -> None:
        """
        Initialize an adaptive test session.
    
        Args:
            user_id: Telegram user ID
            topics: List of topics for the test
        """
        # Initialize a new adaptive test session
        session_data = {
            "test_type": "Adaptive Test",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topics": topics.copy(),
            "remaining_topics": topics.copy(),
            "current_topic_index": 0,
            "current_question": None,
            "completed_topics": [],
            "weak_topics": [],
            "passed_topics": [],
            "answers": []
        }
    
    # Save to database AND update cache
        self.db_manager.save_user_session(user_id, session_data)
    
    # Force cache update
        if user_id in self._user_cache:
            self._user_cache[user_id]["current_test_session"] = session_data
        else:
            self._user_cache[user_id] = self._get_user_data_from_db(user_id)


    def get_current_adaptive_topic(self, user_id: str) -> Optional[str]:
        """
        Get the current topic for the adaptive test.
    
        Args:
            user_id: Telegram user ID
        
        Returns:
            Current topic or None if no adaptive test active
        """
        # Get fresh data from database to avoid cache issues
        session = self.db_manager.load_user_session(user_id)
    
        if not session or session.get("test_type") != "Adaptive Test":
            return None
    
        remaining_topics = session.get("remaining_topics", [])
        if not remaining_topics:
            return None
    
        return remaining_topics[0]

    def set_current_adaptive_question(self, user_id: str, question: Dict) -> None:
        """
        Set the current question in the adaptive test session.
    
        Args:
            user_id: Telegram user ID
            question: Question dictionary
        """
        # Get current session from database
        session = self.db_manager.load_user_session(user_id)
    
        if not session or session.get("test_type") != "Adaptive Test":
            return
    
        session["current_question"] = question
    
        # Save to database AND update cache
        self.db_manager.save_user_session(user_id, session)
    
        # Update cache
        if user_id in self._user_cache:
            self._user_cache[user_id]["current_test_session"] = session


    def get_adaptive_test_session(self, user_id: str) -> Optional[Dict]: 
        """
        Get the current adaptive test session.
    
        Args:
            user_id: Telegram user ID
        
        Returns:
            Current adaptive test session or None if no active session
        """
        # Always get fresh data from database
        session = self.db_manager.load_user_session(user_id)
    
        if not session or session.get("test_type") != "Adaptive Test":
            return None
    
        return session

    def record_adaptive_answer(self, user_id: str, is_correct: bool, topic: str, difficulty: str) -> None:
        """
        Record an answer in the adaptive test session.
        
        Args:
            user_id: Telegram user ID
            is_correct: Whether the answer was correct
            topic: Topic of the question
            difficulty: Difficulty of the question
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")
        
        if not session or session.get("test_type") != "Adaptive Test":
            return
        
        # Record the answer
        session["answers"].append({
            "topic": topic,
            "difficulty": difficulty,
            "correct": is_correct,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        user_data["current_test_session"] = session
        self.db_manager.save_user_session(user_id, session)

    def move_to_next_adaptive_topic(self, user_id: str) -> Optional[str]:
        """
        Move to the next topic in the adaptive test.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Next topic or None if no more topics
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")
        
        if not session or session.get("test_type") != "Adaptive Test":
            return None
        
        # Remove current topic from remaining
        if session["remaining_topics"]:
            completed_topic = session["remaining_topics"].pop(0)
            session["completed_topics"].append(completed_topic)
            
            user_data["current_test_session"] = session
            self.db_manager.save_user_session(user_id, session)
        
        # Get next topic if available
        if session["remaining_topics"]:
            next_topic = session["remaining_topics"][0]
            return next_topic
        
        return None

    def update_adaptive_test_results(self, user_id: str, result_type: str) -> None:
        """
        Update the results of the adaptive test.
    
        Args:
            user_id: Telegram user ID
            result_type: Type of result (complete, offer_reevaluation)
        """
        user_data = self.get_user_data(user_id)
        session = user_data.get("current_test_session")
    
        if not session or session.get("test_type") != "Adaptive Test":
            return
    
        # Analyze results
        topic_results = {}
        for answer in session["answers"]:
            topic = answer["topic"]
            if topic not in topic_results:
                topic_results[topic] = {"correct": 0, "total": 0}
        
            topic_results[topic]["total"] += 1
            if answer["correct"]:
                topic_results[topic]["correct"] += 1
    
        # Mark weak topics (less than 50% correct)
        weak_topics = []
        passed_topics = []
        for topic, result in topic_results.items():
            if result["total"] > 0:
                score = result["correct"] / result["total"]
                if score < 0.5:
                    weak_topics.append(topic)
                else:
                    passed_topics.append(topic)
    
        # Update session data
        session["weak_topics"] = weak_topics
        session["passed_topics"] = passed_topics
    
        # Calculate overall score
        total_questions = len(session["answers"])
        correct_answers = sum(1 for answer in session["answers"] if answer["correct"])
        score = f"{correct_answers}/{total_questions}"
    
        # If test is complete, save to test history
        if result_type == "complete":
            # Create test result entry
            test_result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "test_type": "Adaptive Test",
                "topics_selected": session["topics"],
                "weak_topics": weak_topics,
                "passed_topics": passed_topics,
                "score": score
            }
        
            # Save test to database
            self.db_manager.save_user_test(user_id, test_result)
        
            # Update weak topic pool
            for topic in weak_topics:
                self.db_manager.add_weak_topic(user_id, topic)
        
            # Record progress
            try:
                if total_questions > 0:
                    normalized_score = (correct_answers / total_questions) * 100
                    self.db_manager.save_user_progress(user_id, normalized_score)
            except Exception as e:
                print(f"Error recording adaptive test progress: {e}")
        
            # Only clear the session if we're not offering reevaluation
            if result_type != "offer_reevaluation":
                user_data["current_test_session"] = None
                self.db_manager.clear_user_session(user_id)
                
        # Update cache
        self._update_cache(user_id)

    def get_adaptive_test_results(self, user_id: str) -> Optional[Dict]:
        """
        Get the most recent adaptive test results.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Most recent adaptive test results or None if no results
        """
        tests = self.db_manager.get_user_tests(user_id, limit=5)
        
        for test in tests:
            if test.get("test_type") == "Adaptive Test":
                return test
                
        return None

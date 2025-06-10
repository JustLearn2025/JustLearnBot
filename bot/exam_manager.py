"""
Exam manager module for JUSTLearn Bot.
Handles creation and management of different exam types.
"""
from typing import List, Dict, Optional
import random
from datetime import datetime
from .search_engine import SearchEngine
from .user_tracker import UserTracker

class ExamManager:
    def __init__(self, search_engine: SearchEngine, user_tracker: UserTracker):
        """
        Initialize the exam manager.
        
        Args:
            search_engine: Instance of SearchEngine
            user_tracker: Instance of UserTracker
        """
        self.search_engine = search_engine
        self.user_tracker = user_tracker
        
        # Define exam topics
        self.exam_topics = {
            "first_exam": ["Big-O", "Arrays", "Linked Lists", "Algorithm Analysis and Big-O Notation", "Array-Based Lists", "Linked Lists"],
            "second_exam": ["Stacks", "Queues", "Recursion", "Hashing", "Searching and Hashing"],
            "final_exam": self.search_engine.get_all_topics()
        }
        
        # Define question counts
        self.question_counts = {
            "first_exam": 20,
            "second_exam": 20,
            "final_exam": 40,
            "mini_test": None  # Dynamic based on weak topics
        }
    
    def start_first_exam(self, user_id: str) -> Dict:
        """
        Start first exam for the user with exactly 20 questions and  shuffling.

        Args:
            user_id: Telegram user ID
        
        Returns:
            Dictionary with first question or error message
        """
        # Check if user already has an active test
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}

        topics = self.exam_topics["first_exam"]
        count = 20  # Exactly 20 questions

        # Get questions with shuffling from search engine
        selected_questions = self.search_engine.get_questions_by_topic(topics, count=count)

        if not selected_questions:
            return {"error": "Failed to create exam. No questions available for these topics."}

        # Additional shuffle for extra randomization
        for _ in range(3):
            random.shuffle(selected_questions)

        # Start test session with EXACT test type name
        self.user_tracker.start_test_session(user_id, "First Exam", selected_questions)

        # Return first question
        return {"first_question": self.user_tracker.get_current_question(user_id)}

    def start_second_exam(self, user_id: str, exclude_hashing: bool = False) -> Dict:
        """
        Start second exam for the user with exactly 20 questions and shuffling.

        Args:
            user_id: Telegram user ID
            exclude_hashing: Whether to exclude Hashing topic
        
        Returns:
            Dictionary with first question or error message
        """
        # Check if user already has an active test
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}

        topics = self.exam_topics["second_exam"].copy()
        count = 20  # Exactly 20 questions

        # Apply exclusion if requested
        exclude_topics = ["Hashing", "Searching and Hashing"] if exclude_hashing else None
        if exclude_topics:
            topics = [t for t in topics if t not in exclude_topics 
                    and not any(t.lower() == et.lower() for et in exclude_topics)]

        # Get questions with shuffling from search engine
        selected_questions = self.search_engine.get_questions_by_topic(topics, count=count)

        if not selected_questions:
            return {"error": "Failed to create exam. No questions available for these topics."}

        # Additional shuffle for extra randomization
        for _ in range(3):
            random.shuffle(selected_questions)

        # Start test session with EXACT test type name
        self.user_tracker.start_test_session(user_id, "Second Exam", selected_questions)

        # Return first question
        return {"first_question": self.user_tracker.get_current_question(user_id)}

    def start_final_exam(self, user_id: str, exclude_big_o: bool = False) -> Dict:
        """
        Start final exam for the user with exactly 40 questions and shuffling.

        Args:
            user_id: Telegram user ID
            exclude_big_o: Whether to exclude Big-O topic
        
        Returns:
            Dictionary with first question or error message
        """
        # Check if user already has an active test
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}

        topics = self.exam_topics["final_exam"].copy()
        count = 40  # Exactly 40 questions

        # Apply exclusion if requested
        exclude_topics = ["Big-O", "Algorithm Analysis and Big-O Notation"] if exclude_big_o else None
        if exclude_topics:
            topics = [t for t in topics if t not in exclude_topics 
                    and not any(t.lower() == et.lower() for et in exclude_topics)]

        # Get questions with shuffling from search engine
        selected_questions = self.search_engine.get_questions_by_topic(topics, count=count)

        if not selected_questions:
            return {"error": "Failed to create exam. No questions available for these topics."}

        # Additional shuffle for extra randomization
        for _ in range(3):
            random.shuffle(selected_questions)

        # Start test session with EXACT test type name
        self.user_tracker.start_test_session(user_id, "Final Exam", selected_questions)

        # Return first question
        return {"first_question": self.user_tracker.get_current_question(user_id)}

    def process_answer(self, user_id: str, answer: str) -> Dict:
        """
        Process user's answer and get next question if available.
    
        Args:
            user_id: Telegram user ID
            answer: User's answer (A, B, C, or D)
        
        Returns:
        """
        # Process the answer
        result = self.user_tracker.process_answer(user_id, answer)
    
        if "error" in result:
            return result
    
        # If test is completed, return results
        if result.get("test_completed", False):
            return {
                "correct": result["correct"],
                "correct_answer": result["correct_answer"],
                "explanation": result["explanation"],
                "question": result["question"],
                "test_completed": True,
                "test_results": result["test_results"]
            }
    
    # Get next question
        next_question = self.user_tracker.get_current_question(user_id)
    
        return {
            "correct": result["correct"],
            "correct_answer": result["correct_answer"],
            "explanation": result["explanation"],
            "question": result["question"],
            "test_completed": False,
            "next_question": next_question
        }
        
    # ===== ADAPTIVE TEST METHODS =====
    
    def start_adaptive_test(self, user_id: str, selected_topics: List[str]) -> Dict:
        """
        Start an adaptive test for the user.
        
        Args:
            user_id: Telegram user ID
            selected_topics: List of topics selected by the user
            
        Returns:
            Dictionary with first question or error message
        """
        # Check if user already has an active test
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}
        
        # Validate topics
        all_topics = self.search_engine.get_all_topics()
        
        # Handle topic variations
        topic_mapping = self.search_engine.get_standardized_topic_mapping()
        valid_topics = []
        
        for selected in selected_topics:
            # Check if it's a valid topic as-is
            if selected in all_topics:
                valid_topics.append(selected)
                continue
                
            # Check if it's a variation of a valid topic
            for main_topic, variations in topic_mapping.items():
                if selected == main_topic or selected in variations:
                    if main_topic in all_topics:
                        valid_topics.append(main_topic)
                    else:
                        for v in variations:
                            if v in all_topics:
                                valid_topics.append(v)
                                break
        
        # Remove duplicates
        valid_topics = list(dict.fromkeys(valid_topics))
        
        if not valid_topics:
            return {"error": "None of the selected topics are valid. Please select from available topics."}
        
        # Initialize adaptive test session
        self.user_tracker.start_adaptive_test_session(user_id, valid_topics)
        
        # Get first question (Medium difficulty)
        current_topic = self.user_tracker.get_current_adaptive_topic(user_id)
        if not current_topic:
            return {"error": "Failed to get current topic. Please try again."}
        
        # Get a random medium difficulty question for the topic
        question = self.search_engine.get_random_question_by_topic_and_difficulty(current_topic, "Medium")
        
        if not question:
            return {"error": f"No medium difficulty questions available for {current_topic}. Please try another topic."}
        
        # Save current question in user session
        self.user_tracker.set_current_adaptive_question(user_id, question)
        
        return {"success": True, "question": question, "is_first_question": True}

    def process_adaptive_answer(self, user_id: str, answer: str) -> Dict:
        """
        Process user's answer in adaptive test and determine next question.
        
        Args:
            user_id: Telegram user ID
            answer: User's answer (A, B, C, or D)
            
        Returns:
            Dictionary with result and next actions
        """
        # Get current session data
        session = self.user_tracker.get_adaptive_test_session(user_id)
        if not session:
            return {"error": "No active adaptive test session. Please start a new test."}
        
        # Get current question
        current_question = session.get("current_question")
        if not current_question:
            return {"error": "No current question. Please start a new test."}
        
        # Check if the answer is correct
        is_correct = answer.upper() == current_question["correct_answer"]
        current_topic = current_question["topic"]
        current_difficulty = current_question["difficulty"]
        
        # Record the answer
        self.user_tracker.record_adaptive_answer(user_id, is_correct, current_topic, current_difficulty)
        
        # Determine next difficulty based on current answer
        next_action = self._determine_next_adaptive_action(is_correct, current_difficulty, current_topic)
        
        result = {
            "correct": is_correct,
            "question": current_question,
            "correct_answer": current_question["correct_answer"],
            "explanation": current_question["explanation"],
            "next_action": next_action
        }
        
        # If test is complete or needs reevaluation
        if next_action["type"] in ["complete", "offer_reevaluation"]:
            self.user_tracker.update_adaptive_test_results(user_id, next_action["type"])
            return result
        
        # Get next question based on next_action
        next_topic = next_action.get("topic", current_topic)
        next_difficulty = next_action.get("difficulty")
        
        next_question = self.search_engine.get_random_question_by_topic_and_difficulty(next_topic, next_difficulty)
        
        if not next_question:
            # If no question available, try another topic or end test
            if len(session["remaining_topics"]) > 0:
                next_topic = self.user_tracker.move_to_next_adaptive_topic(user_id)
                if next_topic:
                    next_question = self.search_engine.get_random_question_by_topic_and_difficulty(next_topic, "Medium")
        
        if next_question:
            self.user_tracker.set_current_adaptive_question(user_id, next_question)
            result["next_question"] = next_question
        else:
            # End test if no more questions
            self.user_tracker.update_adaptive_test_results(user_id, "complete")
            result["next_action"] = {"type": "complete", "message": "No more questions available. Test completed."}
        
        return result

    def _determine_next_adaptive_action(self, is_correct: bool, current_difficulty: str, current_topic: str) -> Dict:
        """
        Determine the next action based on the current answer.
        
        Args:
            is_correct: Whether the answer was correct
            current_difficulty: Difficulty of the current question
            current_topic: Topic of the current question
            
        Returns:
            Dictionary with next action information
        """
        if is_correct:
            if current_difficulty == "Medium":
                return {
                    "type": "next_question",
                    "difficulty": "Hard",
                    "topic": current_topic,
                    "message": "Moving to a Hard question on the same topic."
                }
            elif current_difficulty == "Easy":
                return {
                    "type": "next_question",
                    "difficulty": "Hard",
                    "topic": current_topic,
                    "message": "Moving to a Hard question on the same topic."
                }
            elif current_difficulty == "Hard":
                # Successfully completed this topic
                return {
                    "type": "topic_complete",
                    "topic": current_topic,
                    "message": f"You have successfully completed {current_topic}. Moving to the next topic."
                }
        else:  # Incorrect answer
            if current_difficulty == "Medium":
                return {
                    "type": "next_question",
                    "difficulty": "Easy",
                    "topic": current_topic,
                    "message": "Moving to an Easy question on the same topic."
                }
            elif current_difficulty == "Easy":
                # Failed easy question - mark topic as weak and offer reevaluation
                return {
                    "type": "offer_reevaluation",
                    "topic": current_topic,
                    "message": f"❗ You seem to struggle with {current_topic}.\n\n📚 Suggested: Review class materials or slides.\n\nWould you like to take a 3-question reevaluation test now on this topic?"
                }
            elif current_difficulty == "Hard":
                # Failed hard question - soft warning
                return {
                    "type": "warning",
                    "topic": current_topic,
                    "message": f"⚠️ You answered the hard question on {current_topic} incorrectly.",
                    "difficulty": "Medium",  # Next question difficulty
                }
        
        # Default fallback
        return {
            "type": "next_question",
            "difficulty": "Medium",
            "topic": current_topic,
            "message": "Moving to the next question."
        }

    def start_reevaluation_test(self, user_id: str, topic: str) -> Dict:
        """
        Start a reevaluation test for a specific topic 
        
        Args:
            user_id: Telegram user ID
            topic: Topic to reevaluate
            
        Returns:
            Dictionary with first question or error message
        """
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}
        
        # Get questions 
        all_questions = self.search_engine.get_questions_by_topic([topic])
        
        # Separate by difficulty
        easy_questions = [q for q in all_questions if q.get("difficulty") == "Easy"]
        medium_questions = [q for q in all_questions if q.get("difficulty") == "Medium"]
        hard_questions = [q for q in all_questions if q.get("difficulty") == "Hard"]
        
        # selection: pick one from each difficulty with shuffling
        questions = []
        
        if easy_questions:
            for _ in range(5):
                random.shuffle(easy_questions)
            questions.append(random.choice(easy_questions))
        
        if medium_questions:
            for _ in range(5):
                random.shuffle(medium_questions)
            questions.append(random.choice(medium_questions))
        
        if hard_questions:
            for _ in range(5):
                random.shuffle(hard_questions)
            questions.append(random.choice(hard_questions))
        
        if not questions:
            return {"error": f"No questions available for reevaluation on {topic}."}
        
        # Final shuffle to randomize the order (Easy, Medium, Hard order is not guaranteed)
        for _ in range(3):
            random.shuffle(questions)
        
        # Start reevaluation test session
        self.user_tracker.start_test_session(user_id, f"Reevaluation: {topic}", questions)
        
        # Return first question
        return {"first_question": self.user_tracker.get_current_question(user_id)}
        
    # ===== MINI TEST METHODS =====
    
    def start_mini_test(self, user_id: str) -> Dict:
        """
        Start mini test for the user based on their weak topics.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary with first question or error message
        """
        # Check if user already has an active test
        if self.user_tracker.has_active_test(user_id):
            return {"error": "You already have an active test session. Complete it first."}
        
        # Get user's weak topics
        weak_topics = self.user_tracker.get_weak_topics(user_id)
        
        if not weak_topics:
            return {"error": "No weak topics detected. Take an exam first to identify your weak areas."}
        
        # Get questions for mini test (1 easy, 1 medium, 1 hard for each weak topic)
        questions = self.search_engine.get_questions_for_mini_test(weak_topics)
        
        if not questions:
            return {"error": "Failed to create mini test. No questions available for your weak topics."}
        
        # Start test session
        self.user_tracker.start_test_session(user_id, "Mini Test", questions)
        
        # Return first question
        return {"first_question": self.user_tracker.get_current_question(user_id)}

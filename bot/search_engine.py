"""
Search engine module for JUSTLearn Bot - SQLite version.
Handles embeddings and question retrieval using FAISS and SQLite.
Maintains 100% functionality while switching from JSON to SQLite.
"""
import json
import random
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Optional, Any
from database.database_manager import DatabaseManager

class SearchEngine:
    def __init__(self, db_path: str = 'data/justlearn.db', index_path: str = None):
        """
        Initialize the search engine with SQLite database and embeddings.
        
        Args:
            db_path: Path to the SQLite database file
            index_path: Optional path to save/load the FAISS index
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db_manager = DatabaseManager(db_path)
        self.mcqs = self.db_manager.load_mcqs()
        self.topic_to_questions = self._group_by_topic()
        self.difficulty_mapping = self._get_standardized_difficulty_mapping()
        
        # Create or load index
        if index_path and self._index_exists(index_path):
            self.index, self.question_ids = self._load_index(index_path)
        else:
            self.index, self.question_ids = self._build_index()
            if index_path:
                self._save_index(index_path)
    
    def _group_by_topic(self) -> Dict[str, List[int]]:
        """Group question indices by topic for easy topic-based retrieval."""
        topic_dict = {}
        for i, mcq in enumerate(self.mcqs):
            topic = mcq['topic']
            if topic not in topic_dict:
                topic_dict[topic] = []
            topic_dict[topic].append(i)
        return topic_dict
    
    def _index_exists(self, index_path: str) -> bool:
        """Check if a FAISS index file exists."""
        try:
            with open(index_path, 'rb'):
                return True
        except FileNotFoundError:
            return False
    
    def _build_index(self) -> Tuple[faiss.IndexFlatL2, List[int]]:
        """Build a FAISS index from MCQs."""
        # Extract questions for embedding
        questions = [mcq['question'] for mcq in self.mcqs]
        question_ids = list(range(len(questions)))
        
        # Generate embeddings
        embeddings = self.model.encode(questions)
        
        # Normalize embeddings (recommended for cosine similarity)
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings).astype('float32'))
        
        return index, question_ids
    
    def _save_index(self, index_path: str) -> None:
        """Save the FAISS index to disk."""
        faiss.write_index(self.index, index_path)
        # Save question_ids alongside the index
        with open(index_path + '.ids', 'w') as f:
            json.dump(self.question_ids, f)
    
    def _load_index(self, index_path: str) -> Tuple[faiss.IndexFlatL2, List[int]]:
        """Load the FAISS index from disk."""
        index = faiss.read_index(index_path)
        # Load question_ids
        with open(index_path + '.ids', 'r') as f:
            question_ids = json.load(f)
        return index, question_ids

    def get_standardized_topic_mapping(self) -> Dict[str, List[str]]:
        """Get standardized mapping of topics to their variations."""
        return {
            "Algorithm Analysis and Big-O Notation": ["Big-O", "Algorithm Analysis", "Algorithmic Analysis", "Big O", "Big-O Notation"],
            "Array-Based Lists": ["Arrays", "Array", "Array-Based", "Array Based Lists"],
            "Linked Lists": ["Linked List", "LinkedList", "LinkedLists"],
            "Stacks": ["Stack"],
            "Queues": ["Queue"],
            "Recursion": ["Recursive"],
            "Searching and Hashing": ["Hashing", "Hash", "Search", "Searching"],
            "Binary Trees": ["Tree", "Trees", "Binary Tree"],
            "Graphs": ["Graph"],
            "Sorting Algorithms": ["Sorting", "Sort Algorithms", "Sort"]
        }
    
    def _get_standardized_difficulty_mapping(self) -> Dict[str, str]:
        """Get standardized mapping of difficulty levels."""
        return {
            "easy": "Easy",
            "medium": "Medium", 
            "med": "Medium",
            "hard": "Hard"
        }
    
    def get_all_topics(self) -> List[str]:
        """Get all available topics from the database."""
        return self.db_manager.get_all_topics()
    
    def search_by_query(self, query: str, top_k: int = 1) -> List[Dict]:
        """
        Search for questions similar to the query.
        
        Args:
            query: User query text
            top_k: Number of results to return
            
        Returns:
            List of matching MCQ dictionaries
        """
        # Encode the query
        query_embedding = self.model.encode([query])
        
        # Normalize query embedding for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search for similar questions
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return empty list if no good match (distance threshold)
        if len(indices[0]) == 0 or distances[0][0] > 0.8:  # Adjust threshold as needed
            return []
        
        # Return the matching MCQs
        return [self.mcqs[self.question_ids[idx]] for idx in indices[0]]
    
    def get_questions_by_topic(self, topics: List[str], difficulty: str = None, 
                              count: int = None, exclude_topics: List[str] = None) -> List[Dict]:
        """
        Get questions from specified topics with balanced distribution.
        
        Args:
            topics: List of topics to include
            difficulty: Optional difficulty filter
            count: Optional number of questions to return
            exclude_topics: Optional list of topics to exclude
            
        Returns:
            List of matching MCQ dictionaries
        """
        # Include topic variations using the standardized mapping
        topic_mapping = self.get_standardized_topic_mapping()
        expanded_topics = []
        for topic in topics:
            expanded_topics.append(topic)
            # Add variations if they exist
            for main_topic, variations in topic_mapping.items():
                if topic == main_topic or topic in variations:
                    expanded_topics.extend(variations)
                    expanded_topics.append(main_topic)
        
        # Remove duplicates
        expanded_topics = list(set(expanded_topics))
        
        # Filter out excluded topics
        if exclude_topics:
            expanded_topics = [t for t in expanded_topics if t not in exclude_topics 
                             and not any(t.lower() == et.lower() for et in exclude_topics)]
        
        # Get MCQs from database
        if difficulty:
            std_difficulty = self.difficulty_mapping.get(difficulty.lower(), difficulty)
            mcqs = self.db_manager.get_mcqs_by_topic_and_difficulty(expanded_topics, std_difficulty)
        else:
            mcqs = self.db_manager.get_mcqs_by_topic_and_difficulty(expanded_topics)
        
        # Special handling for balanced distribution if count is provided
        if count and count > 0:
            result = self._get_balanced_questions_from_list(mcqs, expanded_topics, count, difficulty)
            
            # CRITICAL FIX: Ensure we reach the target count
            if len(result) < count and mcqs:
                # Remove duplicates first
                unique_results = []
                question_ids = set()
                for question in result:
                    question_id = question['question'][:50]
                    if question_id not in question_ids:
                        question_ids.add(question_id)
                        unique_results.append(question)
                
                # If still need more questions, add from remaining MCQs
                remaining_mcqs = [q for q in mcqs if q['question'][:50] not in question_ids]
                if remaining_mcqs:
                    # Shuffle remaining questions
                    for _ in range(5):
                        random.shuffle(remaining_mcqs)
                    
                    # Add questions until we reach target count
                    needed = count - len(unique_results)
                    if len(remaining_mcqs) >= needed:
                        unique_results.extend(remaining_mcqs[:needed])
                    else:
                        unique_results.extend(remaining_mcqs)
                        
                        # If still not enough, allow some duplicates as last resort
                        if len(unique_results) < count:
                            all_available = mcqs.copy()
                            for _ in range(10):  # More aggressive shuffling
                                random.shuffle(all_available)
                            
                            # Add more questions, allowing duplicates if absolutely necessary
                            still_needed = count - len(unique_results)
                            unique_results.extend(all_available[:still_needed])
                
                # Final shuffle
                for _ in range(5):
                    random.shuffle(unique_results)
                
                return unique_results[:count]  # Ensure exact count
            
            return result
            
        # Shuffle questions for randomization
        random.shuffle(mcqs)
        
        # Remove duplicates (in case same question appears in multiple topics)
        unique_results = []
        question_ids = set()
        for question in mcqs:
            # Create a unique ID using question text to identify duplicates
            question_id = question['question'][:50]  # Use first 50 chars as ID
            if question_id not in question_ids:
                question_ids.add(question_id)
                unique_results.append(question)
                
        return unique_results
        
    def _get_balanced_questions_from_list(self, mcqs: List[Dict], topics: List[str], count: int, 
                                        difficulty: Optional[str] = None) -> List[Dict]:
        """
        Get a balanced set of questions from the provided MCQ list.
        
        Args:
            mcqs: List of MCQs to balance
            topics: List of topics
            count: Number of questions to return
            difficulty: Optional difficulty filter
            
        Returns:
            List of balanced MCQ dictionaries
        """
        # Group questions by topic
        topic_questions = {}
        for mcq in mcqs:
            topic = mcq['topic']
            if topic not in topic_questions:
                topic_questions[topic] = []
            topic_questions[topic].append(mcq)
        
        # Calculate questions per topic
        unique_topics = list(topic_questions.keys())
        if not unique_topics:
            return []
            
        questions_per_topic = max(1, count // len(unique_topics))
        remaining = count - (questions_per_topic * len(unique_topics))
        
        result = []
        
        # Collect questions by topic with proper distribution
        for i, topic in enumerate(unique_topics):
            topic_mcqs = topic_questions[topic]
            
            if not difficulty:
                # Balance difficulties if no specific difficulty requested
                by_difficulty = {
                    "Easy": [q for q in topic_mcqs if q['difficulty'] == "Easy"],
                    "Medium": [q for q in topic_mcqs if q['difficulty'] == "Medium"],
                    "Hard": [q for q in topic_mcqs if q['difficulty'] == "Hard"]
                }
                
                # Calculate per difficulty
                current_count = questions_per_topic
                if i < remaining:  # Add remaining to first topics
                    current_count += 1
                    
                questions_per_difficulty = current_count // 3
                extra = current_count - (questions_per_difficulty * 3)
                
                # Collect balanced by difficulty
                balanced_questions = []
                for j, (diff, questions) in enumerate(by_difficulty.items()):
                    if questions:  # If we have questions of this difficulty
                        # Take random sample, or all if not enough
                        sample_count = questions_per_difficulty
                        if j == 1:  # Give any extras to Medium difficulty
                            sample_count += extra
                            
                        if len(questions) <= sample_count:
                            balanced_questions.extend(questions)
                        else:
                            balanced_questions.extend(random.sample(questions, sample_count))
                
                # Shuffle to randomize order
                random.shuffle(balanced_questions)
                result.extend(balanced_questions)
            else:
                # Shuffle to randomize order
                random.shuffle(topic_mcqs)
                
                # Add to result
                current_count = questions_per_topic
                if i < remaining:  # Add remaining to first topics
                    current_count += 1
                    
                if len(topic_mcqs) <= current_count:
                    result.extend(topic_mcqs)
                else:
                    result.extend(topic_mcqs[:current_count])
        
        # CRITICAL FIX: If we don't have enough questions, try to fill remaining slots
        if len(result) < count:
            # Get all unused questions
            used_question_ids = {q['question'][:50] for q in result}
            unused_questions = [q for q in mcqs if q['question'][:50] not in used_question_ids]
            
            if unused_questions:
                # Shuffle unused questions
                for _ in range(5):
                    random.shuffle(unused_questions)
                
                # Add questions to reach target count
                needed = count - len(result)
                result.extend(unused_questions[:needed])
        
        # Shuffle final result for randomization
        random.shuffle(result)
        
        # Remove duplicates
        unique_results = []
        question_ids = set()
        for question in result:
            # Create a unique ID using question text to identify duplicates
            question_id = question['question'][:50]  # Use first 50 chars as ID
            if question_id not in question_ids:
                question_ids.add(question_id)
                unique_results.append(question)
        
        return unique_results
    
    def get_random_question_by_topic_and_difficulty(self, topic: str, difficulty: str) -> Optional[Dict]:
        """Get a random question with the specified topic and difficulty."""
        # Standardize difficulty
        std_difficulty = self.difficulty_mapping.get(difficulty.lower(), difficulty)
        
        # Try exact match first
        matching_questions = [
            q for q in self.mcqs 
            if q.get("topic", "") == topic and q.get("difficulty", "") == std_difficulty
        ]
        
        # If no exact match, try known variations
        if not matching_questions:
            topic_mapping = self.get_standardized_topic_mapping()
            for main_topic, variations in topic_mapping.items():
                if topic == main_topic or topic in variations:
                    for variation in [main_topic] + variations:
                        new_matches = [
                            q for q in self.mcqs 
                            if q.get("topic", "") == variation and q.get("difficulty", "") == std_difficulty
                        ]
                        matching_questions.extend(new_matches)
        
        # If still no match, try case-insensitive partial matching
        if not matching_questions:
            matching_questions = [
                q for q in self.mcqs 
                if (topic.lower() in q.get("topic", "").lower() and 
                    std_difficulty.lower() in q.get("difficulty", "").lower())
            ]
        
        # Last resort: try with any difficulty if the topic matches
        if not matching_questions:
            for main_topic, variations in self.get_standardized_topic_mapping().items():
                if topic == main_topic or topic in variations:
                    for variation in [main_topic] + variations:
                        alt_questions = [
                            q for q in self.mcqs 
                            if q.get("topic", "") == variation
                        ]
                        if alt_questions:
                            # Sort by difficulty preference: Medium, Easy, Hard
                            difficulty_order = {"Medium": 1, "Easy": 2, "Hard": 3}
                            alt_questions.sort(key=lambda q: difficulty_order.get(q.get("difficulty", ""), 4))
                            return alt_questions[0]
        
        if not matching_questions:
            return None
        
        return random.choice(matching_questions)
    
    def get_questions_for_mini_test(self, weak_topics: List[str]) -> List[Dict]:
        """
        Generate questions for a mini test based on weak topics.
        For each weak topic, get one easy, one medium, and one hard question.
        
        Args:
            weak_topics: List of topics the student is weak in
            
        Returns:
            List of MCQs for the mini test
        """
        result = []
        
        for topic in weak_topics:
            # Try to get one question of each difficulty
            for difficulty in ['Easy', 'Medium', 'Hard']:
                question = self.get_random_question_by_topic_and_difficulty(topic, difficulty)
                if question:
                    result.append(question)
        
        # Shuffle for randomization
        random.shuffle(result)
        
        return result
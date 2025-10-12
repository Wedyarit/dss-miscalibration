from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.crud import create_user, create_item, create_session, create_interaction
from app.core.security import verify_api_key
from typing import List
import json
import random
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/seed")
async def seed_database(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Seed database with demo data"""
    
    try:
        # Create demo users
        users = []
        for role in ['student', 'instructor', 'admin']:
            for i in range(3):
                user = create_user(db, role)
                users.append(user)
        
        # Create demo questions
        questions_data = [
            # Math questions
            {
                "stem": "What is 15% of 200?",
                "options": ["30", "25", "35", "40"],
                "correct": 0,
                "tags": ["math", "percentage"],
                "difficulty": 3.0
            },
            {
                "stem": "Solve: 2x + 5 = 13",
                "options": ["x = 4", "x = 3", "x = 5", "x = 6"],
                "correct": 0,
                "tags": ["math", "algebra"],
                "difficulty": 4.0
            },
            {
                "stem": "What is the area of a circle with radius 5?",
                "options": ["25π", "10π", "50π", "5π"],
                "correct": 0,
                "tags": ["math", "geometry"],
                "difficulty": 5.0
            },
            {
                "stem": "Convert 0.75 to a fraction",
                "options": ["3/4", "1/4", "2/3", "4/5"],
                "correct": 0,
                "tags": ["math", "fractions"],
                "difficulty": 2.0
            },
            {
                "stem": "What is 7 × 8?",
                "options": ["56", "54", "58", "64"],
                "correct": 0,
                "tags": ["math", "arithmetic"],
                "difficulty": 1.0
            },
            
            # Logic questions
            {
                "stem": "If all birds can fly and penguins are birds, can penguins fly?",
                "options": ["Yes", "No", "Sometimes", "Depends on the penguin"],
                "correct": 1,
                "tags": ["logic", "reasoning"],
                "difficulty": 4.0
            },
            {
                "stem": "What comes next: 2, 4, 8, 16, ?",
                "options": ["24", "32", "20", "28"],
                "correct": 1,
                "tags": ["logic", "pattern"],
                "difficulty": 3.0
            },
            {
                "stem": "If A > B and B > C, then:",
                "options": ["A > C", "A < C", "A = C", "Cannot determine"],
                "correct": 0,
                "tags": ["logic", "inequality"],
                "difficulty": 3.0
            },
            
            # Computer Science questions
            {
                "stem": "What is the time complexity of binary search?",
                "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
                "correct": 1,
                "tags": ["cs", "algorithms"],
                "difficulty": 6.0
            },
            {
                "stem": "Which data structure uses LIFO principle?",
                "options": ["Queue", "Stack", "Array", "Tree"],
                "correct": 1,
                "tags": ["cs", "data-structures"],
                "difficulty": 4.0
            },
            {
                "stem": "What does HTTP stand for?",
                "options": ["HyperText Transfer Protocol", "High Transfer Text Protocol", "Hyper Transfer Text Protocol", "High Text Transfer Protocol"],
                "correct": 0,
                "tags": ["cs", "networking"],
                "difficulty": 2.0
            },
            
            # Reading comprehension
            {
                "stem": "According to the passage, photosynthesis is:",
                "options": ["The process by which plants convert sunlight into energy", "The process by which animals digest food", "The process by which water evaporates", "The process by which rocks form"],
                "correct": 0,
                "tags": ["reading", "science"],
                "difficulty": 3.0
            },
            {
                "stem": "The main idea of the text is:",
                "options": ["Technology is always beneficial", "Technology has both benefits and drawbacks", "Technology should be avoided", "Technology is too complex"],
                "correct": 1,
                "tags": ["reading", "comprehension"],
                "difficulty": 4.0
            },
            
            # General knowledge
            {
                "stem": "What is the capital of France?",
                "options": ["London", "Paris", "Berlin", "Madrid"],
                "correct": 1,
                "tags": ["gk", "geography"],
                "difficulty": 1.0
            },
            {
                "stem": "Who wrote 'Romeo and Juliet'?",
                "options": ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"],
                "correct": 1,
                "tags": ["gk", "literature"],
                "difficulty": 2.0
            },
            {
                "stem": "What is the chemical symbol for gold?",
                "options": ["Go", "Gd", "Au", "Ag"],
                "correct": 2,
                "tags": ["gk", "chemistry"],
                "difficulty": 3.0
            }
        ]
        
        items = []
        for q_data in questions_data:
            item = create_item(
                db=db,
                stem_en=q_data["stem"],
                options_en=q_data["options"],
                stem_ru=None,  # No Russian translation for demo data
                options_ru=None,
                correct_option=q_data["correct"],
                tags_en=q_data["tags"],
                tags_ru=None,
                difficulty_hint=q_data["difficulty"]
            )
            items.append(item)
        
        # Create demo sessions and interactions
        student_users = [u for u in users if u.role == 'student']
        sessions_created = 0
        interactions_created = 0
        
        for user in student_users:
            # Create 2-3 sessions per student
            for session_num in range(random.randint(2, 3)):
                mode = random.choice(['standard', 'self_confidence'])
                session = create_session(db, user.id, mode)
                sessions_created += 1
                
                # Create 5-15 interactions per session
                session_items = random.sample(items, random.randint(5, min(15, len(items))))
                
                for item in session_items:
                    # Simulate realistic interaction patterns
                    options = json.loads(item.options_en_json)
                    chosen_option = random.randint(0, len(options) - 1)
                    
                    # Base correctness on difficulty and some randomness
                    difficulty_factor = item.difficulty_hint or 5.0
                    correctness_prob = max(0.1, min(0.9, 1.0 - (difficulty_factor - 3.0) / 10.0))
                    is_correct = random.random() < correctness_prob
                    
                    # If incorrect, choose wrong option
                    if not is_correct:
                        correct_option = item.correct_option
                        wrong_options = [i for i in range(len(options)) if i != correct_option]
                        chosen_option = random.choice(wrong_options)
                    
                    # Generate confidence (higher for correct answers, but with some noise)
                    if mode == 'self_confidence':
                        base_confidence = 0.7 if is_correct else 0.4
                        confidence_noise = random.uniform(-0.2, 0.2)
                        confidence = max(0.0, min(1.0, base_confidence + confidence_noise))
                    else:
                        confidence = random.random() if random.random() < 0.3 else None  # 30% chance of confidence in standard mode
                    
                    # Response time based on difficulty and confidence
                    base_time = 2000 + (difficulty_factor * 500)
                    if confidence and confidence > 0.8:
                        base_time *= 0.7  # Faster for high confidence
                    elif confidence and confidence < 0.3:
                        base_time *= 1.3  # Slower for low confidence
                    
                    response_time = int(base_time + random.uniform(-500, 1000))
                    
                    create_interaction(
                        db=db,
                        session_id=session.id,
                        user_id=user.id,
                        item_id=item.id,
                        chosen_option=chosen_option,
                        is_correct=is_correct,
                        confidence=confidence,
                        response_time_ms=response_time,
                        attempts_count=1
                    )
                    interactions_created += 1
        
        return {
            "message": "Database seeded successfully",
            "users_created": len(users),
            "questions_created": len(items),
            "sessions_created": sessions_created,
            "interactions_created": interactions_created
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")

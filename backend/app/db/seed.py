from app.db.base import create_tables
from app.db.crud import create_user
from app.db.session import SessionLocal
from app.db.models import User

def init_database():
    """Initialize database with tables and demo users"""
    # Create tables
    engine = create_tables()
    
    # Create demo users
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users == 0:
            # Create demo users
            create_user(db, "student")
            create_user(db, "student") 
            create_user(db, "student")
            create_user(db, "instructor")
            create_user(db, "instructor")
            create_user(db, "admin")
            print("Demo users created successfully")
        else:
            print(f"Database already has {existing_users} users")
    except Exception as e:
        print(f"Error creating demo users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()

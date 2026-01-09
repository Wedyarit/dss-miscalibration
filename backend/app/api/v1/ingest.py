from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verify_api_key
from app.db.models import User, Session as DBSession, Interaction, Item
from sqlalchemy import func

router = APIRouter()

@router.post("/seed")
async def seed_database(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Seed database with human-like interaction data using seed_interactions_humanlike"""

    try:
        from app.db.seed_interactions_humanlike import main as seed_humanlike
        from app.db.seed_questions import seed_questions

        seed_questions()

        # Store counts before seeding
        users_before = db.query(func.count(User.id)).scalar() or 0
        sessions_before = db.query(func.count(DBSession.id)).scalar() or 0
        interactions_before = db.query(func.count(Interaction.id)).scalar() or 0
        items_before = db.query(func.count(Item.id)).scalar() or 0

        seed_humanlike()

        updated_calib = db.query(DBSession).filter(
            DBSession.mode == 'self_confidence',
            DBSession.purpose != 'calibration'
        ).update({'purpose': 'calibration'}, synchronize_session=False)

        updated_real = db.query(DBSession).filter(
            DBSession.mode == 'standard',
            DBSession.purpose != 'real'
        ).update({'purpose': 'real'}, synchronize_session=False)

        db.commit()

        db.expire_all()

        users_after = db.query(func.count(User.id)).scalar() or 0
        sessions_after = db.query(func.count(DBSession.id)).scalar() or 0
        interactions_after = db.query(func.count(Interaction.id)).scalar() or 0
        items_after = db.query(func.count(Item.id)).scalar() or 0

        return {
            "message": "Database seeded successfully with human-like interactions",
            "users_created": users_after - users_before,
            "questions_created": items_after - items_before,
            "sessions_created": sessions_after - sessions_before,
            "interactions_created": interactions_after - interactions_before,
            "purpose_fixed": {
                "calibration_sessions": updated_calib,
                "real_sessions": updated_real
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")

from app import app
from models import db, ActivityTemplate
from datetime import datetime

def seed_database():
    with app.app_context():
        # Clear existing templates
        ActivityTemplate.query.delete()
        
        # Create sample activity templates
        templates = [
            ActivityTemplate(
                name="Watercolor Painting Workshop",
                description="Learn the basics of watercolor painting with professional artists. Perfect for beginners!",
                category="art_activity",
                default_duration=120,
                default_price=45.00,
                default_max_participants=10,
                is_active=True
            ),
            ActivityTemplate(
                name="Oil Painting Masterclass",
                description="Advanced oil painting techniques for experienced artists.",
                category="art_activity",
                default_duration=180,
                default_price=75.00,
                default_max_participants=8,
                is_active=True
            ),
            ActivityTemplate(
                name="Portrait Drawing Session",
                description="One-on-one portrait drawing session with a professional artist.",
                category="art_session",
                default_duration=90,
                default_price=60.00,
                default_max_participants=1,
                is_active=True
            ),
            ActivityTemplate(
                name="Landscape Photography Walk",
                description="Guided photography walk through scenic locations.",
                category="art_activity",
                default_duration=150,
                default_price=40.00,
                default_max_participants=12,
                is_active=True
            ),
            ActivityTemplate(
                name="Abstract Art Exhibition",
                description="Monthly exhibition showcasing local abstract artists.",
                category="event",
                default_duration=240,
                default_price=15.00,
                default_max_participants=50,
                is_active=True
            ),
            ActivityTemplate(
                name="Sculpture Workshop",
                description="Hands-on sculpture creation using clay and other materials.",
                category="art_activity",
                default_duration=180,
                default_price=55.00,
                default_max_participants=10,
                is_active=True
            ),
            ActivityTemplate(
                name="Digital Art Fundamentals",
                description="Introduction to digital art using tablets and software.",
                category="art_session",
                default_duration=120,
                default_price=50.00,
                default_max_participants=6,
                is_active=True
            ),
            ActivityTemplate(
                name="Art Gallery Opening Night",
                description="Exclusive gallery opening with wine and networking.",
                category="event",
                default_duration=180,
                default_price=25.00,
                default_max_participants=100,
                is_active=True
            )
        ]
        
        for template in templates:
            db.session.add(template)
        
        db.session.commit()
        print(f"✅ Successfully added {len(templates)} activity templates!")

if __name__ == "__main__":
    seed_database()
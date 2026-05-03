from app import app
from models import db, User, Reservation, ClientNote, Notification, ActivityTemplate

def reset_database():
    """Complete database reset - removes all data"""
    with app.app_context():
        print("\n" + "="*50)
        print("🗑️  DATABASE RESET")
        print("="*50 + "\n")
        
        # Ask for confirmation
        confirm = input("⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Reset cancelled.")
            return
        
        print("\n🔄 Resetting database...\n")
        
        # Count current records
        print("📊 Current database status:")
        print(f"   Users: {User.query.count()}")
        print(f"   Reservations: {Reservation.query.count()}")
        print(f"   Templates: {ActivityTemplate.query.count()}")
        print(f"   Notes: {ClientNote.query.count()}")
        print(f"   Notifications: {Notification.query.count()}")
        print()
        
        # Delete all data
        try:
            print("🗑️  Deleting all records...")
            Notification.query.delete()
            print("   ✓ Notifications cleared")
            
            ClientNote.query.delete()
            print("   ✓ Client notes cleared")
            
            Reservation.query.delete()
            print("   ✓ Reservations cleared")
            
            ActivityTemplate.query.delete()
            print("   ✓ Templates cleared")
            
            User.query.delete()
            print("   ✓ Users cleared")
            
            db.session.commit()
            print("\n✅ Database completely reset!")
            print("📝 All data has been removed.\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error resetting database: {e}\n")

if __name__ == "__main__":
    reset_database()
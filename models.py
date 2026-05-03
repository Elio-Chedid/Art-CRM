from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    profile_pic = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    is_owner = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='client', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('ClientNote', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Reservation Type: 'art_activity', 'art_session', 'event'
    reservation_type = db.Column(db.String(50), nullable=False)
    
    # Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in minutes
    
    # Capacity (for activities and events)
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=1)
    
    # Pricing
    price = db.Column(db.Float, default=0.0)
    
    # Status: 'pending', 'confirmed', 'cancelled', 'completed'
    status = db.Column(db.String(20), default='pending')
    
    # Additional fields
    location = db.Column(db.String(200))
    materials_needed = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Payment
    payment_status = db.Column(db.String(20), default='unpaid')  # 'unpaid', 'paid', 'refunded'
    payment_method = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Reservation {self.title}>'

class ClientNote(db.Model):
    __tablename__ = 'client_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))  # Owner who created the note
    
    def __repr__(self):
        return f'<ClientNote for User {self.user_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # 'new_reservation', 'cancellation', 'update'
    is_read = db.Column(db.Boolean, default=False)
    related_reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class ActivityTemplate(db.Model):
    __tablename__ = 'activity_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'art_activity', 'art_session', 'event'
    default_duration = db.Column(db.Integer)
    default_price = db.Column(db.Float)
    default_max_participants = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<ActivityTemplate {self.name}>'
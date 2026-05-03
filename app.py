from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Reservation, ClientNote, Notification, ActivityTemplate
from config import Config
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from functools import wraps
import json
from google.oauth2 import id_token
from google.auth.transport import requests
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Owner required decorator
def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_owner:
            flash('You need owner privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Email notification function
def send_email_notification(subject, recipient, body_html):
    try:
        msg = Message(subject, recipients=[recipient])
        msg.html = body_html
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Create notification
def create_notification(title, message, notification_type, reservation_id=None):
    notification = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        related_reservation_id=reservation_id
    )
    db.session.add(notification)
    db.session.commit()

def send_reservation_confirmation_email(reservation):
    """Send confirmation email to client when reservation is created"""
    try:
        client = reservation.client
        subject = f"🎨 Reservation Confirmed: {reservation.title}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 20px;
                    border-radius: 15px;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    color: #667eea;
                    border-bottom: 3px solid #f093fb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .detail-row {{
                    padding: 10px;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #667eea;
                    display: inline-block;
                    width: 150px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 8px 20px;
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    border-radius: 20px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: 600;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #f0f0f0;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <div class="header">
                        <h1>🎨 Reservation Confirmed!</h1>
                        <p>Thank you for booking with Art CRM</p>
                    </div>
                    
                    <p>Dear {client.name},</p>
                    <p>Your reservation has been successfully created. Here are the details:</p>
                    
                    <div class="status-badge">Status: {reservation.status.upper()}</div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📅 Reservation:</span>
                        <span>{reservation.title}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📋 Type:</span>
                        <span>{reservation.reservation_type.replace('_', ' ').title()}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📆 Date:</span>
                        <span>{reservation.date.strftime('%B %d, %Y')}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">🕐 Time:</span>
                        <span>{reservation.date.strftime('%I:%M %p')}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">⏱️ Duration:</span>
                        <span>{reservation.duration} minutes</span>
                    </div>
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">📍 Location:</span>
                        <span>{reservation.location}</span>
                    </div>''' if reservation.location else ''}
                    {f'''<div class="detail-row">
    <span class="detail-label">📞 Phone:</span>
    <span>{client.phone}</span>
</div>''' if client.phone else ''}
                    {f'''<div class="detail-row">
                        <span class="detail-label">💰 Price:</span>
                        <span>${reservation.price:.2f}</span>
                    </div>''' if reservation.price > 0 else ''}
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">💳 Payment Status:</span>
                        <span>{reservation.payment_status.title()}</span>
                    </div>''' if reservation.price > 0 else ''}
                    
                    {f'''<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea;">
                        <strong>📝 Description:</strong><br>
                        {reservation.description}
                    </div>''' if reservation.description else ''}
                    
                    {f'''<div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Special Requirements:</strong><br>
                        {reservation.special_requirements}
                    </div>''' if reservation.special_requirements else ''}
                    
                    <div class="footer">
                        <p>If you have any questions, please don't hesitate to contact us.</p>
                        <p><strong>Art CRM Team</strong></p>
                        <p style="font-size: 12px; color: #999;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_email_notification(subject, client.email, body_html)
        print(f"✅ Confirmation email sent to {client.email}")
        return True
    except Exception as e:
        print(f"❌ Error sending confirmation email: {e}")
        return False

def send_status_change_email(reservation, old_status, new_status):
    """Send email to client when reservation status changes"""
    try:
        client = reservation.client
        
        # Define status colors and icons
        status_info = {
            'pending': {'color': '#ffc107', 'icon': '⏳', 'message': 'Your reservation is pending confirmation.'},
            'confirmed': {'color': '#28a745', 'icon': '✅', 'message': 'Great news! Your reservation has been confirmed.'},
            'completed': {'color': '#17a2b8', 'icon': '✔️', 'message': 'Thank you for joining us! Your reservation is now complete.'},
            'cancelled': {'color': '#dc3545', 'icon': '❌', 'message': 'Your reservation has been cancelled.'}
        }
        
        info = status_info.get(new_status, {'color': '#6c757d', 'icon': '📋', 'message': f'Status updated to {new_status}.'})
        
        subject = f"{info['icon']} Reservation Status Update: {reservation.title}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 20px;
                    border-radius: 15px;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    color: #667eea;
                    border-bottom: 3px solid #f093fb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .status-change {{
                    text-align: center;
                    padding: 20px;
                    background: {info['color']};
                    color: white;
                    border-radius: 10px;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: 600;
                }}
                .detail-row {{
                    padding: 10px;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #667eea;
                    display: inline-block;
                    width: 150px;
                }}
                .old-status {{
                    text-decoration: line-through;
                    color: #999;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #f0f0f0;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <div class="header">
                        <h1>{info['icon']} Status Update</h1>
                        <p>Your reservation status has changed</p>
                    </div>
                    
                    <p>Dear {client.name},</p>
                    <p>{info['message']}</p>
                    
                    <div class="status-change">
                        <div style="margin-bottom: 10px;">
                            Status Changed: <span class="old-status">{old_status.upper()}</span> → <strong>{new_status.upper()}</strong>
                        </div>
                    </div>
                    
                    <h3 style="color: #667eea; margin-top: 30px;">Reservation Details:</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">📅 Reservation:</span>
                        <span>{reservation.title}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📆 Date:</span>
                        <span>{reservation.date.strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">📍 Location:</span>
                        <span>{reservation.location}</span>
                    </div>''' if reservation.location else ''}
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">💰 Price:</span>
                        <span>${reservation.price:.2f}</span>
                    </div>''' if reservation.price > 0 else ''}
                    
                    {'''<div style="margin-top: 20px; padding: 15px; background: #d4edda; border-left: 4px solid #28a745;">
                        <strong>✅ What's Next?</strong><br>
                        We look forward to seeing you! Please arrive 10 minutes early.
                    </div>''' if new_status == 'confirmed' else ''}
                    
                    {'''<div style="margin-top: 20px; padding: 15px; background: #f8d7da; border-left: 4px solid #dc3545;">
                        <strong>ℹ️ Cancellation Notice</strong><br>
                        If you have any questions about this cancellation, please contact us.
                    </div>''' if new_status == 'cancelled' else ''}
                    
                    <div class="footer">
                        <p>If you have any questions, please don't hesitate to contact us.</p>
                        <p><strong>Art CRM Team</strong></p>
                        <p style="font-size: 12px; color: #999;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_email_notification(subject, client.email, body_html)
        print(f"✅ Status change email sent to {client.email} ({old_status} → {new_status})")
        return True
    except Exception as e:
        print(f"❌ Error sending status change email: {e}")
        return False

def send_owner_notification_email(reservation):
    """Send notification email to owner when new reservation is created"""
    if not app.config.get('OWNER_EMAIL'):
        print("⚠️ OWNER_EMAIL not configured")
        return False
    
    try:
        subject = f"🎨 New Reservation: {reservation.title}"
        
        body_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 40px 20px;
                    border-radius: 15px;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    color: #667eea;
                    border-bottom: 3px solid #f093fb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .alert {{
                    padding: 15px;
                    background: #d1ecf1;
                    border-left: 4px solid #0c5460;
                    margin: 20px 0;
                }}
                .detail-row {{
                    padding: 10px;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #667eea;
                    display: inline-block;
                    width: 150px;
                }}
                .btn {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <div class="header">
                        <h1>🎨 New Reservation Alert!</h1>
                        <p>A new reservation has been created</p>
                    </div>
                    
                    <div class="alert">
                        <strong>⚡ Action Required:</strong> A new reservation is pending your review.
                    </div>
                    
                    <h3 style="color: #667eea;">Client Information:</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">👤 Name:</span>
                        <span>{reservation.client.name}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📧 Email:</span>
                        <span>{reservation.client.email}</span>
                    </div>
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">📞 Phone:</span>
                        <span>{reservation.client.phone}</span>
                    </div>''' if reservation.client.phone else ''}
                    
                    <h3 style="color: #667eea; margin-top: 30px;">Reservation Details:</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">📅 Title:</span>
                        <span><strong>{reservation.title}</strong></span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📋 Type:</span>
                        <span>{reservation.reservation_type.replace('_', ' ').title()}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">📆 Date:</span>
                        <span>{reservation.date.strftime('%B %d, %Y')}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">🕐 Time:</span>
                        <span>{reservation.date.strftime('%I:%M %p')}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">⏱️ Duration:</span>
                        <span>{reservation.duration} minutes</span>
                    </div>
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">💰 Price:</span>
                        <span><strong>${reservation.price:.2f}</strong></span>
                    </div>''' if reservation.price > 0 else ''}
                    
                    {f'''<div class="detail-row">
                        <span class="detail-label">📍 Location:</span>
                        <span>{reservation.location}</span>
                    </div>''' if reservation.location else ''}
                    
                    {f'''<div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea;">
                        <strong>📝 Description:</strong><br>
                        {reservation.description}
                    </div>''' if reservation.description else ''}
                    
                    {f'''<div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Special Requirements:</strong><br>
                        {reservation.special_requirements}
                    </div>''' if reservation.special_requirements else ''}
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{url_for('owner_reservations', _external=True)}" class="btn">
                            View in Dashboard →
                        </a>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f0f0f0; color: #666; font-size: 14px;">
                        <p><strong>Art CRM</strong> - Reservation Management System</p>
                        <p style="font-size: 12px; color: #999;">
                            Reservation ID: #{reservation.id} | Created: {reservation.created_at.strftime('%B %d, %Y at %I:%M %p')}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_email_notification(subject, app.config['OWNER_EMAIL'], body_html)
        print(f"✅ Owner notification email sent to {app.config['OWNER_EMAIL']}")
        return True
    except Exception as e:
        print(f"❌ Error sending owner notification email: {e}")
        return False
# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_owner:
            return redirect(url_for('owner_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    
    templates = ActivityTemplate.query.filter_by(is_active=True).limit(6).all()
    return render_template('index.html', templates=templates)


@app.route('/test-template')
def test_template():
    return render_template('index.html', templates=[])
@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html', 
                         google_client_id=app.config['GOOGLE_CLIENT_ID'])

@app.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        token = request.json.get('token')
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            app.config['GOOGLE_CLIENT_ID']
        )
        
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        
        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
                user.profile_pic = picture
            else:
                # Create new user
                user = User(
                    google_id=google_id,
                    email=email,
                    name=name,
                    profile_pic=picture,
                    is_owner=(email == app.config['OWNER_EMAIL'])
                )
                db.session.add(user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'success': True,
            'redirect': url_for('owner_dashboard' if user.is_owner else 'client_dashboard')
        })
        
    except Exception as e:
        print(f"Error in Google auth: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# Client Routes
@app.route('/client/dashboard')
@login_required
def client_dashboard():
    upcoming_reservations = Reservation.query.filter_by(
        user_id=current_user.id
    ).filter(
        Reservation.date >= datetime.utcnow(),
        Reservation.status.in_(['pending', 'confirmed'])
    ).order_by(Reservation.date).limit(5).all()
    
    past_reservations = Reservation.query.filter_by(
        user_id=current_user.id
    ).filter(
        Reservation.date < datetime.utcnow()
    ).order_by(Reservation.date.desc()).limit(5).all()
    
    stats = {
        'total': Reservation.query.filter_by(user_id=current_user.id).count(),
        'upcoming': len(upcoming_reservations),
        'completed': Reservation.query.filter_by(user_id=current_user.id, status='completed').count(),
    }
    
    return render_template('client/dashboard.html', 
                         upcoming=upcoming_reservations,
                         past=past_reservations,
                         stats=stats)

@app.route('/client/reservations')
@login_required
def my_reservations():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Reservation.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    reservations = query.order_by(Reservation.date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('client/my_reservations.html', 
                         reservations=reservations,
                         status_filter=status_filter)

@app.route('/owner/reservation/new', methods=['GET', 'POST'])
@login_required
@owner_required
def owner_new_reservation():
    if request.method == 'POST':
        try:
            # Get or create client
            client_email = request.form.get('client_email')
            client_phone = request.form.get('client_phone')
            client_name = request.form.get('client_name')
            
            client = User.query.filter_by(email=client_email).first()
            
            if not client:
                # Create new client
                client = User(
                    email=client_email,
                    name=client_name,
                    phone=client_phone,
                    is_owner=False
                )
                db.session.add(client)
                db.session.flush()
            else:
                # Update existing client info
                client.name = client_name
                client.phone = client_phone
            
            # Create reservation
            reservation = Reservation(
                user_id=client.id,
                reservation_type=request.form.get('reservation_type'),
                title=request.form.get('title'),
                description=request.form.get('description'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M'),
                duration=int(request.form.get('duration', 60)),
                max_participants=int(request.form.get('max_participants', 1)),
                price=float(request.form.get('price', 0)),
                location=request.form.get('location'),
                special_requirements=request.form.get('special_requirements'),
                status='confirmed',
                payment_status=request.form.get('payment_status', 'unpaid'),
                payment_method=request.form.get('payment_method')
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            # Send confirmation email to client
            send_reservation_confirmation_email(reservation)
            
            flash(f'Reservation created successfully for {client.name}! Confirmation email sent.', 'success')
            return redirect(url_for('owner_reservations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating reservation: {str(e)}', 'danger')
    
    templates = ActivityTemplate.query.filter_by(is_active=True).all()
    clients = User.query.filter_by(is_owner=False).all()
    return render_template('owner/new_reservation.html', templates=templates, clients=clients)
@app.route('/owner/reservation/<int:id>/update-payment', methods=['POST'])
@login_required
@owner_required
def update_payment_status(id):
    reservation = Reservation.query.get_or_404(id)
    new_payment_status = request.form.get('payment_status')
    
    if new_payment_status in ['unpaid', 'paid', 'partial', 'refunded']:
        reservation.payment_status = new_payment_status
        db.session.commit()
        flash(f'Payment status updated to {new_payment_status}.', 'success')
    
    return redirect(request.referrer or url_for('owner_reservations'))

@app.route('/owner/reservation/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            reservation.title = request.form.get('title')
            reservation.description = request.form.get('description')
            reservation.date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
            reservation.duration = int(request.form.get('duration'))
            reservation.price = float(request.form.get('price'))
            reservation.location = request.form.get('location')
            reservation.payment_status = request.form.get('payment_status')
            reservation.payment_method = request.form.get('payment_method')
            reservation.status = request.form.get('status')
            
            db.session.commit()
            flash('Reservation updated successfully!', 'success')
            return redirect(url_for('owner_reservations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating reservation: {str(e)}', 'danger')
    
    return render_template('owner/edit_reservation.html', reservation=reservation)

@app.route('/api/notifications')
@login_required
@owner_required
def get_notifications():
    notifications = Notification.query.filter_by(
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'created_at': notif.created_at.strftime('%b %d, %I:%M %p'),
            'reservation_id': notif.related_reservation_id
        })
    
    return jsonify(notifications_data)

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
@owner_required
def mark_all_notifications_read():
    Notification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/owner/notifications')
@login_required
@owner_required
def all_notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('owner/notifications.html', notifications=notifications)

@app.route('/client/reservation/new', methods=['GET', 'POST'])
@login_required
def new_reservation():
    if request.method == 'POST':
        try:
            # Update user phone if provided
            phone = request.form.get('phone')
            if phone and phone != current_user.phone:
                current_user.phone = phone
            
            reservation = Reservation(
                user_id=current_user.id,
                reservation_type=request.form.get('reservation_type'),
                title=request.form.get('title'),
                description=request.form.get('description'),
                date=datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M'),
                duration=int(request.form.get('duration', 60)),
                max_participants=int(request.form.get('max_participants', 1)),
                price=float(request.form.get('price', 0)),
                location=request.form.get('location'),
                special_requirements=request.form.get('special_requirements')
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            # Send confirmation email to client
            send_reservation_confirmation_email(reservation)
            
            # Create notification for owner
            create_notification(
                title=f'New {reservation.reservation_type.replace("_", " ").title()} Reservation',
                message=f'{current_user.name} has made a new reservation for {reservation.title}',
                notification_type='new_reservation',
                reservation_id=reservation.id
            )
            
            # Send email to owner
            send_owner_notification_email(reservation)
            
            flash('Reservation created successfully! Check your email for confirmation.', 'success')
            return redirect(url_for('my_reservations'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating reservation: {str(e)}', 'danger')
    
    templates = ActivityTemplate.query.filter_by(is_active=True).all()
    return render_template('client/new_reservation.html', templates=templates)

@app.route('/client/reservation/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    
    if reservation.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('my_reservations'))
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    # Notify owner
    create_notification(
        title='Reservation Cancelled',
        message=f'{current_user.name} cancelled reservation: {reservation.title}',
        notification_type='cancellation',
        reservation_id=reservation.id
    )
    
    flash('Reservation cancelled successfully.', 'info')
    return redirect(url_for('my_reservations'))

# Owner Routes
@app.route('/owner/dashboard')
@login_required
@owner_required
def owner_dashboard():
    today = datetime.utcnow().date()
    
    # Statistics
    stats = {
        'total_clients': User.query.filter_by(is_owner=False, is_active=True).count(),
        'total_reservations': Reservation.query.count(),
        'pending_reservations': Reservation.query.filter_by(status='pending').count(),
        'today_reservations': Reservation.query.filter(
            db.func.date(Reservation.date) == today
        ).count(),
        'this_month_revenue': db.session.query(db.func.sum(Reservation.price)).filter(
            db.extract('month', Reservation.date) == today.month,
            db.extract('year', Reservation.date) == today.year,
            Reservation.payment_status == 'paid'
        ).scalar() or 0
    }
    
    # Recent reservations
    recent_reservations = Reservation.query.order_by(
        Reservation.created_at.desc()
    ).limit(10).all()
    
    # Upcoming reservations
    upcoming_reservations = Reservation.query.filter(
        Reservation.date >= datetime.utcnow(),
        Reservation.status.in_(['pending', 'confirmed'])
    ).order_by(Reservation.date).limit(5).all()
    
    # Unread notifications
    unread_notifications = Notification.query.filter_by(
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('owner/dashboard.html',
                         stats=stats,
                         recent=recent_reservations,
                         upcoming=upcoming_reservations,
                         notifications=unread_notifications)

@app.route('/owner/reservations')
@login_required
@owner_required
def owner_reservations():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    search = request.args.get('search', '')
    
    query = Reservation.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if type_filter != 'all':
        query = query.filter_by(reservation_type=type_filter)
    
    if search:
        query = query.join(User).filter(
            db.or_(
                Reservation.title.ilike(f'%{search}%'),
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    reservations = query.order_by(Reservation.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('owner/reservations.html',
                         reservations=reservations,
                         status_filter=status_filter,
                         type_filter=type_filter,
                         search=search)

@app.route('/owner/reservation/<int:id>/update-status', methods=['POST'])
@login_required
@owner_required
def update_reservation_status(id):
    reservation = Reservation.query.get_or_404(id)
    new_status = request.form.get('status')
    old_status = reservation.status
    
    if new_status in ['pending', 'confirmed', 'cancelled', 'completed']:
        reservation.status = new_status
        db.session.commit()
        
        # Send email notification to client if status changed
        if old_status != new_status:
            send_status_change_email(reservation, old_status, new_status)
        
        flash(f'Reservation status updated to {new_status}. Email sent to client.', 'success')
    
    return redirect(request.referrer or url_for('owner_reservations'))
@app.route('/owner/clients')
@login_required
@owner_required
def owner_clients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query.filter_by(is_owner=False)
    
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    clients = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('owner/clients.html', clients=clients, search=search)

@app.route('/owner/client/<int:id>')
@login_required
@owner_required
def client_detail(id):
    client = User.query.get_or_404(id)
    
    if client.is_owner:
        flash('Invalid client.', 'danger')
        return redirect(url_for('owner_clients'))
    
    reservations = Reservation.query.filter_by(user_id=id).order_by(
        Reservation.date.desc()
    ).all()
    
    notes = ClientNote.query.filter_by(user_id=id).order_by(
        ClientNote.created_at.desc()
    ).all()
    
    stats = {
        'total_reservations': len(reservations),
        'completed': len([r for r in reservations if r.status == 'completed']),
        'cancelled': len([r for r in reservations if r.status == 'cancelled']),
        'total_spent': sum([r.price for r in reservations if r.payment_status == 'paid'])
    }
    
    return render_template('owner/client_detail.html',
                         client=client,
                         reservations=reservations,
                         notes=notes,
                         stats=stats)

@app.route('/owner/client/<int:id>/add-note', methods=['POST'])
@login_required
@owner_required
def add_client_note(id):
    client = User.query.get_or_404(id)
    note_text = request.form.get('note')
    
    if note_text:
        note = ClientNote(
            user_id=id,
            note=note_text,
            created_by=current_user.name
        )
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully.', 'success')
    
    return redirect(url_for('client_detail', id=id))

@app.route('/owner/analytics')
@login_required
@owner_required
def owner_analytics():
    # Revenue by month (last 6 months)
    revenue_data = db.session.query(
        db.extract('month', Reservation.date).label('month'),
        db.func.sum(Reservation.price).label('revenue')
    ).filter(
        Reservation.date >= datetime.utcnow() - timedelta(days=180),
        Reservation.payment_status == 'paid'
    ).group_by(db.extract('month', Reservation.date)).all()
    
    # Reservations by type
    type_data = db.session.query(
        Reservation.reservation_type,
        db.func.count(Reservation.id)
    ).group_by(Reservation.reservation_type).all()
    
    # Status distribution
    status_data = db.session.query(
        Reservation.status,
        db.func.count(Reservation.id)
    ).group_by(Reservation.status).all()
    
    return render_template('owner/analytics.html',
                         revenue_data=revenue_data,
                         type_data=type_data,
                         status_data=status_data)

@app.route('/owner/settings', methods=['GET', 'POST'])
@login_required
@owner_required
def owner_settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_template':
            template = ActivityTemplate(
                name=request.form.get('name'),
                description=request.form.get('description'),
                category=request.form.get('category'),
                default_duration=int(request.form.get('duration', 60)),
                default_price=float(request.form.get('price', 0)),
                default_max_participants=int(request.form.get('max_participants', 1))
            )
            db.session.add(template)
            db.session.commit()
            flash('Activity template added successfully.', 'success')
    
    templates = ActivityTemplate.query.all()
    return render_template('owner/settings.html', templates=templates)

@app.route('/api/notifications/mark-read/<int:id>', methods=['POST'])
@login_required
@owner_required
def mark_notification_read(id):
    notification = Notification.query.get_or_404(id)
    notification.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/notifications/unread-count')
@login_required
@owner_required
def unread_notification_count():
    count = Notification.query.filter_by(is_read=False).count()
    return jsonify({'count': count})

# Initialize database
@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        app.tables_created = True
@app.route('/debug-info')
def debug_info():
    import os
    info = {
        'Template folder exists': os.path.exists(app.template_folder),
        'Static folder exists': os.path.exists(app.static_folder),
        'Template folder path': app.template_folder,
        'Static folder path': app.static_folder,
        'Routes': [str(rule) for rule in app.url_map.iter_rules()]
    }
    return jsonify(info)
@app.route('/owner/template/add', methods=['POST'])
@login_required
@owner_required
def add_template():
    """Add a new activity template"""
    try:
        template = ActivityTemplate(
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            default_duration=int(request.form.get('duration', 60)),
            default_price=float(request.form.get('price', 0)),
            default_max_participants=int(request.form.get('max_participants', 10)),
            is_active=True
        )
        db.session.add(template)
        db.session.commit()
        flash(f'Template "{template.name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding template: {str(e)}', 'danger')
    
    return redirect(url_for('owner_settings'))

@app.route('/owner/template/<int:id>/edit', methods=['POST'])
@login_required
@owner_required
def edit_template(id):
    """Edit an activity template"""
    template = ActivityTemplate.query.get_or_404(id)
    
    try:
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.category = request.form.get('category')
        template.default_duration = int(request.form.get('duration'))
        template.default_price = float(request.form.get('price'))
        template.default_max_participants = int(request.form.get('max_participants'))
        
        db.session.commit()
        flash(f'Template "{template.name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating template: {str(e)}', 'danger')
    
    return redirect(url_for('owner_settings'))

@app.route('/owner/template/<int:id>/delete', methods=['POST'])
@login_required
@owner_required
def delete_template(id):
    """Delete an activity template"""
    template = ActivityTemplate.query.get_or_404(id)
    
    try:
        template_name = template.name
        db.session.delete(template)
        db.session.commit()
        flash(f'Template "{template_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting template: {str(e)}', 'danger')
    
    return redirect(url_for('owner_settings'))

@app.route('/api/calendar/events')
@login_required
@owner_required
def calendar_events():
    """Return reservations in FullCalendar format"""
    try:
        # Get date range from query parameters (sent by FullCalendar)
        start = request.args.get('start')
        end = request.args.get('end')
        
        query = Reservation.query
        
        if start:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            query = query.filter(Reservation.date >= start_date)
        
        if end:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            query = query.filter(Reservation.date <= end_date)
        
        reservations = query.all()
        
        events = []
        for res in reservations:
            # Calculate end time
            end_time = res.date + timedelta(minutes=res.duration)
            
            events.append({
                'id': res.id,
                'title': res.title,
                'start': res.date.isoformat(),
                'end': end_time.isoformat(),
                'extendedProps': {
                    'id': res.id,
                    'reservation_type': res.reservation_type,
                    'status': res.status,
                    'client_name': res.client.name,
                    'client_email': res.client.email,
                    'client_phone': res.client.phone,
                    'description': res.description,
                    'duration': res.duration,
                    'location': res.location,
                    'price': float(res.price),
                    'payment_status': res.payment_status,
                    'special_requirements': res.special_requirements
                }
            })
        
        return jsonify(events)
        
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/owner/calendar')
@login_required
@owner_required
def owner_calendar():
    """Display calendar view"""
    return render_template('owner/calendar.html')


@app.route('/test-email')
@login_required
def test_email():
    msg = Message(
        subject="Test Email from Art CRM",
        recipients=[current_user.email],
        html="<h1>Email is working!</h1><p>If you see this, your email configuration is correct.</p>"
    )
    try:
        mail.send(msg)
        return "Email sent! Check your inbox."
    except Exception as e:
        return f"Error: {e}"
if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")
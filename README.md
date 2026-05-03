# Art CRM

A Flask-based CRM and booking system for art studios. Clients can browse and reserve art activities, sessions, and events; the studio owner manages reservations, clients, calendar, analytics, and templates from a dedicated dashboard.

## Features

- **Google OAuth sign-in** for clients (Flask-Login session management)
- **Reservation system** for three types: art activities, art sessions, and events
- **Client portal** — dashboard, browse templates, create and cancel reservations, view history
- **Owner dashboard** — manage reservations, clients (with notes), calendar, analytics, activity templates, and settings
- **Email notifications** via Flask-Mail (confirmation emails, status updates)
- **In-app notifications** with unread-count API
- **Calendar API** exposing reservations as events
- **Seed data** for sample activity templates

## Tech Stack

- Python / Flask 2.3
- Flask-SQLAlchemy (SQLite by default)
- Flask-Login, Flask-Mail
- Google OAuth (`google-auth`, `google-auth-oauthlib`)
- HTML templates (Jinja2) + static CSS/JS

## Project Structure

```
.
├── app.py              # Flask app, all routes and email/notification helpers
├── config.py           # Config loaded from environment variables
├── models.py           # SQLAlchemy models: User, Reservation, ClientNote, Notification, ActivityTemplate
├── resetdb.py          # Drop and recreate the database
├── seed_data.py        # Seed sample activity templates
├── requirements.txt
├── instance/           # SQLite database lives here
├── static/             # css, js, images
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── client/         # dashboard, my_reservations, new_reservation
    └── owner/          # dashboard, reservations, clients, calendar, analytics, settings, ...
```

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root:

```ini
SECRET_KEY=change-me

# Database (defaults to sqlite:///art_crm.db if unset)
DATABASE_URL=sqlite:///art_crm.db

# Google OAuth — create credentials at https://console.cloud.google.com/
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# Mail (Gmail SMTP example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=you@gmail.com

# The Google account that should receive owner privileges on first login
OWNER_EMAIL=owner@example.com
```

### 3. Initialize the database

```bash
python resetdb.py        # creates tables
python seed_data.py      # optional: adds sample activity templates
```

### 4. Run the app

```bash
python app.py
```

The app starts on `http://localhost:5000`. Sign in with Google — the account whose email matches `OWNER_EMAIL` gets owner privileges and access to `/owner/*` routes.

## Key Routes

| Path | Description |
| --- | --- |
| `/` | Landing page |
| `/login`, `/auth/google`, `/logout` | Auth |
| `/client/dashboard` | Client home |
| `/client/reservations`, `/client/reservation/new` | Client bookings |
| `/owner/dashboard` | Owner home |
| `/owner/reservations`, `/owner/reservation/new`, `/owner/reservation/<id>/edit` | Reservation management |
| `/owner/clients`, `/owner/client/<id>` | Client management with notes |
| `/owner/calendar`, `/api/calendar/events` | Calendar view |
| `/owner/analytics` | Reporting |
| `/owner/settings` | Activity templates and settings |
| `/api/notifications`, `/api/notifications/unread-count` | Notification APIs |

## Notes

- The default database is SQLite and lives in `instance/`. Set `DATABASE_URL` to use Postgres or another backend.
- Owner status is stored on the `User` row (`is_owner`). The first sign-in matching `OWNER_EMAIL` is promoted; you can also flip the flag manually in the DB.
- For Gmail SMTP, generate an [App Password](https://support.google.com/accounts/answer/185833) rather than using your account password.

"""
Google OAuth authentication for Meal Planner.
STR-35: Implement Google OAuth login flow
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Blueprint, redirect, url_for, session, request, g, current_app, jsonify
from authlib.integrations.flask_client import OAuth
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

# Blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# OAuth setup
oauth = OAuth()

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'


class User(UserMixin):
    """User model for Flask-Login."""

    def __init__(self, id, google_id, email, name, avatar_url):
        self.id = id
        self.google_id = google_id
        self.email = email
        self.name = name
        self.avatar_url = avatar_url

    @staticmethod
    def get_by_id(user_id):
        """Load user from database by ID."""
        from app import get_db
        conn = get_db()
        cursor = conn.execute(
            "SELECT id, google_id, email, name, avatar_url FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return User(
                id=row[0],
                google_id=row[1],
                email=row[2],
                name=row[3],
                avatar_url=row[4]
            )
        return None

    @staticmethod
    def get_or_create(google_id, email, name, avatar_url):
        """Get existing user or create new one."""
        from app import get_db
        conn = get_db()

        # Try to find existing user
        cursor = conn.execute(
            "SELECT id, google_id, email, name, avatar_url FROM users WHERE google_id = ?",
            (google_id,)
        )
        row = cursor.fetchone()

        if row:
            # Update last_login and any changed profile info
            conn.execute(
                """UPDATE users
                   SET last_login = ?, name = ?, avatar_url = ?, email = ?
                   WHERE id = ?""",
                (datetime.utcnow(), name, avatar_url, email, row[0])
            )
            conn.commit()
            return User(
                id=row[0],
                google_id=row[1],
                email=email,
                name=name,
                avatar_url=avatar_url
            )

        # Create new user
        cursor = conn.execute(
            """INSERT INTO users (google_id, email, name, avatar_url, created_at, last_login)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (google_id, email, name, avatar_url, datetime.utcnow(), datetime.utcnow())
        )
        conn.commit()

        return User(
            id=cursor.lastrowid,
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return User.get_by_id(user_id)


def init_oauth(app):
    """Initialize OAuth with the Flask app."""
    oauth.init_app(app)

    # Register Google OAuth provider
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )


def init_auth(app):
    """Initialize all auth components with the Flask app."""
    # Set secret key for sessions
    app.secret_key = app.config.get('SECRET_KEY', os.urandom(24))

    # Initialize Flask-Login
    login_manager.init_app(app)

    # Initialize OAuth
    init_oauth(app)

    # Register blueprint
    app.register_blueprint(auth_bp)


# ============================================================================
# AUTH ROUTES
# ============================================================================

@auth_bp.route('/login')
def login():
    """Redirect to Google OAuth consent screen."""
    # Store the page user came from to redirect back after login
    next_url = request.args.get('next') or request.referrer or url_for('index')
    session['next_url'] = next_url

    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Handle OAuth callback from Google."""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')

        if not user_info:
            # Fetch user info from Google
            user_info = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo').json()

        # Get or create user in database
        user = User.get_or_create(
            google_id=user_info['sub'],
            email=user_info['email'],
            name=user_info.get('name', ''),
            avatar_url=user_info.get('picture', '')
        )

        # Log the user in
        login_user(user)

        # Redirect to original page or home
        next_url = session.pop('next_url', url_for('index'))
        return redirect(next_url)

    except Exception as e:
        current_app.logger.error(f"OAuth error: {e}")
        return redirect(url_for('index'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log out the current user."""
    logout_user()
    session.clear()
    return redirect(url_for('index'))


@auth_bp.route('/me')
def me():
    """Return current user info as JSON (API endpoint)."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.name,
            'avatar_url': current_user.avatar_url
        })
    return jsonify({'authenticated': False})

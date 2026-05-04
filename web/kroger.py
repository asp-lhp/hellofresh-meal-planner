"""
Kroger API integration for Meal Planner.
Implements OAuth 2.0 Authorization Code Grant flow for cart access.

Kroger Developer Portal: https://developer.kroger.com/
Required scope: cart.basic:write
"""

import os
import base64
import secrets
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from flask import Blueprint, redirect, url_for, session, request, current_app, jsonify
from flask_login import login_required, current_user

# Blueprint for Kroger routes
kroger_bp = Blueprint('kroger', __name__, url_prefix='/kroger')

# Kroger OAuth endpoints
KROGER_AUTH_URL = "https://api.kroger.com/v1/connect/oauth2/authorize"
KROGER_TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
KROGER_API_BASE = "https://api.kroger.com/v1"

# Required scope for cart operations
KROGER_SCOPE = "cart.basic:write product.compact"


def get_db():
    """Import get_db from app module."""
    from app import get_db as app_get_db
    return app_get_db()


def get_user_kroger_credentials(user_id):
    """Get Kroger credentials for a user."""
    conn = get_db()
    row = conn.execute("""
        SELECT kroger_client_id, kroger_client_secret,
               kroger_access_token, kroger_refresh_token, kroger_token_expires_at
        FROM user_preferences WHERE user_id = ?
    """, (user_id,)).fetchone()
    conn.close()

    if row:
        return {
            'client_id': row[0],
            'client_secret': row[1],
            'access_token': row[2],
            'refresh_token': row[3],
            'token_expires_at': row[4]
        }
    return None


def save_kroger_tokens(user_id, access_token, refresh_token, expires_in):
    """Save Kroger OAuth tokens to database."""
    conn = get_db()
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    conn.execute("""
        UPDATE user_preferences SET
            kroger_access_token = ?,
            kroger_refresh_token = ?,
            kroger_token_expires_at = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (access_token, refresh_token, expires_at, user_id))

    conn.commit()
    conn.close()


def clear_kroger_tokens(user_id):
    """Clear Kroger OAuth tokens (disconnect)."""
    conn = get_db()
    conn.execute("""
        UPDATE user_preferences SET
            kroger_access_token = NULL,
            kroger_refresh_token = NULL,
            kroger_token_expires_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()


def is_token_expired(token_expires_at):
    """Check if token is expired or about to expire."""
    if not token_expires_at:
        return True

    if isinstance(token_expires_at, str):
        token_expires_at = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))

    # Consider expired if less than 5 minutes remaining
    return datetime.utcnow() >= token_expires_at - timedelta(minutes=5)


def refresh_kroger_token(user_id, credentials):
    """Refresh Kroger access token using refresh token."""
    if not credentials.get('refresh_token'):
        return None

    client_id = credentials['client_id']
    client_secret = credentials['client_secret']

    # Base64 encode credentials for Basic auth
    auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    try:
        with httpx.Client() as client:
            response = client.post(
                KROGER_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": credentials['refresh_token']
                }
            )

            if response.status_code == 200:
                token_data = response.json()
                save_kroger_tokens(
                    user_id,
                    token_data['access_token'],
                    token_data.get('refresh_token', credentials['refresh_token']),
                    token_data.get('expires_in', 1800)
                )
                return token_data['access_token']
            else:
                current_app.logger.error(f"Kroger token refresh failed: {response.status_code}")
                return None
    except Exception as e:
        current_app.logger.error(f"Kroger token refresh error: {e}")
        return None


def get_valid_kroger_token(user_id):
    """Get a valid Kroger access token, refreshing if necessary."""
    credentials = get_user_kroger_credentials(user_id)

    if not credentials or not credentials.get('access_token'):
        return None

    if is_token_expired(credentials.get('token_expires_at')):
        return refresh_kroger_token(user_id, credentials)

    return credentials['access_token']


# ============================================================================
# KROGER OAUTH ROUTES
# ============================================================================

@kroger_bp.route('/authorize')
@login_required
def authorize():
    """Redirect to Kroger OAuth consent screen."""
    credentials = get_user_kroger_credentials(current_user.id)

    if not credentials or not credentials.get('client_id') or not credentials.get('client_secret'):
        return redirect(url_for('settings_page', error='Please configure Kroger API credentials first.'))

    # Generate PKCE code verifier and challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')

    # Store verifier in session for callback
    session['kroger_code_verifier'] = code_verifier
    session['kroger_state'] = secrets.token_urlsafe(32)

    # Build authorization URL
    params = {
        'scope': KROGER_SCOPE,
        'response_type': 'code',
        'client_id': credentials['client_id'],
        'redirect_uri': url_for('kroger.callback', _external=True),
        'state': session['kroger_state'],
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }

    auth_url = f"{KROGER_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)


@kroger_bp.route('/callback')
@login_required
def callback():
    """Handle OAuth callback from Kroger."""
    error = request.args.get('error')
    if error:
        current_app.logger.error(f"Kroger OAuth error: {error}")
        return redirect(url_for('settings_page', error=f'Kroger authorization failed: {error}'))

    code = request.args.get('code')
    state = request.args.get('state')

    # Verify state
    if state != session.get('kroger_state'):
        return redirect(url_for('settings_page', error='Invalid OAuth state. Please try again.'))

    code_verifier = session.pop('kroger_code_verifier', None)
    session.pop('kroger_state', None)

    if not code or not code_verifier:
        return redirect(url_for('settings_page', error='Missing authorization code. Please try again.'))

    credentials = get_user_kroger_credentials(current_user.id)
    if not credentials:
        return redirect(url_for('settings_page', error='Kroger credentials not found.'))

    # Exchange code for tokens
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']
    auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    try:
        with httpx.Client() as client:
            response = client.post(
                KROGER_TOKEN_URL,
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": url_for('kroger.callback', _external=True),
                    "code_verifier": code_verifier
                }
            )

            if response.status_code == 200:
                token_data = response.json()
                save_kroger_tokens(
                    current_user.id,
                    token_data['access_token'],
                    token_data.get('refresh_token'),
                    token_data.get('expires_in', 1800)
                )
                return redirect(url_for('settings_page', success='Successfully connected to Kroger!'))
            else:
                current_app.logger.error(f"Kroger token exchange failed: {response.status_code} - {response.text}")
                return redirect(url_for('settings_page', error='Failed to connect to Kroger. Please try again.'))

    except Exception as e:
        current_app.logger.error(f"Kroger OAuth error: {e}")
        return redirect(url_for('settings_page', error='Connection error. Please try again.'))


@kroger_bp.route('/disconnect', methods=['POST'])
@login_required
def disconnect():
    """Disconnect Kroger account."""
    clear_kroger_tokens(current_user.id)
    return redirect(url_for('settings_page', success='Disconnected from Kroger.'))


@kroger_bp.route('/status')
@login_required
def status():
    """Check Kroger connection status (JSON endpoint)."""
    credentials = get_user_kroger_credentials(current_user.id)

    if not credentials:
        return jsonify({'connected': False, 'configured': False})

    configured = bool(credentials.get('client_id') and credentials.get('client_secret'))
    connected = bool(credentials.get('access_token'))

    if connected and is_token_expired(credentials.get('token_expires_at')):
        # Try to refresh
        token = refresh_kroger_token(current_user.id, credentials)
        connected = token is not None

    return jsonify({
        'connected': connected,
        'configured': configured
    })


# ============================================================================
# KROGER CART API
# ============================================================================

@kroger_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    """Add items to Kroger cart."""
    token = get_valid_kroger_token(current_user.id)

    if not token:
        return jsonify({'error': 'Not connected to Kroger. Please authorize first.'}), 401

    data = request.json
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'No items provided'}), 400

    # Format items for Kroger Cart API
    cart_items = []
    for item in items:
        cart_items.append({
            "upc": item.get('upc') or item.get('product_id'),
            "quantity": item.get('quantity', 1)
        })

    try:
        with httpx.Client() as client:
            response = client.put(
                f"{KROGER_API_BASE}/cart/add",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={"items": cart_items}
            )

            if response.status_code in [200, 201, 204]:
                return jsonify({
                    'success': True,
                    'message': f'Added {len(cart_items)} item(s) to Kroger cart'
                })
            elif response.status_code == 401:
                # Token might be invalid, clear it
                clear_kroger_tokens(current_user.id)
                return jsonify({'error': 'Kroger authorization expired. Please reconnect.'}), 401
            else:
                current_app.logger.error(f"Kroger cart add failed: {response.status_code} - {response.text}")
                return jsonify({'error': 'Failed to add items to cart'}), response.status_code

    except Exception as e:
        current_app.logger.error(f"Kroger cart error: {e}")
        return jsonify({'error': 'Connection error'}), 500


@kroger_bp.route('/products/search')
@login_required
def search_products():
    """Search Kroger products to get UPCs for cart."""
    token = get_valid_kroger_token(current_user.id)

    if not token:
        return jsonify({'error': 'Not connected to Kroger'}), 401

    query = request.args.get('q', '').strip()
    location_id = request.args.get('location_id')

    if not query:
        return jsonify({'error': 'Search query required'}), 400

    params = {
        'filter.term': query,
        'filter.limit': 10
    }

    if location_id:
        params['filter.locationId'] = location_id

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{KROGER_API_BASE}/products",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )

            if response.status_code == 200:
                data = response.json()
                products = []
                for item in data.get('data', []):
                    products.append({
                        'upc': item.get('upc'),
                        'productId': item.get('productId'),
                        'description': item.get('description'),
                        'brand': item.get('brand'),
                        'images': item.get('images', []),
                        'price': item.get('items', [{}])[0].get('price', {})
                    })
                return jsonify({'products': products})
            else:
                return jsonify({'error': 'Search failed'}), response.status_code

    except Exception as e:
        current_app.logger.error(f"Kroger search error: {e}")
        return jsonify({'error': 'Connection error'}), 500


def init_kroger(app):
    """Register Kroger blueprint with app."""
    app.register_blueprint(kroger_bp)

import math
import os
import io
import re
import secrets
import smtplib
import sqlite3
from contextlib import closing
from email.message import EmailMessage

from flask import Flask, render_template, send_file, jsonify, abort, redirect, request

app = Flask(__name__)

# Register pillow-heif so PIL can open HEIC files
from pillow_heif import register_heif_opener
register_heif_opener()

SURPRISE_DAD_DIR = os.path.join(app.static_folder, 'images', 'surprise', 'dad')
VISITOR_TRACKING_DB = os.path.join(app.instance_path, 'visitor_tracking.sqlite3')


def _visitor_tracking_connection():
    os.makedirs(app.instance_path, exist_ok=True)
    connection = sqlite3.connect(VISITOR_TRACKING_DB, timeout=5)
    os.chmod(VISITOR_TRACKING_DB, 0o600)
    connection.row_factory = sqlite3.Row
    connection.execute(
        '''
        CREATE TABLE IF NOT EXISTS visitor_privacy (
            visitor_id TEXT PRIMARY KEY,
            consent INTEGER NOT NULL,
            ip_address TEXT,
            visitor_name TEXT,
            latitude REAL,
            longitude REAL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    columns = {
        row['name']
        for row in connection.execute('PRAGMA table_info(visitor_privacy)')
    }
    if 'visitor_name' not in columns:
        connection.execute('ALTER TABLE visitor_privacy ADD COLUMN visitor_name TEXT')
    return connection


def _send_visitor_notification(visitor):
    recipient = os.environ.get('VISITOR_NOTIFICATION_EMAIL', '').strip()
    username = os.environ.get('SMTP_USERNAME', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '')
    sender = os.environ.get('SMTP_FROM', username).strip()
    if not all((recipient, username, password)):
        app.logger.error(
            'Visitor notification email is not configured; set '
            'VISITOR_NOTIFICATION_EMAIL, SMTP_USERNAME, and SMTP_PASSWORD.'
        )
        return False

    coordinates = 'Not shared'
    if visitor['latitude'] is not None and visitor['longitude'] is not None:
        coordinates = f"{visitor['latitude']:.2f}, {visitor['longitude']:.2f}"
    message = EmailMessage()
    message['Subject'] = 'Visitor on the Koloth Group site'
    message['From'] = sender
    message['To'] = recipient
    message.set_content(
        'A visitor opened the Koloth Group site and opted in to optional tracking.\n\n'
        f"Name: {visitor['visitor_name'] or 'Not provided'}\n"
        f"Approximate coordinates: {coordinates}\n"
        f"IP address: {visitor['ip_address'] or 'Unavailable'}\n"
        f"Recorded at: {visitor['updated_at']}\n"
    )
    host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    try:
        with smtplib.SMTP_SSL(
            host,
            int(os.environ.get('SMTP_PORT', '465')),
            timeout=10,
        ) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        app.logger.exception('Could not send visitor notification email.')
        return False
    return True


def _visitor_id():
    visitor_id = request.cookies.get('visitor_id', '')
    if not re.fullmatch(r'[a-f0-9]{32}', visitor_id):
        return None
    return visitor_id


@app.route('/')
def home():
    return render_template('index.html', active_tab='home')


@app.route('/shop')
def shop():
    return redirect('https://shop.kolothgroup.com')


@app.route('/api/privacy/consent', methods=['GET', 'POST'])
def visitor_privacy_consent():
    visitor_id = _visitor_id()
    if request.method == 'GET':
        if visitor_id is None:
            response = jsonify(consent=False)
        else:
            with closing(_visitor_tracking_connection()) as db:
                row = db.execute(
                    'SELECT consent FROM visitor_privacy WHERE visitor_id = ?',
                    (visitor_id,),
                ).fetchone()
            response = jsonify(consent=bool(row['consent']) if row else False)
        response.headers['Cache-Control'] = 'no-store'
        return response

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or type(payload.get('consent')) is not bool:
        return jsonify(error='Choose whether to allow optional visitor tracking.'), 400

    consent = payload['consent']
    visitor_name = payload.get('name', '')
    if not isinstance(visitor_name, str) or len(visitor_name) > 80:
        return jsonify(error='Name must be 80 characters or fewer.'), 400
    visitor_name = re.sub(r'[\x00-\x1f\x7f]', '', visitor_name).strip() or None
    latitude = payload.get('latitude')
    longitude = payload.get('longitude')
    if consent and (latitude is not None or longitude is not None):
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
            or not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            return jsonify(error='The location coordinates are invalid.'), 400
        latitude = round(latitude, 2)
        longitude = round(longitude, 2)
    else:
        latitude = longitude = None

    visitor_id = visitor_id or secrets.token_hex(16)
    with closing(_visitor_tracking_connection()) as db:
        db.execute(
            '''
            INSERT INTO visitor_privacy
                (visitor_id, consent, ip_address, visitor_name, latitude, longitude, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (visitor_id) DO UPDATE SET
                consent = excluded.consent,
                ip_address = excluded.ip_address,
                visitor_name = excluded.visitor_name,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (
                visitor_id,
                consent,
                request.remote_addr if consent else None,
                visitor_name if consent else None,
                latitude,
                longitude,
            ),
        )
        db.commit()

    response = jsonify(consent=consent)
    response.set_cookie(
        'visitor_id',
        visitor_id,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        secure=request.is_secure,
        samesite='Lax',
    )
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.post('/api/privacy/visit')
def visitor_visit():
    visitor_id = _visitor_id()
    if visitor_id is None:
        return jsonify(error='Opt in to optional visitor tracking first.'), 403
    with closing(_visitor_tracking_connection()) as db:
        visitor = db.execute(
            '''
            SELECT consent, visitor_name, ip_address, latitude, longitude, updated_at
            FROM visitor_privacy WHERE visitor_id = ?
            ''',
            (visitor_id,),
        ).fetchone()
    if visitor is None or not visitor['consent']:
        return jsonify(error='Opt in to optional visitor tracking first.'), 403
    if not _send_visitor_notification(visitor):
        return jsonify(error='Email notification could not be sent; check the server email settings.'), 503
    response = jsonify(notification_sent=True)
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.route('/favicon.ico')
def favicon():
    favicon_path = os.path.join(app.static_folder, 'images', 'Logos', 'Logo.ico')
    return send_file(favicon_path, mimetype='image/x-icon', max_age=0)


@app.route('/surprise')
def surprise():
    return render_template('index.html', active_tab='surprise')


@app.route('/api/surprise-photos')
def surprise_photos():
    """Return a JSON list of photo filenames in the dad folder."""
    allowed_ext = {'.jpg', '.jpeg', '.png', '.heic', '.gif'}
    photos = []
    if os.path.isdir(SURPRISE_DAD_DIR):
        for f in sorted(os.listdir(SURPRISE_DAD_DIR)):
            ext = os.path.splitext(f)[1].lower()
            if ext in allowed_ext:
                photos.append(f)
    return jsonify(photos)


@app.route('/photo/<filename>')
def serve_photo(filename):
    """Serve a photo, converting HEIC to JPEG on the fly."""
    filepath = os.path.join(SURPRISE_DAD_DIR, filename)

    if not os.path.isfile(filepath):
        abort(404)

    ext = os.path.splitext(filename)[1].lower()

    if ext == '.heic':
        from PIL import Image
        # Check for a cached JPEG version
        cache_dir = os.path.join(SURPRISE_DAD_DIR, '.cache')
        os.makedirs(cache_dir, exist_ok=True)
        cached_name = os.path.splitext(filename)[0] + '.jpg'
        cached_path = os.path.join(cache_dir, cached_name)

        if not os.path.isfile(cached_path):
            img = Image.open(filepath)
            # Auto-orient based on EXIF
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
            # Resize for web (max 1200px on longest side)
            img.thumbnail((1200, 1200), Image.LANCZOS)
            img.save(cached_path, 'JPEG', quality=82, optimize=True)

        return send_file(cached_path, mimetype='image/jpeg')

    # For JPG/PNG/GIF serve directly
    return send_file(filepath)


@app.route('/api/bmw-theme-images')
def bmw_theme_images():
    """Return a JSON list of BMW theme image filenames."""
    bmw_dir = os.path.join(app.static_folder, 'images', 'BMW_Theme')
    allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    images = []
    if os.path.isdir(bmw_dir):
        for f in sorted(os.listdir(bmw_dir)):
            ext = os.path.splitext(f)[1].lower()
            if et:
                images.append(f)
    return jsonify(images)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1440)

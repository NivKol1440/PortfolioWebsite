import os
import io
from flask import Flask, render_template, send_file, jsonify, abort

app = Flask(__name__)

# Register pillow-heif so PIL can open HEIC files
from pillow_heif import register_heif_opener
register_heif_opener()

SURPRISE_DAD_DIR = os.path.join(app.static_folder, 'images', 'surprise', 'dad')


@app.route('/')
def home():
    return render_template('index.html', active_tab='home')


@app.route('/shop')
def shop():
    return render_template('index.html', active_tab='shop')


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
            if ext in allowed_ext:
                images.append(f)
    return jsonify(images)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

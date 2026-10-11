# kolothgroup

Portfolio website for **Nivedh Koloth Shijan** — built with Flask, featuring a BMW-themed birthday Surprise page dedicated to Shijan Koloth.

## Features

- 🏠 **Portfolio Home** — Hero section, ventures (Volar India, BranFresh), and skills showcase
- 🔘 **Apple-style liquid tab switcher** with spring-animated indicator
- 📸 **HEIC-to-JPEG conversion** — server-side with caching

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000`

## Deploy to Render

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

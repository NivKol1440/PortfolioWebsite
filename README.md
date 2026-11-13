# kolothgroup

Portfolio website for **Nivedh Koloth Shijan** — built with Flask, **You can build your own Website too... Learn how to below!**

## Features

- 🏠 **Portfolio Home** — Hero section, ventures (Volar India, BranFresh), and skills showcase
- 🔘 **Apple-style liquid tab switcher** with spring-animated indicator
- 📸 **HEIC-to-JPEG conversion** — server-side with caching
- 📍 **Optional visitor location tracking** — explicit consent; approximate coordinates, IP, and an optional name stored locally in `instance/visitor_tracking.sqlite3`

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:1440`

To receive email alerts for each visit from a browser that opted in, configure `VISITOR_NOTIFICATION_EMAIL`, `SMTP_USERNAME`, and `SMTP_PASSWORD` in the server environment. `SMTP_FROM` defaults to `SMTP_USERNAME`; `SMTP_HOST` defaults to `smtp.gmail.com` and `SMTP_PORT` to `465`. Never commit email credentials.

## Deploy to Render

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`

# kolothgroup

Portfolio website for **Nivedh Koloth Shijan** — built with Flask, featuring a BMW-themed birthday Surprise page dedicated to Shijan Koloth.

## Features

- 🏠 **Portfolio Home** — Hero section, ventures (Volar India, BranFresh), and skills showcase
- 🎁 **Surprise Page** — Happy Birthday celebration with:
  - 96 photo memories in a masonry flow layout
  - BMW-themed cinematic slideshow background
  - Click-to-enlarge lightbox with keyboard navigation
  - Birthday music at ambient volume
  - Confetti animation & ambient background from photo colors
- 🔘 **Apple-style liquid tab switcher** with spring-animated indicator
- 📸 **HEIC-to-JPEG conversion** — server-side with caching

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install flask pillow pillow-heif
python app.py
```

Visit `http://127.0.0.1:5000`

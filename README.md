# UnderGroundZone

This repository contains a small Flask backend and a simple frontend for the UnderGroundZone Telegram Mini App.

Quick start (local):

1. Copy .env.example to .env and fill secrets (CRYPTO_WEBHOOK_SECRET, ADMIN_SECRET, BOT_TOKEN if used).

```bash
cp .env.example .env
```

2. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Seed the database with sample data:

```bash
python seed_db.py
```

4. Run locally:

```bash
gunicorn start:app --bind 0.0.0.0:5000
```

Open http://localhost:5000/?telegram_id=12345 to simulate a user (or use Telegram WebApp to pass real data).

Railway deployment
------------------

Railway is a convenient host for this app. Recommended flow:

1) Create a new project on Railway and connect GitHub repository atomowabomba3-boop/UnderGroundZone.
2) In Railway, add the PostgreSQL plugin (Railway will provide DATABASE_URL automatically in project environment variables).
3) In Railway project settings → Variables, add the following environment variables:
   - CRYPTO_WEBHOOK_SECRET
   - ADMIN_SECRET
   - BOT_TOKEN (optional)

Note: The app reads DATABASE_URL (if present) or falls back to local SQLite (DATABASE).

4) Deploy the ugz/add-features branch (Railway will detect Dockerfile and build). If you prefer, set the Start Command to:

```bash
gunicorn start:app --bind 0.0.0.0:$PORT
```

5) After first deploy, run a one-off command in Railway to seed DB:

```bash
python seed_db.py
```

6) Test the app using the Railway-assigned URL, e.g. https://your-project.up.railway.app/?telegram_id=1001

Security note:
- Do NOT commit real secrets to the repository. Use platform env vars.


# UnderGroundZone

This repository contains a small Flask backend and a simple frontend for the UnderGroundZone Telegram Mini App.

Quick start (local):

1. Copy .env.example to .env and fill secrets (CRYPTO_WEBHOOK_SECRET, ADMIN_SECRET, BOT_TOKEN if used).

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

Deploying to Railway / Heroku:
- Repository contains a Procfile and Dockerfile ready for container deployments.
- Set environment variables in the deployment provider (CRYPTO_WEBHOOK_SECRET and ADMIN_SECRET at minimum).

Security note:
- Do NOT commit real secrets into the repo. Use environment variables on the host.


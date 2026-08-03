# UnderGroundZone

Projekt Telegram Mini App — backend (Flask) + frontend (simple HTML/JS). Gotowy do wdrożenia na Railway.

Pliki:
- api.py — główny Flask app i endpointy
- database.py — SQLite wrapper i helpery
- giveaway.py — logika giveaway
- utils.py — helpery (ładowanie ebooków, bonusy)
- start.py — lokalny entrypoint (gunicorn preferowany)
- requirements.txt
- /webapp — frontend
- /ebooks — pliki PDF i metadata

Uruchomienie lokalne:
- python -m venv venv
- pip install -r requirements.txt
- flask run

W Railway ustaw start command: `gunicorn start:app`

Dodaj pliki PDF do /ebooks i grafiki do webapp/images

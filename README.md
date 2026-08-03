# UnderGroundZone

Projekt Telegram Mini App — backend (Flask) + frontend (simple HTML/JS). Gotowy do wdrożenia na Railway.

Pliki:
- api.py — główny Flask app z endpointami
- database.py — SQLite wrapper i helpery
- giveaway.py — logika giveaway (start/join/end, wybór zwycięzcy)
- utils.py — helpery (ładowanie ebooków, bonusy)
- start.py — lokalny entrypoint (gunicorn preferowany)
- requirements.txt
- /webapp — frontend
- /ebooks — pliki PDF i metadata

Wymagane zmienne środowiskowe (Railway):
- TELEGRAM_BOT_TOKEN — token bota (opcjonalne, wymagane do wysyłania przycisków Web App)
- WEBHOOK_SECRET — sekret, który będzie wysyłany w nagłówku X-WEBHOOK-SECRET do /buy-ebook (silne zalecenie)

Uruchomienie lokalne:
- python -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- flask run

Production / Railway (zalecane):
- Start command: gunicorn start:app
- Dodaj pliki PDF do katalogu /ebooks oraz obrazy do /webapp/images
- Ustaw zmienne środowiskowe (TELEGRAM_BOT_TOKEN, WEBHOOK_SECRET) w Railway Project -> Settings -> Variables
- Po deployu Railway poda publiczny URL (np. https://project-name.up.railway.app/) — to będzie adres Twojej Mini App.

Bezpieczeństwo:
- Traktuj TELEGRAM_BOT_TOKEN i WEBHOOK_SECRET jak sekrety. Nie umieszczaj ich w repo.
- Jeśli token wyciekł — rotuj go natychmiast przez @BotFather.

Dalsze kroki (opcjonalnie):
- Dodać walidację HMAC dla webhooków od procesora płatności (bardziej bezpieczna niż prosty header)
- Przenieść SQLite na Postgres w Railway dla trwałości
- Dodać testy i migracje (Flask-Migrate / Alembic)

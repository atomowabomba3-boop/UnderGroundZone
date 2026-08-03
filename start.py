from api import app

if __name__ == '__main__':
    # Run with gunicorn in production: `gunicorn start:app`
    app.run(host='0.0.0.0', port=5000)

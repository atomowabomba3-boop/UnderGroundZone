import subprocess
import time


bot = subprocess.Popen(
    [
        "python",
        "main.py"
    ]
)


time.sleep(2)


api = subprocess.Popen(
    [
        "uvicorn",
        "api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8080"
    ]
)


bot.wait()
api.wait()

from api import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

FROM python:3.11-slim

WORKDIR /app

# system deps (if needed for some packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . .

ENV PORT=5000
EXPOSE 5000

CMD ["gunicorn", "start:app", "--bind", "0.0.0.0:5000"]

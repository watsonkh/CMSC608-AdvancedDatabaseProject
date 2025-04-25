FROM python:3.11-slim

WORKDIR /app

COPY flask/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask/ .

# Expose the port that the Flask app runs on
EXPOSE 5000


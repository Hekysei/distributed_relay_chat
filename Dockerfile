FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY relay.py moderator.py ./
COPY src ./src

CMD ["python", "relay.py", "--host", "0.0.0.0", "--port", "12021"]

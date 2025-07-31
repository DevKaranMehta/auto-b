FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc postgresql-client libpq-dev python3-dev build-essential curl net-tools procps iputils-ping \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN mkdir -p /app/logs /app/uploads /app/app/static /app/app/templates

EXPOSE 8000

# Use the most reliable uvicorn startup method
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; s=socket.socket(); s.connect(('db', 5432))" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is up!"

echo "Making migrations..."
python manage.py makemigrations

echo "Running migrations..."
python manage.py migrate

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
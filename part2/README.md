# Lab Queue Service

A file-based FIFO queue implemented in Python.

## Run tests

python -m pip install -r requirements-dev.txt
python -m pytest -v

Run these commands from the part2 directory.

## Run with Docker Compose

cp .env.example .env
docker compose up -d --build --scale app=3

## API

- GET /health
- POST /join
- POST /next

## Concurrency

Three application replicas share the queue-data volume.
Nginx distributes requests across the replicas.
File locking and atomic file replacement prevent lost updates.

## Concurrency test

python tools/concurrent_join.py --url http://localhost:8000 --drain

#!/bin/sh
# Waits for the configured database to accept connections, then applies
# migrations and starts the API. Bounded retries, not an arbitrary sleep.
set -e

python <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
parsed = urlparse(url.replace("postgresql+psycopg", "postgresql"))
host = parsed.hostname or "database"
port = parsed.port or 5432

for _ in range(30):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Database reachable at {host}:{port}.")
            sys.exit(0)
    except OSError:
        time.sleep(2)

print(f"Database not reachable at {host}:{port} after waiting; continuing anyway.", file=sys.stderr)
PY

python -m alembic -c alembic.ini upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 5000

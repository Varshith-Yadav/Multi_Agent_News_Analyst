#!/bin/sh
# Start the background worker in the background
python -m app.core.worker &

# Start the FastAPI server in the foreground
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

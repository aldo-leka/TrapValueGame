#!/bin/sh
set -e

# Initialize database from bundled copy if volume is empty
if [ ! -f /shared/stocks.db ]; then
    echo "Initializing stocks.db from bundled copy..."
    mkdir -p /shared
    cp /app/shared/stocks.db /shared/stocks.db
    echo "Database initialized successfully"
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000

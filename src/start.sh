#!/bin/bash

#google-chrome \
#  --remote-debugging-port=9222 \
#  --user-data-dir=/tmp/chrome-debug \
#  --no-first-run \
#  --no-default-browser-check \
#  --disable-extensions

start_chrome() {
    set -e

    echo "Starting Chrome..."

    google-chrome \
      --remote-debugging-port=9222 \
      --user-data-dir=/tmp/chrome-debug \
      --no-first-run \
      --no-default-browser-check \
      --disable-extensions \
      >/dev/null 2>&1 &
    
    CHROME_PID=$!

    echo "Waiting for Chrome to initialize..."
    sleep 3
}

check_chrome_readiness() {
    if curl -s http://127.0.0.1:9222/json > /dev/null; then
        echo "Chrome is running and debugging port is open ✔"
        return 0
    else
        echo "Chrome failed to start ❌"
        kill "$CHROME_PID" 2>/dev/null || true
        exit 1
    fi
}

start_chrome

check_chrome_readiness

pipenv run python fetch_jobs.py

pipenv run python filter_jobs.py

fuser -k 9222/tcp >/dev/null 2>&1 || true

echo "Done."

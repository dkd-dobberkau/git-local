#!/bin/bash
# Stop git-local server

PID=$(lsof -ti:1899)

if [ -z "$PID" ]; then
    echo "git-local is not running"
else
    kill "$PID"
    echo "git-local stopped (PID $PID)"
fi

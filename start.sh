#!/bin/bash
cd "$(dirname "$0")"
uv run uvicorn git_local.main:app --host 127.0.0.1 --port 1899

#!/bin/bash
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/usr/bin/env bash
# Founder City — start the server. Loads OPENROUTER_API_KEY etc. from .env (git-ignored).
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
exec python3 -m uvicorn server:app --host 0.0.0.0 --port 8010 "$@"

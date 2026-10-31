#!/usr/bin/env python3
"""Founder City operator console: review and verify real-world claims.
Usage:  python3 fc_operator.py list
        python3 fc_operator.py verify <player_id> <mission|attest> <idx>
Reads FC_ADMIN_TOKEN from .env. The server rejects verification without it."""
import sys, os, json, sqlite3, urllib.request
R = os.path.dirname(os.path.abspath(__file__))
tok = ""
for l in open(os.path.join(R, ".env")):
    if l.startswith("FC_ADMIN_TOKEN="): tok = l.split("=", 1)[1].strip()
if len(sys.argv) < 2: sys.exit(__doc__)
if sys.argv[1] == "list":
    c = sqlite3.connect(os.path.join(R, "empire.db")); c.row_factory = sqlite3.Row
    for r in c.execute("SELECT id,handle,missions,attestations FROM players"):
        for kind, col in (("mission", "missions"), ("attest", "attestations")):
            for i, m in enumerate(json.loads(r[col] or "[]")):
                if not m.get("verified"):
                    print(f"{r['id']}  {r['handle']:<14} {kind:<8} idx={i}  {m.get('title','')}  | {(m.get('evidence') or m.get('url') or '')[:70]}")
elif sys.argv[1] == "verify" and len(sys.argv) == 5:
    pid, kind, idx = sys.argv[2], sys.argv[3], int(sys.argv[4])
    path = "missions/verify" if kind == "mission" else "attest/verify"
    req = urllib.request.Request(f"http://localhost:8010/api/players/{pid}/{path}", data=json.dumps({"idx": idx}).encode(),
                                 headers={"Content-Type": "application/json", "x-admin-token": tok}, method="POST")
    print(urllib.request.urlopen(req).read().decode()[:300])
else: sys.exit(__doc__)

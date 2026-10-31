#!/usr/bin/env python3
"""Founder City smoke + exploit regression. Run against a live server: python3 tests/smoke_test.py"""
import json, urllib.request, urllib.error, sys
B = "http://localhost:8010"
def call(m, p, b=None, h=None):
    req = urllib.request.Request(B + p, method=m); req.add_header("Content-Type", "application/json")
    for k, v in (h or {}).items(): req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, data=json.dumps(b).encode() if b is not None else None, timeout=60) as x:
            return x.status, json.loads(x.read())
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except Exception: return e.code, {}
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)
s, a = call("POST", "/api/players", {"handle": "<img src=x onerror=1>", "city": "Boise, ID"}); A = a["id"]
check("handle sanitized", "<" not in a["handle"] and ">" not in a["handle"])
s, b = call("POST", "/api/players", {"handle": "Buyer", "city": "Boise, ID"}); Bp = b["id"]
for g in ["/api/meta", "/api/stats", "/api/world", "/api/learning", "/api/missions", "/api/events", "/api/producers", "/api/econ/supply", f"/api/players/{A}", f"/api/players/{A}/coach", f"/api/players/{A}/economy", f"/api/players/{A}/wallet"]:
    check("GET " + g.split("/")[2] + ("/" + g.split("/")[-1] if g.count("/") > 2 else ""), call("GET", g)[0] == 200)
call("POST", f"/api/players/{A}/start-business", {"business_id": "steel"}); call("POST", f"/api/players/{A}/run-month")
offers = [m for m in call("GET", "/api/econ/supply")[1]["market"] if m["commodity"] == "steel"][0]["offers"]
check("producer posted surplus", len(offers) > 0)
if offers:
    check("buy negative units rejected", call("POST", f"/api/players/{Bp}/supply/buy", {"offer_id": offers[0]["offer_id"], "units": -5})[0] == 400)
check("message self rejected", call("POST", f"/api/players/{A}/message", {"to": A, "msg": "hi"})[0] == 400)
call("POST", f"/api/players/{A}/missions/submit", {"mission_id": "m_bizplan", "evidence": "x"})
check("mission double-submit rejected", call("POST", f"/api/players/{A}/missions/submit", {"mission_id": "m_bizplan", "evidence": "y"})[0] == 409)
check("self-verify mission blocked", call("POST", f"/api/players/{A}/missions/verify", {"idx": 0})[0] == 403)
check("self-verify attestation blocked", call("POST", f"/api/players/{A}/attest/verify", {"idx": 0})[0] == 403)
bid = call("GET", "/api/learning")[1]["books"][0]["id"]
check("book minutes capped", call("POST", f"/api/players/{Bp}/books/progress", {"book_id": bid, "minutes": 10**7})[1].get("xp", 99999) <= 240)
print("\n%d failure(s)" % len(fails)); sys.exit(1 if fails else 0)

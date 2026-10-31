"""
EMPIRE ONE — HTTP API + static hosting.
Run:  uvicorn server:app --host 0.0.0.0 --port 8010
Investor dashboard at /, playable game at /game.
"""
import json, os, re, sqlite3, time
from pathlib import Path
from fastapi import Request, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional

import engine as E
import payments as PAY
from data.datasets import CITIES, BUSINESSES, LEVELS, DEFAULT_START
from data import learning as LEARN

BASE = Path(__file__).parent
DB = BASE / "empire.db"
app = FastAPI(title="Founder City")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c

import hashlib as _hl, hmac as _hmac, secrets as _sec

def _pw_hash(pw, salt): return _hl.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()
def _mk_token(): return _sec.token_urlsafe(32)

def account_tables(c):
    c.execute("CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,username TEXT UNIQUE,pwd_hash TEXT,salt TEXT,created REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,account_id TEXT,created REAL)")
    cols=[r[1] for r in c.execute("PRAGMA table_info(players)").fetchall()]
    if "account_id" not in cols: c.execute("ALTER TABLE players ADD COLUMN account_id TEXT")

def register_account(username, password):
    username=(username or "").strip().lower()
    if not username or len(username)<3 or len(username)>32: raise HTTPException(400,"Username must be 3-32 characters")
    if len(password)<6: raise HTTPException(400,"Password must be at least 6 characters")
    c=db()
    if c.execute("SELECT 1 FROM accounts WHERE username=lower(?)",(username,)).fetchone():
        c.close(); raise HTTPException(409,"Username already taken")
    salt=_sec.token_hex(16); acc_id=new_id()
    c.execute("INSERT INTO accounts(id,username,pwd_hash,salt,created) VALUES(?,?,?,?,?)",
              (acc_id,username,_pw_hash(password,salt),salt,time.time()))
    tok=_mk_token(); c.execute("INSERT INTO sessions(token,account_id,created) VALUES(?,?,?)",(tok,acc_id,time.time()))
    c.commit(); c.close(); return acc_id, tok

def login_account(username, password):
    c=db(); row=c.execute("SELECT * FROM accounts WHERE username=lower(?)",(username,)).fetchone()
    if not row: c.close(); raise HTTPException(401,"Bad username or password")
    if not _hmac.compare_digest(row["pwd_hash"], _pw_hash(password, row["salt"])):
        c.close(); raise HTTPException(401,"Bad username or password")
    tok=_mk_token(); c.execute("INSERT INTO sessions(token,account_id,created) VALUES(?,?,?)",(tok,row["id"],time.time())); c.commit(); c.close()
    return tok

def account_for_token(token):
    if not token: return None
    c=db(); row=c.execute("SELECT account_id FROM sessions WHERE token=?",(token,)).fetchone(); c.close()
    return row["account_id"] if row else None

async def auth_gate(request: Request, call_next):
    path=request.url.path
    m=re.match(r"^/api/players/([^/]+)(?:/|$)", path)
    if m and path!="/api/players" and not path.startswith("/api/players/meta"):
        pid=m.group(1)
        az=request.headers.get("authorization","")
        token=az[7:] if az.lower().startswith("bearer ") else None
        acc=account_for_token(token)
        if not acc: return JSONResponse(status_code=401,content={"detail":"Please log in. Authentication is required."})
        c=db(); own=c.execute("SELECT account_id FROM players WHERE id=?",(pid,)).fetchone(); c.close()
        if not own or own["account_id"]!=acc:
            return JSONResponse(status_code=403,content={"detail":"This account does not own that player."})
    return await call_next(request)

app.middleware("http")(auth_gate)


def init_db():
    c = db()
    c.execute("""CREATE TABLE IF NOT EXISTS players(
        id TEXT PRIMARY KEY, handle TEXT, city TEXT, state TEXT, lat REAL, lon REAL,
        cash REAL, net_worth REAL, business TEXT, business_label TEXT,
        level INTEGER, deals_done INTEGER, month_global INTEGER,
        moved INTEGER DEFAULT 0, skills TEXT, passports TEXT, negotiation TEXT,
        created REAL, last_seen REAL)""")
    # roll forward new columns (idempotent)
    for col in ["wallet REAL DEFAULT 0","xp INTEGER DEFAULT 0","books TEXT DEFAULT '{}'",
                "classes TEXT DEFAULT '{}'","attestations TEXT DEFAULT '[]'",
                "payouts TEXT DEFAULT '[]'","connected TEXT",
                "relationships TEXT DEFAULT '{}'","owned TEXT DEFAULT '{}'",
                "bookings TEXT DEFAULT '[]'","meetings TEXT DEFAULT '[]'",
                "npc_memory TEXT DEFAULT '[]'","integrations TEXT DEFAULT '{}'",
                "open_contracts TEXT DEFAULT '[]'","col REAL","biz REAL",
                "linkedin TEXT DEFAULT ''","uploads TEXT DEFAULT '[]'",
                "voice_cache TEXT DEFAULT ''",
                "missions TEXT DEFAULT '[]'","mentor_card TEXT DEFAULT '{}'",
                "supply_contracts TEXT DEFAULT '[]'","producer TEXT DEFAULT ''",
                "events_history TEXT DEFAULT '[]'"]:
        cols = [r[1] for r in c.execute("PRAGMA table_info(players)").fetchall()]
        if col.split()[0] not in cols:
            c.execute("ALTER TABLE players ADD COLUMN " + col)
    c.execute("CREATE TABLE IF NOT EXISTS offers(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "owner TEXT, commodity TEXT, units INTEGER, price REAL, posted REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "sender TEXT, receiver TEXT, msg TEXT, ts REAL, read INTEGER DEFAULT 0)")
    account_tables(c)
    c.commit(); c.close()


def row_to_player(r):
    d = dict(r)
    d["skills"] = json.loads(d["skills"] or "{}")
    d["passport"] = json.loads(d["passports"] or "{}")
    d["negotiation"] = json.loads(d["negotiation"]) if d.get("negotiation") else None
    d["books"] = json.loads(d["books"] or "{}")
    d["classes"] = json.loads(d["classes"] or "{}")
    d["attestations"] = json.loads(d["attestations"] or "[]")
    d["payouts"] = json.loads(d["payouts"] or "[]")
    d["relationships"] = json.loads(d["relationships"] or "{}")
    d["owned"] = json.loads(d["owned"] or "{}")
    d["bookings"] = json.loads(d["bookings"] or "[]")
    d["meetings"] = json.loads(d["meetings"] or "[]")
    d["npc_memory"] = json.loads(d["npc_memory"] or "[]")
    d["integrations"] = json.loads(d["integrations"] or "{}")
    return d


def new_id():
    return time.strftime("%M%S") + os.urandom(2).hex()


def _post_offer(c, owner, commodity, units, price):
    """Merge into an existing (owner,commodity) offer; else insert a new one."""
    row=c.execute("SELECT id,units FROM offers WHERE owner=? AND commodity=? LIMIT 1",(owner,commodity)).fetchone()
    if row:
        c.execute("UPDATE offers SET units=units+?, price=?, posted=? WHERE id=?",(units,price,time.time(),row["id"]))
    else:
        c.execute("INSERT INTO offers(owner,commodity,units,price,posted) VALUES(?,?,?,?,?)",(owner,commodity,units,price,time.time()))

def _consumer_demand(c, commodity):
    """Units of a commodity demanded monthly by all consumer businesses."""
    import data.econ as EC
    total=0
    rows=c.execute("SELECT business FROM players WHERE business IS NOT NULL AND business<>''").fetchall()
    for rr in rows:
        ind=EC.BIZ_TO_INDUSTRY.get(rr["business"])
        if ind and commodity in (EC.INDUSTRIES.get(ind,{}) or {}).get("inputs") if ind else ():
            total += 90
    return total


def PAY_STAT():
    return PAY.status()


# --------------------------------------------------------------------- players
import re as _re
def clean_handle(h):
    h=_re.sub(r"[^A-Za-z0-9 _.\-]","",(h or "")).strip()[:24]
    return h or ("founder-"+str(int(time.time())%1000))

class PlayerCreate(BaseModel):
    handle: str
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    username: Optional[str] = None
    password: Optional[str] = None

class AuthBody(BaseModel):
    username: str
    password: str

@app.get("/api/nation/nearest")
def nearest(lat: float, lon: float):
    import nation as NA
    m,dist=NA.nearest_city(lat,lon)
    return {"city":m["n"],"state":m.get("s"),"lat":m["la"],"lon":m["lo"],"distance_km":round(dist)}


@app.post("/api/players")
def create_player(pc: PlayerCreate):
    import nation as NA
    pc.handle=clean_handle(pc.handle)
    cstate=None; col_ix=None; biz_ix=None
    if pc.city and pc.city.strip():
        _c=pc.city.strip()
        if "," in _c:
            nm,st=[x.strip() for x in _c.rsplit(",",1)]; m=NA.match_city(nm,st)
        else:
            m=NA.match_city(_c)
        if m: city,cstate=m["n"],m.get("s")
        else: city,cstate=_c,"US"
    elif pc.lat is not None and pc.lon is not None:
        m,dist=NA.nearest_city(pc.lat,pc.lon); city,cstate=m["n"],m.get("s")
    else:
        m=NA.match_city("New York","NY"); city,cstate=m["n"],m.get("s")
    if city in E.CITY and cstate in ("NY","CA","TX","IL","FL"):
        col_ix=E.CITY[city][4]; biz_ix=E.CITY[city][5]
    else:
        col_ix,biz_ix=NA.econ(city, cstate)
    mm=NA.match_city(city, cstate)
    _la,_lo=(mm["la"],mm["lo"]) if mm else (39.0,-99.0)
    pid=new_id(); c=db()
    cols=("id,handle,city,state,lat,lon,cash,net_worth,business,business_label,"
          "level,deals_done,month_global,moved,skills,passports,negotiation,"
          "wallet,xp,books,classes,attestations,payouts,connected,col,biz,"
          "created,last_seen").split(",")
    vals=(pid, pc.handle[:24], city, cstate or "US", _la, _lo,
          DEFAULT_START, DEFAULT_START, None, None, 1, 0, 1, 0,
          json.dumps(E.seed_skills()),
          json.dumps({"industry":"New Founder","verified":False,"interests":[],"network":[]}),
          None, 0.0, 0, json.dumps({}), json.dumps({}),
          json.dumps([]), json.dumps([]), None, col_ix, biz_ix,
          time.time(), time.time())
    assert len(cols)==len(vals),(len(cols),len(vals))
    c.execute(f"INSERT INTO players({','.join(cols)}) VALUES({','.join(['?']*len(cols))})", vals)
    c.commit(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    out=row_to_player(r)
    if pc.username and pc.password:
        acc_id, tok = register_account(pc.username, pc.password)
        c.execute("UPDATE players SET account_id=? WHERE id=?",(acc_id,pid)); c.commit()
        out=dict(out); out["token"]=tok
    c.close()
    return out


@app.get("/api/players/{pid}")
def get_player(pid: str):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    if not r: raise HTTPException(404, "player not found")
    return row_to_player(r)


class Relocate(BaseModel):
    target: str
@app.post("/api/players/{pid}/relocate")
def relocate(pid: str, body: Relocate):
    import nation as NA
    c = db()
    r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    # parse "City, ST"
    _t=body.target.strip()
    if "," in _t:
        nm,st=[x.strip() for x in _t.rsplit(",",1)]
    else:
        nm,st=_t,None
    m=NA.match_city(nm, st)
    if not m: c.close(); raise HTTPException(400,"Unknown US city. Try 'City, ST' (e.g. 'Boise, ID').")
    tcity, tstate = m["n"], m.get("s") or "US"
    if tcity==r["city"] and r["state"]==tstate: c.close(); raise HTTPException(400,"You're already there.")
    cost=NA.relocation_cost_na(r["city"], r["state"], tcity, tstate)
    if cost is None: c.close(); raise HTTPException(400,"Cannot compute relocation.")
    if r["cash"] < cost:
        c.close()
        raise HTTPException(400, f"Need ${cost:,} to relocate — you have ${r['cash']:,.0f}. Earn more first. That's the 'from your capital you move' rule.")
    if tcity in E.CITY and tstate in ("NY","CA","TX","IL","FL"):
        ncol,nbiz=E.CITY[tcity][4],E.CITY[tcity][5]
    else:
        ncol,nbiz=NA.econ(tcity, tstate)
    npv=r["net_worth"]-cost
    c.execute("""UPDATE players SET city=?, state=?, lat=?, lon=?, col=?, biz=?,
                cash=cash-?, net_worth=?, moved=moved+1, last_seen=? WHERE id=?""",
              (tcity, tstate, m["la"], m["lo"], ncol, nbiz, cost, npv, time.time(), pid))
    c.commit()
    rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {**row_to_player(rr), "relocated": True, "cost": cost}





class StartBiz(BaseModel):
    business_id: str
@app.post("/api/players/{pid}/start-business")
def start_business(pid: str, body: StartBiz):
    import data.econ as EC
    producer = body.business_id in EC.PRODUCERS
    if body.business_id not in E.BIZ and not producer: raise HTTPException(400, "unknown business")
    label = EC.PRODUCERS[body.business_id]["name"] if producer else E.BIZ[body.business_id][1]
    cost = EC.PRODUCERS[body.business_id]["setup_cost"] if producer else E.BIZ[body.business_id][3]
    c = db()
    r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    if r["business"]: raise HTTPException(400, "already running a business")
    if r["cash"] < cost:
        c.close()
        raise HTTPException(400, f"Need ${cost:,} to start {label} — you have ${r['cash']:,.0f}.")
    c.execute("""UPDATE players SET business=?, business_label=?, producer=?, cash=cash-?,
                net_worth=net_worth-?, last_seen=? WHERE id=?""",
              (body.business_id, label, ("1" if producer else ""), cost, cost, time.time(), pid))
    c.commit()
    rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return row_to_player(rr)


@app.post("/api/players/{pid}/run-month")
def run_month(pid: str):
    c = db()
    r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    if not r["business"]: raise HTTPException(400, "start a business first")
    import data.econ as EC
    if r["business"] in EC.PRODUCERS:
        pr=EC.PRODUCERS[r["business"]]
        price=round(EC.commodity_price(pr["output"], r["month_global"])*1.08,3)
        dem=EC.base_demand(pr["output"], r["month_global"])+_consumer_demand(c, pr["output"])
        sim=EC.producer_monthly(r["business"], r["city"], r["month_global"], price,
                                col_ix=r["col"] or 100, biz_ix=r["biz"] or 50, demand_units=dem)
        if sim["unsold"]>0:
            _post_offer(c, pid, pr["output"], int(sim["unsold"]), price)
    else:
        _ind = EC.BIZ_TO_INDUSTRY.get(r["business"]) or "ecom"
        mm = EC.materials_mod(_ind, r["month_global"])
        if json.loads(r["supply_contracts"] or "[]"):
            mm = round(mm * 0.93, 3)
        sim = E.monthly_sim(r["business"], r["city"], r["month_global"],
                            seed=int(time.time()) % 1_000_000, cash=r["cash"],
                            col_ix=r["col"] or 100, biz_ix=r["biz"] or 50, materials_mod=mm)
    cash2 = r["cash"] + sim["net"]
    npv2 = r["net_worth"] + sim["net"]
    level = E.recompute_level(r["xp"], r["deals_done"])
    c.execute("""UPDATE players SET cash=?, net_worth=?, month_global=month_global+1,
                level=?, last_seen=? WHERE id=?""", (cash2, npv2, level, time.time(), pid))
    c.commit()
    rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    data = row_to_player(rr); c.close()
    return {**data, "month": sim}


# --------------------------------------------------------------------- negotiation
class NegStart(BaseModel):
    deal_id: str = "supplier"
@app.post("/api/players/{pid}/negotiate/start")
def neg_start(pid: str, body: NegStart):
    if body.deal_id not in E.DEALS: raise HTTPException(400, "unknown deal")
    seed = int(time.time()) % 1_000_000
    neg = E.negotiate(body.deal_id, seed)
    c = db()
    c.execute("UPDATE players SET negotiation=?, last_seen=? WHERE id=?",
              (json.dumps(neg), time.time(), pid)); c.commit(); c.close()
    return neg


def _load_neg(c, pid):
    r = c.execute("SELECT negotiation FROM players WHERE id=?", (pid,)).fetchone()
    if not r or not r["negotiation"]: raise HTTPException(409, "no active negotiation")
    return json.loads(r["negotiation"])

class Ask(BaseModel):
    qid: str
@app.post("/api/players/{pid}/negotiate/ask")
def neg_ask(pid: str, body: Ask):
    c = db(); neg = _load_neg(c, pid)
    neg, out = E.ask(neg, body.qid)
    c.execute("UPDATE players SET negotiation=?, last_seen=? WHERE id=?", (json.dumps(neg), time.time(), pid))
    c.commit(); c.close()
    return out

class Offer(BaseModel):
    amount: float
@app.post("/api/players/{pid}/negotiate/offer")
def neg_offer(pid: str, body: Offer):
    c = db(); neg = _load_neg(c, pid)
    neg, out = E.offer(neg, round(body.amount))
    c.execute("UPDATE players SET negotiation=?, last_seen=? WHERE id=?",
              (json.dumps(neg), time.time(), pid))
    c.commit(); c.close()
    return out

@app.post("/api/players/{pid}/negotiate/counter")
def neg_counter(pid: str):
    c = db(); neg = _load_neg(c, pid)
    final = neg["anchor"]
    deal = E.DEALS[neg["deal_id"]]
    c.execute("UPDATE players SET negotiation=?, last_seen=? WHERE id=?",
              (json.dumps({**neg, "status": "accepted", "final_price": final}), time.time(), pid))
    c.commit(); c.close()
    return {"reply": f"You accept {final/1000:.0f}k.", "type": "result", "status": "accepted", "price": final,
            "true_value": deal["true_value"]}


@app.post("/api/players/{pid}/negotiate/close")
def neg_close(pid: str):
    c = db()
    neg = _load_neg(c, pid)
    r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    deal = E.DEALS[neg["deal_id"]]
    true = deal["true_value"]
    final = neg.get("final_price") or (neg["offers"][-1] if neg["offers"] else None)
    review = E.coach_review(neg)

    if final is not None and neg["status"] == "accepted":
        captured = true - final
        down = min(final * 0.04, r["cash"] * 0.5)
        value_change = round(captured * 0.5)
        cash2 = r["cash"] - down
        npv2 = max(0, r["net_worth"] - down + value_change)
        gain = value_change - down
    else:
        cash2, npv2, down, gain = r["cash"], r["net_worth"], 0, 0

    deals = r["deals_done"] + (1 if neg["status"] == "accepted" else 0)
    # deals also grant XP + wallet money
    deal_xp = 1200 if neg["status"] == "accepted" else 150
    deal_cash = 900 if neg["status"] == "accepted" else 0
    xp = r["xp"] + (1200 if neg["status"] == "accepted" else 150)
    wallet = r["wallet"] + deal_cash

    skills = json.loads(r["skills"])
    skills["negotiation"] = round((skills["negotiation"] + review["negotiation"]) / 2)
    skills["finance"] = round((skills["finance"] + review["diligence"]) / 2)
    passport = json.loads(r["passports"])
    passport["industry"] = r["business_label"] or deal["title"]
    passport["verified"] = True
    passport["reputation"] = round((passport.get("reputation", 0) + review["score"]) / 2)
    passport["network"].append({"with": deal["title"], "kind": "business", "rating": review["score"]})
    level = E.recompute_level(xp, deals)

    c.execute("""UPDATE players SET cash=?, net_worth=?, deals_done=?, level=?,
                negotiation=?, skills=?, passports=?, xp=?, wallet=?, last_seen=? WHERE id=?""",
              (cash2, npv2, deals, level, json.dumps({**neg, "closed": True}),
               json.dumps(skills), json.dumps(passport), xp, wallet, time.time(), pid))
    c.commit()
    rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {"review": review, "deal": deal["title"], "final_price": final, "true_value": true,
            "financial": {"gain": round(gain), "down_payment": round(down),
                          "cash_after": round(cash2), "net_worth_after": round(npv2),
                          "xp_gained": deal_xp, "wallet_gained": deal_cash},
            "player": row_to_player(rr)}


# --------------------------------------------------------------------- investor dashboard
@app.get("/api/stats")
def stats():
    c = db()
    n = c.execute("SELECT COUNT(*) q FROM players").fetchone()["q"]
    tot = c.execute("SELECT COALESCE(SUM(net_worth),0) s FROM players").fetchone()["s"]
    wallet = c.execute("SELECT COALESCE(SUM(wallet),0) s FROM players").fetchone()["s"]
    moved = c.execute("SELECT COALESCE(SUM(moved),0) s FROM players").fetchone()["s"]
    deals = c.execute("SELECT COALESCE(SUM(deals_done),0) s FROM players").fetchone()["s"]
    books = c.execute("SELECT COUNT(*) FROM players WHERE length(COALESCE(books,'{}')) > 2").fetchone()[0]
    top = c.execute("SELECT handle,city,net_worth,level,xp FROM players ORDER BY net_worth DESC LIMIT 10").fetchall()
    bycity = c.execute("SELECT city, COUNT(*) q FROM players GROUP BY city ORDER BY q DESC LIMIT 12").fetchall()
    c.close()
    return {"empires": n, "total_net_worth": round(tot), "total_wallet": round(wallet),
            "relocations": moved, "deals_done": deals, "books_started": books,
            "leaderboard": [dict(x) for x in top], "cities": [dict(x) for x in bycity]}


@app.get("/")
def landing(): return FileResponse(BASE / "static" / "index.html")
@app.get("/game")
def game(): return FileResponse(BASE / "static" / "game.html")
@app.get("/_health")
def health(): return JSONResponse({"ok": True, "t": time.time()})

@app.get("/api/meta")
def meta():
    cities = [{"name": c[0], "state": c[1], "lat": c[2], "lon": c[3],
               "col": c[4], "biz": c[5], "pop": c[6]} for c in CITIES]
    biz = [{"id": b[0], "name": b[1], "category": b[2], "cost": b[3],
            "margin": b[4], "demand": b[5], "blurb": b[6]} for b in BUSINESSES]
    levels = [{"n": l[0], "title": l[1], "blurb": l[2]} for l in LEVELS]
    return {"cities": cities, "businesses": biz, "levels": levels, "start": DEFAULT_START}


# --------------------------------------------------------------------- learning / growth / money
@app.get("/api/learning")
def learning_meta():
    return {"books": [dict(zip(["id","title","author","category","hours","skills","cash"],
                               [b[0],b[1],b[2],b[3],b[4],b[5],b[6]])) for b in LEARN.BOOKS],
            "classes": [dict(zip(["id","title","category","minutes","skills","cash","exercise"],
                                 [c[0],c[1],c[2],c[3],c[4],c[5],c[6]])) for c in LEARN.CLASSES],
            "all_skills": E.ALL_SKILLS,
            "audible_search": "https://www.audible.com/search?keywords=",
            "payments": PAY_STAT()}


def _load_books(c, pid):
    r = c.execute("SELECT books FROM players WHERE id=?", (pid,)).fetchone()
    return json.loads(r[0] or '{}')


class BookProgress(BaseModel):
    book_id: str; minutes: float = 10
@app.post("/api/players/{pid}/books/progress")
def book_progress(pid: str, body: BookProgress):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    if body.book_id not in E.BOOK: raise HTTPException(400, "unknown book")
    books = _load_books(c, pid)
    b = books.get(body.book_id, {})
    skills = json.loads(r["skills"])
    mins = max(0.0, min(float(body.minutes), 240.0))               # cap one log at 4h
    mins = min(mins, max(0.0, E.BOOK[body.book_id][4]*60 - b.get("minutes", 0)))  # no XP beyond book length
    res = E.book_progress(body.book_id, mins, b.get("minutes", 0), skills)
    books[body.book_id] = dict(b, minutes=res["minutes"])
    xp = r["xp"] + res["xp"]; cash = r["cash"] + res["cash"]; wallet = r["wallet"] + res["cash"]
    lvl = E.recompute_level(xp, r["deals_done"])
    c.execute("UPDATE players SET books=?,skills=?,xp=?,cash=?,wallet=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(books), json.dumps(skills), xp, cash, wallet, lvl, time.time(), pid))
    c.commit(); rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {**res, "player": row_to_player(rr)}


class ClassDone(BaseModel):
    class_id: str; score: float = 70
@app.post("/api/players/{pid}/classes/complete")
def class_done(pid: str, body: ClassDone):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    if body.class_id not in E.CLASS: raise HTTPException(400, "unknown class")
    classes = json.loads(r["classes"] or "{}")
    if classes.get(body.class_id, {}).get("done"): raise HTTPException(400, "already completed")
    skills = json.loads(r["skills"])
    score = max(0, min(100, float(body.score)))
    res = E.class_complete(body.class_id, score, skills)
    classes[body.class_id] = {"done": True, "score": score}
    xp = r["xp"] + res["xp"]; cash = r["cash"] + res["cash"]; wallet = r["wallet"] + res["cash"]
    lvl = E.recompute_level(xp, r["deals_done"])
    c.execute("UPDATE players SET classes=?,skills=?,xp=?,cash=?,wallet=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(classes), json.dumps(skills), xp, cash, wallet, lvl, time.time(), pid))
    c.commit(); rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {**res, "player": row_to_player(rr)}


class Attest(BaseModel):
    title: str; url: str; description: str = ""
@app.post("/api/players/{pid}/attest")
def attest(pid: str, body: Attest):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r or not body.title: raise HTTPException(404, "not found / title required")
    att = json.loads(r["attestations"] or "[]")
    att.append({"title": body.title[:80], "url": body.url[:200], "description": body.description[:400],
                "verified": False, "xp": 0, "cash": 0, "time": time.time()})
    c.execute("UPDATE players SET attestations=?,last_seen=? WHERE id=?",
              (json.dumps(att), time.time(), pid))
    c.commit(); rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {"player": row_to_player(rr),
            "note": "Real-world project submitted. A sponsor must verify it before it pays XP + money."}



def require_operator(request: Request):
    tok=os.environ.get("FC_ADMIN_TOKEN","")
    if not tok: raise HTTPException(403,"Verification is operator-only and no operator token is configured.")
    if request.headers.get("x-admin-token","")!=tok: raise HTTPException(403,"Operator token required to verify real-world claims.")

class VerifyAttest(BaseModel):
    idx: int
@app.post("/api/players/{pid}/attest/verify")
def attest_verify(pid: str, body: VerifyAttest, request: Request):
    require_operator(request)
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    att = json.loads(r["attestations"] or "[]")
    if body.idx >= len(att) or att[body.idx]["verified"]: raise HTTPException(400, "bad idx / already verified")
    att[body.idx].update({"verified": True, "xp": 2500, "cash": 3000})
    xp = r["xp"] + 2500; cash = r["cash"] + 3000; wallet = r["wallet"] + 3000
    lvl = E.recompute_level(xp, r["deals_done"])
    c.execute("UPDATE players SET attestations=?,xp=?,cash=?,wallet=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(att), xp, cash, wallet, lvl, time.time(), pid))
    c.commit(); rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {"player": row_to_player(rr), "granted": {"xp": 2500, "cash": 3000}}


class PayoutC(BaseModel):
    processor: str; account: str
@app.post("/api/players/{pid}/payout/connect")
def payout_connect(pid: str, body: PayoutC):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    res = PAY.connect_account(r, body.processor, body.account)
    if res["ok"]:
        c.execute("UPDATE players SET connected=?,last_seen=? WHERE id=?",
                  (json.dumps(res), time.time(), pid)); c.commit()
    c.close(); return res


class PayoutReq(BaseModel):
    processor: str; amount_cents: int; account: str = ""
@app.post("/api/players/{pid}/payout/request")
def payout_request(pid: str, body: PayoutReq):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "not found")
    wallet_cents = int(r["wallet"] * 100)
    if body.amount_cents <= 0 or body.amount_cents > wallet_cents:
        c.close()
        raise HTTPException(400, f"Amount must be between $0.01 and your ${r['wallet']:.2f} wallet.")
    account = body.account or (json.loads(r["connected"] or '{}') if r["connected"] else {}).get("account", "")
    res = PAY.request_payout(r, body.processor, body.amount_cents, account)
    payouts = json.loads(r["payouts"] or "[]")
    record = {"processor": body.processor, "amount_cents": body.amount_cents, "status": res["status"],
              "ref": res.get("provider_ref"), "error": res.get("error"), "time": time.time()}
    payouts.append(record)
    # never reduce the in-game wallet until the provider has actually paid
    if res["status"] in ("paid", "submitted"):
        c.execute("UPDATE players SET wallet=wallet-?,payouts=?,last_seen=? WHERE id=?",
                  (body.amount_cents / 100, json.dumps(payouts), time.time(), pid))
    else:
        c.execute("UPDATE players SET payouts=?,last_seen=? WHERE id=?",
                  (json.dumps(payouts), time.time(), pid))
    c.commit(); rr = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    return {"payout": res, "wallet_after": row_to_player(rr)["wallet"]}


@app.get("/api/players/{pid}/wallet")
def wallet(pid: str):
    c = db(); r = c.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone(); c.close()
    if not r: raise HTTPException(404, "not found")
    p = row_to_player(r)
    return {"wallet": p["wallet"], "xp": p["xp"], "deals": p["deals_done"], "level": p["level"],
            "payouts": p["payouts"], "attestations": p["attestations"]}


@app.get("/api/payments/status")
def pay_status(): return PAY_STAT()

# --------------------------------------------------------------------- living world
import llm as LLM
def LLM_ON(): return LLM.configured()

@app.get("/api/world")
def world_meta():
    from data import market as MK
    return {"companies": [dict(zip(["id","name","sector","rep","blurb"],c)) for c in MK.NPC_COMPANIES],
            "contracts": [dict(zip(["id","company","title","service","service_label","skills_used","budget","difficulty","days"],
                                   [c[0],c[1],c[2],c[3],E.SERVICE_LABEL.get(c[3],c[3]),c[4],c[5],c[6],c[7]])) for c in MK.CONTRACTS],
            "coaches":   [dict(zip(["id","name","title","specialty","rate","bio"],c)) for c in MK.COACHES],
            "listings":  [dict(zip(["id","name","sector","price","revenue","margin","verified","kind","note"],
                                   [b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8]])) for b in MK.LISTINGS],
            "llm": LLM_ON(), "services": E.SERVICE_LABEL}

@app.get("/api/players/{pid}/work")
def work(pid: str):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    rel=json.loads(r["relationships"] or "{}")
    taken=json.loads(r["open_contracts"] or "[]")
    c.close()
    all_ids=[cc[0] for cc in __contracts()]
    avail=[E.contract_take(i) for i in sorted(set(all_ids)-set(taken))]
    comps=[{"id":k,"name":E.COMPANY[k][1],"sector":E.COMPANY[k][2],"rep":v["rel"],"done":v["done"]}
           for k,v in rel.items() if k in E.COMPANY]
    return {"relationships":rel,"available":avail,"taken":taken,"companies":comps}

def __contracts():
    from data import market as MK
    return MK.CONTRACTS

class Take(BaseModel): contract_id: str
@app.post("/api/players/{pid}/work/take")
def work_take(pid: str, body: Take):
    if body.contract_id not in E.CONTRACT: raise HTTPException(400,"unknown contract")
    c=db(); r=c.execute("SELECT open_contracts FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    taken=json.loads(r[0] or "[]")
    if body.contract_id in taken: raise HTTPException(409,"already taken")
    taken.append(body.contract_id)
    c.execute("UPDATE players SET open_contracts=?,last_seen=? WHERE id=?",(json.dumps(taken),time.time(),pid))
    c.commit(); c.close()
    return {"taken":body.contract_id,"contract":E.contract_take(body.contract_id)}

class Complete(BaseModel): contract_id: str
@app.post("/api/players/{pid}/work/complete")
def work_complete(pid: str, body: Complete):
    if body.contract_id not in E.CONTRACT: raise HTTPException(400,"unknown contract")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    if body.contract_id not in json.loads(r["open_contracts"] or "[]"): raise HTTPException(409,"take the contract first")
    skills=json.loads(r["skills"]); rel=json.loads(r["relationships"])
    comp=E.CONTRACT[body.contract_id][1]; cur=rel.get(comp,{"rel":0,"done":0})
    res=E.contract_complete(body.contract_id, skills, cur["rel"])
    rel[comp]={"rel":res["rel_after"],"done":cur["done"]+1}
    taken=[x for x in json.loads(r["open_contracts"] or "[]") if x!=body.contract_id]
    cash=r["cash"]+res["pay"]; wallet=r["wallet"]+res["pay"]; xp=r["xp"]+res["xp"]
    lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET relationships=?,open_contracts=?,cash=?,wallet=?,xp=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(rel),json.dumps(taken),cash,wallet,xp,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {**res,"player":row_to_player(rr)}

@app.get("/api/players/{pid}/market")
def market(pid: str):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    owned=json.loads(r["owned"] or "{}"); c.close()
    return {"wallet":r["wallet"],"owned":owned}

class Buy(BaseModel): listing_id: str
@app.post("/api/players/{pid}/market/buy")
def market_buy(pid: str, body: Buy):
    if body.listing_id not in E.LISTING: raise HTTPException(400,"unknown listing")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    owned=json.loads(r["owned"] or "{}")
    if body.listing_id in owned: raise HTTPException(409,"you already own this rights")
    chk=E.buy_listing_ok(r, body.listing_id, r["wallet"], r["net_worth"])
    if not chk["ok"]: c.close(); raise HTTPException(400, chk["error"])
    price=chk["price"]; wallet=r["wallet"]-price
    owned[body.listing_id]={"since":time.time(),"price":price,"name":chk["name"]}
    npv=r["net_worth"]+price; xp=r["xp"]+1500; lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET owned=?,wallet=?,net_worth=?,xp=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(owned),wallet,npv,xp,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"bought":chk["name"],"price":price,"wallet_after":wallet,
            "note":"Rights recorded in-game. Real equity settlement completes through Stripe/PayPal once matching credentials are live.",
            "player":row_to_player(rr)}

@app.get("/api/players/{pid}/coaches")
def coaches(pid: str):
    c=db(); r=c.execute("SELECT bookings FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"bookings":json.loads(r[0] or "[]") if r else []}

class Book(BaseModel): coach_id: str
@app.post("/api/players/{pid}/coaches/book")
def coach_book(pid: str, body: Book):
    if body.coach_id not in E.COACH: raise HTTPException(400,"unknown coach")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    coach=E.coach_book(body.coach_id)
    if r["wallet"] < coach["rate"]: c.close(); raise HTTPException(400,f"Need ${coach['rate']} (1hr). You have ${r['wallet']:.0f} in earned wallet.")
    bookings=json.loads(r["bookings"] or "[]")
    wallet=r["wallet"]-coach["rate"]
    bookings.append({"coach":coach["name"],"title":coach["title"],"specialty":coach["specialty"],
                     "rate":coach["rate"],"status":"booked·awaiting settlement","time":time.time()})
    xp=r["xp"]+600; lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET bookings=?,wallet=?,xp=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(bookings),wallet,xp,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"booking":bookings[-1],"wallet_after":wallet,
            "note":"Session booked & charged to your earned wallet. Stripe/PayPal settlement activates when live credentials are set.",
            "player":row_to_player(rr)}

class Integrate(BaseModel): platform: str; value: str
@app.post("/api/players/{pid}/integrations/connect")
def integ_connect(pid: str, body: Integrate):
    c=db(); r=c.execute("SELECT integrations FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    integ=json.loads(r[0] or "{}"); integ[body.platform]=body.value
    c.execute("UPDATE players SET integrations=?,last_seen=? WHERE id=?",(json.dumps(integ),time.time(),pid))
    c.commit(); c.close()
    return {"ok":True,"platform":body.platform,"note":f"{body.platform} connected (link/webhook stored). Active when you use it."}

class Meeting(BaseModel):
    title: str; platform: str="Google Meet"; notes: str=""; participants: int=1
@app.post("/api/players/{pid}/integrations/log-meeting")
def log_meeting(pid: str, body: Meeting):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    meetings=json.loads(r["meetings"] or "[]"); mem=json.loads(r["npc_memory"] or "[]")
    rec={"title":body.title[:80],"platform":body.platform,"notes":body.notes[:500],
         "participants":max(1,body.participants),"time":time.time()}
    meetings.append(rec)
    conn_xp=350*max(1,body.participants)
    xp=r["xp"]+conn_xp; lvl=E.recompute_level(xp,r["deals_done"])
    mem.append(f"{body.title} ({body.platform}) with {max(1,body.participants)} person(s)")
    if len(mem)>8: mem=mem[-8:]
    c.execute("UPDATE players SET meetings=?,npc_memory=?,xp=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(meetings),json.dumps(mem),xp,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"xp_gained":conn_xp,"meeting":rec,"player":row_to_player(rr),
            "note":"Meeting logged & folded into your NPC mentor's knowledge. Every real connection earns XP."}

@app.get("/api/players/{pid}/integrations")
def integ(pid: str):
    c=db(); r=c.execute("SELECT integrations,meetings FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"integrations":json.loads(r[0] or "{}"),"meetings":json.loads(r[1] or "[]")}

class MentorQ(BaseModel): question: str
@app.post("/api/players/{pid}/mentor")
def mentor(pid: str, body: MentorQ):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    mem=json.loads(r["npc_memory"] or "[]")
    ans=E.npc_mentor(body.question, mem, LLM_ON())
    xp=r["xp"]+25
    c.execute("UPDATE players SET xp=?,last_seen=? WHERE id=?",(xp,time.time(),pid)); c.commit(); c.close()
    return {**ans,"you_got_xp":25}

init_db()
# --------------------------------------------------------------------- nation / characters / network / reading
import nation as NA
class SearchQ(BaseModel): q: str
@app.get("/api/nation/search")
def nation_search(q: str = ""):
    q=q.strip().upper()
    if not q: return {"results":[]}
    _state=""
    if "," in q:
        parts=q.rsplit(",",1); q=parts[0].strip(); _state=parts[1].strip()
    def _go(q):
        out=[]; seen=set()
        for c in NA.CITIES:
            nm=c["n"].upper()
            if nm.startswith(q) or (len(q)>=3 and q in nm):
                if _state and c["s"]!=_state: continue
                out.append({"name":c["n"],"state":c["s"],"la":c["la"],"lo":c["lo"],
                            "biz":NA.biz_index(c["n"],c["s"])}); seen.add(c["n"]+c["s"])
                if len(out)>=20: break
        if _state and len(out)<20:
            for c in NA.CITIES:
                if c["s"].upper()==_state and (c["n"]+c["s"]) not in seen:
                    out.append({"name":c["n"],"state":c["s"],"la":c["la"],"lo":c["lo"],
                                "biz":NA.biz_index(c["n"],c["s"])}); seen.add(c["n"]+c["s"])
                    if len(out)>=20: break
        return out
    return {"results":_go(q)}

@app.get("/api/nation/city")
def nation_city(name: str, state: str = ""):
    m=NA.match_city(name, state)
    if not m: raise HTTPException(404,"City not found. Try 'City, ST' q into /api/nation/search.")
    col,biz=NA.econ(m["n"], m["s"])
    return {"city":m["n"],"state":m["s"],"la":m["la"],"lo":m["lo"],
            "col":col,"biz":biz,
            "local_businesses":NA.local_businesses(m["n"], m["s"]),
            "corporations":NA.city_corporations(m["n"], m["s"]),
            "characters":[{"id":c[0],"name":c[1],"role":c[2],"company":c[3],"personality":c[4],"specialty":c[6]} for c in NA.CHARACTERS]}

class CharAsk(BaseModel): character_id: str; question: str
@app.post("/api/players/{pid}/characters/ask")
def char_ask(pid: str, body: CharAsk):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    xp=r["xp"]+30
    c.execute("UPDATE players SET xp=?,last_seen=? WHERE id=?",(xp,time.time(),pid)); c.commit(); c.close()
    res=NA.business_person(body.character_id, body.question)
    return {**res,"you_got_xp":30}

class Speq(BaseModel): character_id: str; text: str
@app.post("/api/players/{pid}/characters/speak")
def char_speak(pid: str, body: Speq):
    import nation
    ch = next((c for c in nation.CHARACTERS if c[0]==body.character_id), nation.CHARACTERS[0])
    voice = nation.elevenlabs_speak(body.text or "Hello, I'm ready to do business.", ch[5])
    return {"ok":voice["ok"],"audio":voice.get("audio"),"character":ch[1],
            "error":voice.get("error"),"fallback_text":body.text,
            "note":voice["ok"] and "ElevenLabs voice generated." or (voice.get("error") or "")}

class Lin(BaseModel): url: str
@app.post("/api/players/{pid}/linkedin")
def linkedin(pid: str, body: Lin):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    # linking a real professional profile grants XP; verification/handshake is a later gate
    xp=r["xp"]+800; lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET linkedin=?,xp=?,level=?,last_seen=? WHERE id=?",
              (body.url[:200],xp,lvl,time.time(),pid)); c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"xp_gained":800,"linkedin":body.url[:200],
            "note":"LinkedIn linked. Real profile handshake verification comes with account auth.",
            "player":row_to_player(rr)}

@app.get("/api/players/{pid}/network/matches")
def matches(pid: str):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    rows=c.execute("SELECT id,handle,city,state,level,xp FROM players WHERE id!=?",(pid,)).fetchall()
    c.close()
    base=max(100, r["xp"])
    band=[dict(x) for x in rows if abs(x["xp"]-r["xp"]) <= 0.15*base]
    return {"my_xp":r["xp"],"band":band}

class Msg(BaseModel): to: str; msg: str=Field(min_length=1,max_length=500)
@app.post("/api/players/{pid}/message")
def send_msg(pid: str, body: Msg):
    c=db(); r=c.execute("SELECT handle FROM players WHERE id=?",(pid,)).fetchone()
    if body.to==pid: c.close(); raise HTTPException(400,"You can't message yourself.")
    dest=c.execute("SELECT id FROM players WHERE id=?",(body.to,)).fetchone()
    if not r or not dest: c.close(); raise HTTPException(404,"player not found")
    # visibility gate: can only message someone within your XP band
    src=c.execute("SELECT xp FROM players WHERE id=?",(pid,)).fetchone()
    dst=c.execute("SELECT xp FROM players WHERE id=?",(body.to,)).fetchone()
    base=max(100,src[0])
    if abs(src[0]-dst[0]) > 0.15*base:
        c.close(); raise HTTPException(403,"Player is outside your XP band. Earn XP and reconnect when you're in their range.")
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,sender TEXT,receiver TEXT,msg TEXT,ts REAL,read INTEGER DEFAULT 0)")
    c.execute("INSERT INTO messages(sender,receiver,msg,ts) VALUES(?,?,?,?)",(pid,body.to,body.msg[:500],time.time()))
    c.commit(); c.close()
    return {"ok":True,"to":body.to}

@app.get("/api/players/{pid}/inbox")
def inbox(pid: str):
    c=db()
    c.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,sender TEXT,receiver TEXT,msg TEXT,ts REAL,read INTEGER DEFAULT 0)")
    rows=c.execute("""SELECT m.id,m.sender,m.msg,m.ts,p.handle AS from_handle FROM messages m
                      LEFT JOIN players p ON p.id=m.sender WHERE m.receiver=? ORDER BY m.ts DESC LIMIT 30""",(pid,)).fetchall()
    c.close()
    return {"messages":[dict(x) for x in rows]}

class ReadTest(BaseModel): book_id: str; score: float
@app.post("/api/players/{pid}/reading/test")
def reading_test(pid: str, body: ReadTest):
    if body.book_id not in E.BOOK: raise HTTPException(400,"unknown book")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    books=json.loads(r["books"] or "{}"); b=books.get(body.book_id,{})
    if b.get("test_done"): c.close(); raise HTTPException(409,"already certified this book")
    score=max(0,min(100,float(body.score)))
    passed = score>=70
    skills=json.loads(r["skills"])
    deltas=E.BOOK[body.book_id][5]
    if passed:
        skills=E.add_skill(skills, deltas)
        cash=round(E.BOOK[body.book_id][6])
        xp=r["xp"]+900; wallet=r["wallet"]+cash
    else:
        skills=skills; cash=0; xp=r["xp"]+150; wallet=r["wallet"]
    b["test_done"]=True; b["test_score"]=score
    books[body.book_id]=b
    lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET books=?,skills=?,xp=?,cash=?,wallet=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(books),json.dumps(skills),xp,r["cash"]+cash,wallet,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"passed":passed,"score":score,"xp_gained":900 if passed else 150,"cash":cash,
            "player":row_to_player(rr)}

class Up(BaseModel): book_id: str; url: str
@app.post("/api/players/{pid}/reading/upload")
def reading_upload(pid: str, body: Up):
    if body.book_id not in E.BOOK: raise HTTPException(400,"unknown book")
    c=db(); r=c.execute("SELECT uploads FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    ups=json.loads(r[0] or "[]")
    ups.append({"book":E.BOOK[body.book_id][1],"url":body.url[:300],"time":time.time(),"verified":False})
    c.execute("UPDATE players SET uploads=? WHERE id=?",(json.dumps(ups),pid)); c.commit(); c.close()
    return {"ok":True,"note":"Audiobook link recorded for verification. Reading certified via the comprehension test earns even more."}


# --------------------------------------------------------------------- missions + lifelong coach
@app.get("/api/missions")
def missions_meta():
    return {"missions":[E.mission_meta(m) for m in MISSIONS_],
            "verify_policy":"AI helps review; a human/operator confirms consequential verification."}

MISSIONS_=__import__("data.missions", fromlist=["MISSIONS"]).MISSIONS

class MissionSubmit(BaseModel): mission_id: str; evidence: str=""; url: str=""
@app.post("/api/players/{pid}/missions/submit")
def mission_submit(pid: str, body: MissionSubmit):
    if body.mission_id not in E.MISSION: raise HTTPException(400,"unknown mission")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    ms=json.loads(r["missions"] or "[]")
    m=E.MISSION[body.mission_id]
    if any(x.get("mission")==body.mission_id for x in ms):
        c.close(); raise HTTPException(409,"You already submitted this mission. Wait for verification.")
    # participation XP on submit (verify grants the big reward)
    res=E.mission_submit(r, body.mission_id)
    ms.append({"mission":body.mission_id,"title":m[1],"evidence":body.evidence[:500],
               "url":body.url[:300],"verified":False,"time":time.time()})
    xp=r["xp"]+res["submit_xp"]; lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET missions=?,xp=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(ms),xp,lvl,time.time(),pid)); c.commit()
    rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"submit_xp":res["submit_xp"],"note":res["note"],"player":row_to_player(rr)}

class VerifyM(BaseModel): idx: int
@app.post("/api/players/{pid}/missions/verify")
def mission_verify_endpoint(pid: str, body: VerifyM, request: Request):
    require_operator(request)
    """Operator/human verification gate for Real World Missions (the centrepiece)."""
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    ms=json.loads(r["missions"] or "[]")
    if body.idx>=len(ms) or ms[body.idx]["verified"]: raise HTTPException(400,"bad idx / already verified")
    mid=ms[body.idx]["mission"]
    skills=json.loads(r["skills"]); esc=E.mission_verify(skills, mid)
    ms[body.idx]["verified"]=True; ms[body.idx]["verified_time"]=time.time()
    xp=r["xp"]+esc["xp"]; cash=r["cash"]+esc["cash"]; wallet=r["wallet"]+esc["cash"]
    # reputation on passport too
    pp=json.loads(r["passports"] or "{}")
    pp["reputation"]=round((pp.get("reputation",0)+esc["xp"]//100)/2)
    lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET missions=?,skills=?,xp=?,cash=?,wallet=?,passports=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(ms),json.dumps(skills),xp,cash,wallet,json.dumps(pp),lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"verified":ms[body.idx]["title"],"xp_gained":esc["xp"],"cash":esc["cash"],
            "player":row_to_player(rr)}

@app.get("/api/players/{pid}/coach")
def coach(pid: str):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    if not r: raise HTTPException(404,"not found")
    p=row_to_player(r)
    card=E.coach_card(p); focus=E.coach_focus(p)
    return {"card":card,"focus":focus,"llm_on":LLM_ON(),
            "note":"Your lifelong mentor. This memory grows with every deal, book, mission and real meeting."}


# --------------------------------------------------------------------- connected supply-chain economy (Phase A)
import data.econ as EC
@app.get("/api/econ")
def econ_snapshot():
    st=EC.market_snapshot(_GLOBAL_MONTH())
    return st

@app.get("/api/players/{pid}/economy")
def player_economy(pid: str):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    ind = EC.BIZ_TO_INDUSTRY.get(r["business"]) or ("ecom" if r["business"] else None)
    snap=EC.market_snapshot(r["month_global"])
    exposure=None; offers=[]
    if ind:
        exposure={"industry":EC.INDUSTRIES[ind]["name"],
                  "basket":EC.input_basket(ind, r["month_global"]),
                  "pressure":EC.materials_mod(ind, r["month_global"]),
                  "materials_bill_est": round(1200*EC.materials_mod(ind,r["month_global"]),0)}
        offers=EC.supplier_offers(r["business"], r["city"], r["month_global"])
    contracts=json.loads(r["supply_contracts"] or "[]")
    c.close()
    return {"snapshot":snap,"exposure":exposure,"offers":offers,"contracts":contracts}

class Ctr(BaseModel): commodity: str
@app.post("/api/players/{pid}/economy/contract")
def econ_contract(pid: str, body: Ctr):
    if body.commodity=="labor" or body.commodity not in EC.COMMODITIES: raise HTTPException(400,"pick a real commodity")
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    cs=json.loads(r["supply_contracts"] or "[]")
    if any(c.get("commodity")==body.commodity for c in cs): c.close(); raise HTTPException(409,"already have a supply contract for this input")
    price=EC.commodity_price(body.commodity, r["month_global"])
    cs.append({"commodity":body.commodity,"name":EC.COMMODITIES[body.commodity][0],"locked_price":price,"since":time.time()})
    c.execute("UPDATE players SET supply_contracts=?,last_seen=? WHERE id=?",
              (json.dumps(cs),time.time(),pid)); c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"locked":EC.COMMODITIES[body.commodity][0],"price":price,
            "note":"Supply locked at today's price. Your input bill runs ~7% cheaper while the contract holds.",
            "player":row_to_player(rr)}

def _GLOBAL_MONTH():
    c=db(); m=c.execute("SELECT COALESCE(MAX(month_global),1) FROM players").fetchone()[0]; c.close()
    return max(1,int(m))


# --------------------------------------------------------------------- player supply market (producers sell to players)
class BuyOffer(BaseModel): offer_id: int; units: int
@app.get("/api/econ/supply")
def supply_market():
    import data.econ as EC
    c=db()
    month=(c.execute("SELECT COALESCE(MAX(month_global),1) FROM players").fetchone()[0] or 1)
    market=[]
    for cid in EC.COMMODITIES:
        price=EC.commodity_price(cid, month)
        offers=[]
        rows=c.execute("SELECT o.id,o.owner,o.units,o.price,p.handle FROM offers o LEFT JOIN players p ON p.id=o.owner WHERE o.commodity=? AND o.units>0 ORDER BY o.price ASC LIMIT 5",(cid,)).fetchall()
        for o in rows:
            is_self=False
            offers.append({"offer_id":o["id"],"owner":o["handle"],"units":o["units"],"price":o["price"]})
        market.append({"commodity":cid,"name":EC.COMMODITIES[cid][0],"market":price,
                       "base_demand":EC.base_demand(cid,month),"offers":offers})
    c.close()
    return {"month":month,"market":market}

@app.post("/api/players/{pid}/supply/buy")
def supply_buy(pid: str, body: BuyOffer):
    import data.econ as EC
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    o=c.execute("SELECT * FROM offers WHERE id=? AND units>0",(body.offer_id,)).fetchone()
    if not o: c.close(); raise HTTPException(404,"that supply offer is gone (sold out)")
    if o["owner"]==pid: c.close(); raise HTTPException(400,"you can't buy your own supply offer")
    if body.units<1: c.close(); raise HTTPException(400,"units must be at least 1")
    units=min(body.units, o["units"])
    cost=round(units*o["price"],2)
    if r["cash"]<cost:
        c.close(); raise HTTPException(400,f"You need ${cost:,.2f} to buy {units} units from {body.offer_id} — you have ${r['cash']:,.2f}.")
    # buyer pays cash; seller's wallet is credited (real P2P value transfer)
    seller=c.execute("SELECT wallet FROM players WHERE id=?",(o["owner"],)).fetchone()
    new_seller_wallet=(seller["wallet"] if seller else 0)+cost
    # buyer secures supply -> input discount (like a contract)
    cs=json.loads(r["supply_contracts"] or "[]")
    if o["commodity"] not in [x.get("commodity") for x in cs]:
        cs.append({"commodity":o["commodity"],"name":EC.COMMODITIES[o["commodity"]][0],
                   "locked_price":o["price"],"from":"player supply","since":time.time()})
    c.execute("UPDATE players SET cash=cash-?, supply_contracts=? WHERE id=?",(cost,json.dumps(cs),pid))
    c.execute("UPDATE players SET wallet=wallet+? WHERE id=?",(cost,o["owner"]))
    c.execute("UPDATE offers SET units=units-? WHERE id=?",(units,o["id"]))
    c.commit()
    rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    c.close()
    return {"ok":True,"units":units,"cost":cost,"commodity":o["commodity"],
            "paid_to":o["owner"],"wallet_after":row_to_player(rr)["wallet"],
            "note":f"Bought {units} units from a real player. Your input is now locked (~7% cheaper).",
            "player":row_to_player(rr)}


@app.get("/api/producers")
def producers_meta():
    import data.econ as EC
    return {"producers":[{"id":k,"name":v["name"],"output":v["output"],
                          "setup_cost":v["setup_cost"],"blurb":v["blurb"]} for k,v in EC.PRODUCERS.items()]}


# --------------------------------------------------------------------- live events + network discovery
from data.events import EVENTS

@app.get("/api/events")
def live_events():
    return {"events":[E.event_meta(e) for e in EVENTS],
            "note":"Live competitions. Outcomes are seeded by your skills — winning is earned, not RNG."}

class EnterEv(BaseModel): event_id: str
@app.post("/api/players/{pid}/events/enter")
def event_enter(pid: str, body: EnterEv):
    c=db(); r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    hist=json.loads(r["events_history"] or "[]")
    if body.event_id in hist: c.close(); raise HTTPException(409,"You've already competed in this event this cycle. Check back next week/month.")
    res=E.enter_event(row_to_player(r), body.event_id, r["month_global"])
    if not res["ok"]: c.close(); raise HTTPException(400, res["error"])
    hist.append(body.event_id)
    skills=json.loads(r["skills"])
    skills[res["skill"]]=skills.get(res["skill"],15)+int(res["rank"]<=2 and 0 or 0)  # podium minor bump
    if res["rank"]<=2: skills[res["skill"]]+=3
    xp=r["xp"]+res["xp"]; cash=r["cash"]+res["cash"]; wallet=r["wallet"]+res["cash"]
    lvl=E.recompute_level(xp,r["deals_done"])
    c.execute("UPDATE players SET events_history=?,skills=?,xp=?,cash=?,wallet=?,level=?,last_seen=? WHERE id=?",
              (json.dumps(hist),json.dumps(skills),xp,cash,wallet,lvl,time.time(),pid))
    c.commit(); rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {**res,"player":row_to_player(rr)}

@app.get("/api/players/{pid}/events/history")
def events_history(pid: str):
    c=db(); r=c.execute("SELECT events_history FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"entered":json.loads(r[0] or "[]") if r else []}

class Profile(BaseModel): interests: list=[]; industry: str=""
@app.post("/api/players/{pid}/profile")
def set_profile(pid: str, body: Profile):
    c=db(); r=c.execute("SELECT passports FROM players WHERE id=?",(pid,)).fetchone()
    if not r: raise HTTPException(404,"not found")
    pp=json.loads(r[0] or "{}")
    if body.interests: pp["interests"]=[str(x)[:40] for x in body.interests][:10]
    if body.industry: pp["industry"]=body.industry[:60]
    # linking a real professional life is worth a little XP once
    core=c_xp=lambda r_: r_  # noop
    c.execute("UPDATE players SET passports=?,last_seen=? WHERE id=?",(json.dumps(pp),time.time(),pid)); c.commit()
    rr=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone(); c.close()
    return {"ok":True,"player":row_to_player(rr)}

@app.get("/api/network/discover")
def discover(q: str="", city: str="", industry: str=""):
    c=db()
    rows=c.execute("SELECT id,handle,city,state,level,xp,passports FROM players").fetchall()
    c.close()
    out=[]
    for rr in rows:
        pp=json.loads(rr["passports"] or "{}")
        if q and not (q.lower() in rr["handle"].lower() or q.lower() in (rr["city"] or "").lower()
                      or q.lower() in (pp.get("industry") or "").lower()
                      or any(q.lower() in (i or "").lower() for i in pp.get("interests") or [])):
            continue
        if city and city.lower() not in (rr["city"] or "").lower(): continue
        if industry and industry.lower() not in (pp.get("industry") or "").lower(): continue
        out.append({"id":rr["id"],"handle":rr["handle"],"city":rr["city"],"state":rr["state"],
                    "level":rr["level"],"xp":rr["xp"],"industry":pp.get("industry",""),
                    "interests":(pp.get("interests") or [])[:4]})
    return {"results":out[:40]}


@app.post("/api/auth/login")
def auth_login(body: AuthBody):
    tok = login_account(body.username, body.password)
    c=db(); row=c.execute("SELECT p.* FROM players p JOIN accounts a ON a.id=p.account_id WHERE a.username=lower(?)",(body.username,)).fetchone()
    out={"token":tok,"player": row_to_player(row) if row else None}; c.close(); return out

@app.get("/api/auth/me")
def auth_me(request: Request):
    az=request.headers.get("authorization",""); token=az[7:] if az.lower().startswith("bearer ") else None
    acc=account_for_token(token)
    if not acc: raise HTTPException(401,"Not logged in")
    c=db(); row=c.execute("SELECT * FROM players WHERE account_id=?",(acc,)).fetchone(); c.close()
    if not row: return {"player":None}
    return {"player":row_to_player(row)}

@app.post("/api/auth/logout")
def auth_logout(request: Request):
    az=request.headers.get("authorization",""); token=az[7:] if az.lower().startswith("bearer ") else None
    if token:
        c=db(); c.execute("DELETE FROM sessions WHERE token=?",(token,)); c.commit(); c.close()
    return {"ok":True}


init_db()







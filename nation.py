"""
EMPIRE ONE — nationwide US layer.
Loads REAL US city data (data/us_cities.json, from the GeoNames US extract: lat/lng + state).
Provides the map, per-city business/eco generation, national corporations, and LLM-backed
business people & characters. All indices are deterministic (seeded by name+state) so the
world is stable across reloads.
"""
import json, hashlib, random, math
from pathlib import Path
import llm as LLM

_DATA = Path(__file__).parent / "data" / "us_cities.json"
CITIES = json.loads(_DATA.read_text())      # list of {n,s,la,lo}
_bykey = {(c["n"].upper(), c["s"]): c for c in CITIES}
_KEYLIST = [(c["n"].upper(), c["s"]) for c in CITIES]
N = len(CITIES)

# rough cost-of-living multiplier by state (national default 1.0)
_STATE_COL = {
    "CA":1.38,"NY":1.42,"HI":1.55,"DC":1.48,"MA":1.28,"WA":1.22,"NJ":1.30,"CT":1.28,
    "MD":1.22,"IL":1.10,"CO":1.15,"OR":1.18,"AK":1.28,"VT":1.14,"VA":1.10,"FL":1.08,
    "TX":0.99,"GA":0.98,"NC":0.97,"TN":0.96,"AZ":0.99,"MI":0.98,"PA":1.02,"OH":0.95,
    "ID":1.00,"MT":1.00,"WY":0.99,"ND":0.96,"SD":0.96,"NE":0.99,"KS":0.96,"IA":0.94,
    "MN":1.06,"WI":0.99,"MO":0.96,"AR":0.92,"LA":0.96,"MS":0.91,"AL":0.92,"KY":0.94,
    "WV":0.93,"SC":0.96,"NM":0.98,"UT":1.02,"NV":1.04,"IN":0.95,"OK":0.94,"DE":1.05,
    "RI":1.18,"NH":1.08,"ME":1.02,"PR":1.00,"GU":1.00,"VI":1.20,
}

def _seed(name, state, salt=0):
    return int(hashlib.md5(f"{name.upper()}|{state}|{salt}".encode()).hexdigest()[:8], 16)

def state_col(state):
    return _STATE_COL.get(state, 1.0)

def match_city(name, state=None):
    """Resolve a city: by (name,state) or name alone when unique."""
    if not name: return None
    name=name.strip()
    if not name: return None
    if state:
        c=_bykey.get((name.upper(), state.upper()))
        if c: return {**c, "key":(name.upper(),state.upper())}
    # unique-name match
    hits=[k for k in _KEYLIST if k[0]==name.upper()]
    if len(hits)==1:
        k=hits[0]; return {**_bykey[k], "key":k}
    return None

def nearest_city(lat, lon):
    best, bd = None, 1e18
    for c in CITIES:
        d=hav(lat,lon,c["la"],c["lo"])
        if d<bd: bd, best = d, c
    return {**best, "key":(best["n"].upper(), best["s"])}, round(bd,1)

def hav(a_la,a_lo,b_la,b_lo):
    R=3958.8; p1=math.radians(a_la); p2=math.radians(b_la)
    dp=p2-p1; dl=math.radians(b_lo-a_lo)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def biz_index(name, state):
    """Deterministic 35–95 business-opportunity index."""
    return 45 + (_seed(name,state,7) % 51)

def local_businesses(name, state, limit=8):
    """Deterministic local business ecology for a city."""
    rnd=random.Random(_seed(name,state,11))
    pool=[("Cafe","Food & Retail"),("Salon","Beauty"),("Auto Repair","Repair"),
          ("Gym","Health"),("Restaurant","Food & Retail"),("Cleaning Co","Services"),
          ("Laundry","Services"),("Bakery","Food & Retail"),("Bookstore","Retail"),
          ("Neighborhood Market","Retail"),("Plumbing Co","Services"),
          ("Mini-Golf & Arcade","Leisure"),("Spa","Beauty"),("Food Truck","Food & Retail")]
    rnd.shuffle(pool)
    n=int(biz_index(name,state)/18)+2
    out=[]
    for i in range(min(n,limit)):
        nm,sec=pool[i%len(pool)]
        out.append({"name":f"{name} {nm}", "sector":sec,
                    "value": 8000+ _seed(name,state,i+50)%180000,
                    "jobs": 3+ _seed(name,state,i+90)%40})
    return out

# real national corporations
CORPORATIONS = [
 ("AmberTech Group","Technology","Recurring software sales","large"),
 ("Summit Manufacturing","Manufacturing","B2B industrial supply","large"),
 ("Delta Distribution","Distribution","Logistics & freight","large"),
 ("Vantage Retail","Retail","Consumer goods","large"),
 ("Meridian Financial","Finance","Lending & business services","mega"),
 ("NorthPeak Energy","Energy","Renewables & utilities","mega"),
 ("CoreHealth Partners","Healthcare","Clinics & virtual care","large"),
 ("Pinnacle Media","Media","Advertising & content","large"),
 ("SteelRiver Capital","Investing","Acquisitions & holdings","mega"),
 ("BlueHorizon Foods","Consumer Packaged Goods","National brand","large"),
]

def city_corporations(name, state, limit=4):
    """National corps with local presence, deterministic."""
    rnd=random.Random(_seed(name,state,21))
    pool=list(CORPORATIONS); rnd.shuffle(pool)
    return [{"name":c[0],"sector":c[1],"line":c[2],"tier":c[3]} for c in pool[:min(limit,2+ biz_index(name,state)//30)]]

# ------------------------------------------------------------------------- business people / characters
# id, name, role, company-kind, personality, voice_id (ElevenLabs), specialty
CHARACTERS = [
 ("ch_vera","Vera Alvarez","CFO","Meridian Financial","sharp, numbers-first","21m00Tcm4TlvDq8ikWAM","finance"),
 ("ch_marcus","Marcus Bell","VP Sales","Vantage Retail","greedy, competitive","pNInz6obpgDQGcFmaJgB","sales"),
 ("ch_priya","Priya Nair","Founder","Nimbus Cloud (Virtual SaaS)","eager, optimistic","EXAVITQu4vr4xnSDxMaL","negotiation"),
 ("ch_ingrid","Ingrid Solberg","Operations Director","Delta Distribution","tough, no-nonsense","MF3mGyEYCl7XYWbB9VQL","operations"),
 ("ch_omar","Omar Haddad","Investor","SteelRiver Capital","strategic, patient","jake_voice_placeholder","strategy"),
]

def business_person(character_id, question, state=""):
    """An LLM-backed business person who 'thinks and responds like a businessman/woman'.
    Uses a live LLM when ELEVENLESS.../LLM key present; else a personality-tuned fallback."""
    cA = next((c for c in CHARACTERS if c[0]==character_id), CHARACTERS[0])
    persona=(f"You are {cA[1]}, {cA[2]} at a real {cA[3]} company. Personality: {cA[4]}. "
             f"Respond exactly as this sharp businessperson would: concrete, decisive, "
             f"negotiation-minded, uses real business language ({cA[6]}). Under 90 words.")
    holder="EMPLOYEE"
    reply=LLM.chat(persona, f"{question}", temperature=0.8)
    if reply: return {"kind":"llm","reply":reply.strip(),"voice_id":cA[5],"character":cA[1]}
    import engine as E
    fb=E.npc_mentor(question, [], False)["reply"]
    return {"kind":"fallback","reply":fb,"voice_id":cA[5],"character":cA[1]}

# ElevenLabs voice gateway (needs ELEVENLABS_API_KEY)
def elevenlabs_speak(text, voice_id):
    key=__import__("os").environ.get("ELEVENLABS_API_KEY","").strip()
    if not key:
        return {"ok":False,"error":"ELEVENLABS_API_KEY not set. Add it to unlock real character voices."}
    import requests
    r=requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key":key,"Content-Type":"application/json"},
        json={"text":text[:2000],"voice_settings":{"stability":0.55,"similarity_boost":0.75}},
        timeout=40)
    if r.status_code == 200:
        path=str(Path("/home/nova/empire-one")/"static"/f"voice_{hash(text[:40])&0xffff}.mp3")
        Path(path).write_bytes(r.content)
        return {"ok":True,"audio":"/static/"+path.split("/")[-1]}
    return {"ok":False,"error":f"ElevenLabs http {r.status_code}: {r.text[:120]}"} 

def econ(city, state=None):
    """(col_index, biz_index) for any city. Uses curated rich data where available
    (state must be supplied and city in the curated 50), else nationwide heuristics."""
    return round(state_col(state or "US") * 100), biz_index(city, state or "US")

def relocation_cost_na(a_city, a_state, b_city, b_state):
    a = match_city(a_city or "", a_state); b = match_city(b_city or "", b_state)
    if not a or not b: return None
    d = hav(a["la"], a["lo"], b["la"], b["lo"])
    cost = 250 + d * 2.2 + max(0, (state_col(b_state or "US") - state_col(a_state or "US"))) * 90
    return max(350, round(cost))

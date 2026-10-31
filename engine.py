"""
EMPIRE ONE — game engine.
Pure functions: geography/relocation, business economics, AI negotiation, AI coach.
No I/O so it is unit-testable and deterministic (pass seed for repeatable rolls).
"""
import hashlib
import math, random, time
from data.datasets import CITIES, BUSINESSES, LEVELS, DEFAULT_START

CITY = {c[0]: c for c in CITIES}          # name -> tuple
BIZ  = {b[0]: b for b in BUSINESSES}      # id   -> tuple


# ----------------------------------------------------------------------------- geolocation / relocation
def haversine_miles(a_lat, a_lon, b_lat, b_lon):
    R = 3958.8
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = p2 - p1
    dl = math.radians(b_lon - a_lon)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def relocation_cost(src, dst, multi_business=1):
    """The 'from your $5,000 you can move' mechanic. Moving costs real cash derived
    from distance + cost-of-living delta. Local moves cheap, cross-country expensive."""
    a, b = CITY[src], CITY[dst]
    dist = haversine_miles(a[2], a[3], b[2], b[3])
    col_delta = max(0, b[4] - a[4])
    setup = 250.0
    cost = setup + dist * 2.2 + col_delta * 90.0
    return max(350.0, round(cost * multi_business))

def nearest_city(lat, lon):
    best, bestd = None, 1e18
    for c in CITIES:
        d = haversine_miles(lat, lon, c[2], c[3])
        if d < bestd:
            bestd, best = d, c
    return best, round(bestd, 1)

def city_business_index(name):
    return CITY[name][5]   # BIZ 0-100


# ----------------------------------------------------------------------------- business economics
def monthly_sim(biz_id, city, month_global, seed=None, cash=0.0, col_ix=None, biz_ix=None, materials_mod=1.0):
    """Simulate one operating month for a business in a city.
    col_ix/biz_ix override city lookup for nationwide (non-curated) cities."""
    rnd = random.Random(seed)
    b = BIZ[biz_id]      # id, name, category, start_cost, margin, demand, blurb
    if col_ix is None or biz_ix is None:
        import nation as NA
        col_ix, biz_ix = NA.econ(city, "US")
    col = col_ix / 100.0
    bizidx = biz_ix / 100.0
    growth = b[5] / 5.0                       # demand driver normalized 0-1
    margin = b[4]

    # economic cycle: slow sine 0.8..1.2 (12-month cycle) + noise
    cycle = 0.8 + 0.4 * ((math.sin(month_global / 6.0) + 1) / 2.0)
    noise = 1.0 + rnd.uniform(-0.10, 0.10)

    base_rev = 1700.0 * bizidx * (0.6 + growth) * cycle * noise
    # rent scales with the size of the business (a lawn-care crew rents less than a food truck commissary)
    rent = (60 + 0.11 * b[3]) * (0.6 + 0.4 * col)
    import data.econ as EC
    materials = base_rev * (1 - margin) * materials_mod
    input_pressure = 1.0 if materials_mod<=1.0 else materials_mod
    labor = base_rev * 0.22 * (0.6 + col * 0.4)
    expenses = rent + materials + labor
    net = base_rev - expenses

    level = "boom" if cycle > 1.05 else ("slump" if cycle < 0.9 else "normal")
    return {
        "revenue": round(base_rev, 2),
        "rent": round(rent, 2),
        "materials": round(materials, 2),
        "input_pressure": round(input_pressure, 2),
        "labor": round(labor, 2),
        "expenses": round(expenses, 2),
        "net": round(net, 2),
        "cycle": round(cycle, 2),
        "cycle_label": level,
        "burn_warning": cash + net < 0,
    }


# ----------------------------------------------------------------------------- AI negotiation engine
DEALS = {
    "supplier": {
        "title": "Acquire 'Redline Manufacturing'",
        "context": "A regional manufacturer is for sale. The owner quotes $2,000,000.",
        "hid": {"rev": 2_400_000, "ebitda": 480_000, "concentration": 0.43, "contract_lock": 0.55},
        "true_value": 4_800_000,  # 10x EBITDA
    },
    "lease": {
        "title": "Negotiate a Downtown Storefront Lease",
        "context": "The landlord wants $4,200/month for a prime retail unit. 5-year term.",
        "hid": {"rev": 0, "ebitda": None, "concentration": 0.0, "contract_lock": 0.0,
                "market_rent": 3_400, "vacancy": 0.62},
        "true_value": 3_400,
    },
}

# questions the player can ask during due diligence; each reveals info + earns/loses diligence score
QUESTIONS = {
    "revenue":     ("Ask about annual revenue.", lambda d: d["rev"]),
    "ebitda":      ("Ask about EBITDA / true cash earnings.", lambda d: d["ebitda"]),
    "why_selling": ("Ask why they are selling.", None),
    "concentration":("Investigate customer concentration.", lambda d: d["concentration"]),
    "contracts":   ("Ask about customer contract renewals.", lambda d: d["contract_lock"]),
    "market_rent": ("Ask about comparable market rents.", lambda d: d.get("market_rent")),
    "vacancy":     ("Ask about local vacancy rates.", lambda d: d.get("vacancy")),
}

PERSONALITIES = {
    "greedy":   {"anch": 0.95, "tol": 0.55, "emotion": 0.6},
    "eager":    {"anch": 0.80, "tol": 0.35, "emotion": 0.3},
    "tough":    {"anch": 1.05, "tol": 0.75, "emotion": 0.2},
    "straight": {"anch": 0.90, "tol": 0.45, "emotion": 0.1},
}

def _personality_for(deal, seed):
    return PERSONALITIES[random.Random(seed).choice(list(PERSONALITIES))]

def negotiate(deal_id, seed):
    """Start a negotiation. Returns session state (no side effects)."""
    deal = DEALS[deal_id]
    personality = _personality_for(deal_id, seed + 1)
    price = deal["true_value"]
    anchor = round(price * personality["anch"])
    return {
        "deal_id": deal_id, "title": deal["title"], "context": deal["context"],
        "price": price, "true_value": price, "anchor": anchor,
        "personality": list(PERSONALITIES.keys())[list(PERSONALITIES.values()).index(personality)],
        "tol": personality["tol"], "emotion": personality["emotion"],
        "asked": [], "offers": [], "status": "playing", "log": [{"who": "opp", "msg": deal["context"], "type": "info"}],
        "opp_ask": ["revenue", "ebitda", "why_selling", "concentration", "contracts", "market_rent", "vacancy"],
    }

def ask(neg, qid):
    if qid not in neg["opp_ask"] or qid in neg["asked"]:
        return neg, {"msg": "Already asked."}
    deal = DEALS[neg["deal_id"]]
    hid = deal["hid"]
    neg["asked"].append(qid)
    label = QUESTIONS[qid][0]
    if qid == "why_selling":
        msg = ("\"Honestly? My health and I'm burned out. The business is solid — "
               + ("but one customer is a lot of my revenue and contracts roll over soon.\""
                  if hid.get("concentration", 0) > 0.3 else
                  "\"It's profitable. I just want to cash out and retire.\""))
    else:
        fn = QUESTIONS[qid][1]
        val = fn(hid) if fn else None
        money = f"${val:,}" if isinstance(val, (int, float)) and val and val > 100 else (
                f"{val*100:.0f}%" if isinstance(val, float) else "")
        if qid == "revenue":
            msg = f"We do about ${val:,} in annual revenue."
        elif qid == "ebitda":
            if val is None: msg = "We run lean — call it about $480k in real cash earnings."
            else: msg = f"Real cash earnings (EBITDA) ≈ ${val:,}."
        elif qid == "concentration":
            msg = f"Look, I'll be straight — one client is about {val*100:.0f}% of revenue."
        elif qid == "contracts":
            msg = f"Most contracts renew within {str(val*100)[:2]} months. Nothing is locked long-term."
        elif qid == "market_rent":
            msg = f"Comps downtown run around ${val:,}/month."
        elif qid == "vacancy":
            msg = f"Current vacancy rate in the strip is about {val*100:.0f}%."
        else:
            msg = money or "I'd rather not say."
    neg["log"].append({"who": "opp", "msg": msg, "type": "info"})
    return neg, {"msg": label, "reply": msg}

def offer(neg, amount):
    """Player makes an offer. Evaluates vs hidden valuation + personality.
    Returns updated state + one round of dialogue."""
    deal = DEALS[neg["deal_id"]]
    true = deal["true_value"]
    neg["offers"].append(amount)
    p = neg["personality"]
    tolerance = neg["tol"]
    emotion = neg["emotion"]

    # compute a "counter" path toward his floor = true*(1-some concession)
    floor = true * 0.9
    above = amount >= floor
    blew = amount > true * 1.15

    if blew:
        neg["status"] = "accepted"
        msg = ("The owner jumps at your offer. \"Deal. Sign here.\" "
               "— You paid far above value; the seller is thrilled.")
        kind = "accept_overpay"
    elif above and abs(amount - true) / true < 0.12:
        neg["status"] = "accepted"
        msg = ("\"Done.\" The owner nods and shakes your hand. "
               "Right about fair value — a clean deal.")
        kind = "accept_fair"
    elif above and abs(amount - true) / true >= 0.12:
        # paid above fair, accepted but should have bargained
        neg["status"] = "accepted"
        msg = ("\"Fine, done.\" You paid, but not as hard as you could have. "
               "There was room to push."
               if emotion < 0.4 else
               "\"Look, I can't take less than that, but... done. Deal.\"")
        kind = "accept_soft"
    elif amount >= true * 0.82:
        # counter offer
        counter = round(true + (true - amount) * 0.35)
        neg["anchor"] = counter
        neg["log"].append({"who": "opp", "msg": f"\"{counter/1000:.0f}k. That's my line. Take it or leave it.\"", "type": "counter"})
        return neg, {"reply": "The owner counters.", "counter": counter, "type": "counter"}
    elif amount >= true * 0.7:
        counter = round(true + (true - amount) * 0.55)
        neg["anchor"] = counter
        neg["log"].append({"who": "opp", "msg": f"\"Come on. I need {counter/1000:.0f}k at least.\"", "type": "counter"})
        return neg, {"reply": "The owner counters.", "counter": counter, "type": "counter"}
    else:
        if emotion > 0.5:
            neg["status"] = "walked"
            msg = ("\"That's insulting. I'm done here.\" The owner stands up and walks out. "
                   "You lowballed too aggressively.")
        else:
            neg["status"] = "playing"
            neg["log"].append({"who": "opp", "msg": "\"Too low. I can't even consider that.\"", "type": "info"})
            return neg, {"reply": "\"Too low.\" Try higher.", "type": "info"}
        return neg, {"reply": msg, "type": "walkaway", "status": neg["status"]}

    neg["status"] = "accepted"
    return neg, {"reply": msg, "type": "result", "status": "accepted", "price": amount,
                 "true_value": true}


# ----------------------------------------------------------------------------- AI coach review
def coach_review(neg):
    """Score the finished negotiation and coach the player (the killer feature)."""
    deal = DEALS[neg["deal_id"]]
    true = deal["true_value"]
    asked = neg["asked"]
    offers = neg["offers"]

    # diligence score: how many material questions asked
    material = ["revenue", "ebitda", "concentration", "contracts", "market_rent"]
    caught = [q for q in asked if q in material]
    diligence = round(35 + 13 * len(caught), 0)
    diligence = min(100, diligence)

    # negotiation score: based on final price vs true value
    # use accepted counter if present, else the player's last offer
    final = neg.get("final_price") or (offers[-1] if offers else None)
    if not final:
        neg_score, comm = 0, "You never made an offer."
    elif neg["status"] == "walked":
        neg_score = 20
        comm = "You walked away by lowballing — nothing was agreed."
    else:
        ratio = final / true
        if ratio <= 0.90:
            neg_score = round(88 + (0.90 - ratio) * 30)
            comm = f"You bought at {ratio*100:.0f}% of fair value. Strong."
        elif ratio <= 1.0:
            neg_score = round(80 - (ratio - 0.90) * 50)
            comm = f"You closed at about fair value ({ratio*100:.0f}%). Solid but there was a little room."
        else:
            neg_score = round(70 - (ratio - 1.0) * 90)
            comm = f"You overpaid — {ratio*100:.0f}% of fair value. That erodes your return."

    insights = []
    # hidden-risk teaching — catch concentration
    if deal_id := neg["deal_id"]:
        h = deal["hid"]
        if "concentration" not in asked and h.get("concentration", 0) > 0.3:
            insights.append(
                "You never investigated customer concentration. One client is "
                f"{h['concentration']*100:.0f}% of revenue — that is the single biggest "
                "risk in this deal. Always ask who your repeatable revenue depends on.")
        elif "concentration" in asked:
            insights.append("Good — you caught the customer-concentration flag and factored it in.")
        if "contracts" not in asked and h.get("contract_lock", 0) > 0.3:
            insights.append("You didn't ask about contract renewals. Revenue that isn't locked "
                            "down can vanish in months, which should have lowered your offer.")
        if "revenue" not in asked:
            insights.append("You never verified annual revenue. Valuation without verified "
                            "top-line is guesswork.")
        if "ebitda" not in asked:
            insights.append("You never confirmed EBITDA. You were trading on reported numbers.")

    score = round(0.5 * neg_score + 0.5 * diligence)
    return {
        "score": max(0, min(100, score)),
        "negotiation": max(0, min(100, neg_score)),
        "diligence": max(0, min(100, diligence)),
        "communication": 75,
        "summary": comm,
        "insights": insights,
    }


# ----------------------------------------------------------------------------- skill / level / passport
LEVEL_DEFS = {l[0]: {"title": l[1], "blurb": l[2]} for l in LEVELS}

def level_for(net_worth, deals_done):
    _l = 1
    if deals_done >= 6 and net_worth >= 5_000_000: _l = 4
    elif deals_done >= 3 and net_worth >= 1_000_000: _l = 3
    elif deals_done >= 1: _l = 2
    return max(1, _l) if net_worth > 0 else 1

# ----------------------------------------------------------------------------- learning / growth (XP, skills, money)
from data.learning import BOOKS, CLASSES, LEVEL_STEPS, AUDIBLE_SEARCH
BOOK = {b[0]: b for b in BOOKS}
CLASS = {c[0]: c for c in CLASSES}

ALL_SKILLS = ["negotiation", "sales", "finance", "communication",
              "leadership", "strategy", "operations", "mindset"]

def seed_skills():
    return {s: 15 for s in ALL_SKILLS}

def add_skill(skills, deltas):
    skills = skills or {}
    for k, v in (deltas or {}).items():
        skills[k] = int(skills.get(k, 15)) + v
    return skills

def recompute_level(xp, deals):
    """Dual-gate: you must have BOTH the XP and the deal-count to climb."""
    if deals >= 6 and xp >= 24000: return 4
    if deals >= 3 and xp >= 7000:  return 3
    if deals >= 1 and xp >= 1000:  return 2
    return 1

def book_progress(book_id, minutes, prior_minutes, skills):
    """Listening minutes -> XP. Completing a book (>= its hours) -> skill + cash (once)."""
    b = BOOK[book_id]
    total_minutes = (prior_minutes or 0) + minutes
    hours_needed = b[4] * 60
    newly_completed = (prior_minutes or 0) < hours_needed and total_minutes >= hours_needed
    xp = int(minutes)                     # XP from active learning
    cash = b[6] if newly_completed else 0 # one-time completion bonus (anti-exploit)
    skills = add_skill(skills, b[5]) if newly_completed else skills
    return {"xp": xp, "cash": cash, "completed": newly_completed,
            "minutes": total_minutes, "hours_needed": hours_needed,
            "book": b[1], "skills_granted": b[5] if newly_completed else {}}

def class_complete(book_id, score, skills):
    c = CLASS[book_id]
    # score 0-100; partial credit for effort, full skill/cash on passing grade
    passed = score >= 60
    q = score / 100.0
    minutes = c[3]
    xp = int(minutes * (0.5 + 0.5 * q))
    cash = c[5] if passed else 0
    skills = add_skill(skills, {k: int(v * q) for k, v in c[4].items()})
    return {"xp": xp, "cash": cash, "passed": passed, "class": c[1],
            "cert": c[1] if passed else None}

def xp_title(xp):
    prev = 0
    for thresh, title in LEVEL_STEPS:
        if xp < thresh: break
        prev = thresh
    # title is the last reached tier
    title = "Rookie"
    for thresh, t in LEVEL_STEPS:
        if xp >= thresh: title = t
    return title


# ----------------------------------------------------------------------------- living world (contracts / market / coaches / meetings / NPC mentor)
from data.market import NPC_COMPANIES, CONTRACTS, COACHES, LISTINGS, SERVICE_LABEL
COMPANY = {c[0]: c for c in NPC_COMPANIES}
CONTRACT = {c[0]: c for c in CONTRACTS}
COACH = {c[0]: c for c in COACHES}
LISTING = {b[0]: b for b in LISTINGS}

def _skill(sk, name, base=15):
    return int(sk.get(name, base))

def contract_take(contract_id):
    c = CONTRACT[contract_id]
    return {"id": c[0], "company": c[1], "title": c[2], "service": c[3],
            "service_label": SERVICE_LABEL.get(c[3], c[3]), "skills_used": c[4],
            "budget": c[5], "difficulty": c[6], "days": c[7]}

def contract_complete(contract_id, skills, rel):
    """Execute a freelance contract against an NPC company. Outcome rides your skill.
    Success -> full pay + XP + relationship. Success depends on skill vs difficulty."""
    c = CONTRACT[contract_id]
    skill_used = c[3]
    skill_level = _skill(skills, skill_used)
    diff = c[6]                       # 1..5
    # base 45% + up to 45% from the relevant skill (skill 15..~80)
    p = 0.45 + max(0.0, (skill_level - 10)) / 100.0 - (diff - 1) * 0.04
    p = min(0.96, max(0.15, p))
    success = random.random() < p
    pay = round(c[5] * (1.0 if success else 0.25))
    xp = 400 if success else 80
    rel_gain = 3 if success else 1
    new_rel = (rel or 0) + rel_gain
    note = (f"You delivered the contract. {COMPANY[c[1]][1]} is impressed (+{rel_gain} trust)."
            if success else
            f"Delivery came up short — you billed the cost price. Build your {SERVICE_LABEL[skill_used]} skill.")
    return {"success": success, "pay": pay, "xp": xp, "rel_gain": rel_gain,
            "rel_after": new_rel, "note": note, "company": c[1],
            "company_name": COMPANY[c[1]][1], "title": c[2]}

def buy_listing_ok(p, listing_id, wallet, net_worth):
    b = LISTING[listing_id]
    price = b[3]
    if wallet < price:
        return {"ok": False, "error": f"Need ${price:,} in your earned wallet — you have ${wallet:,.0f}. Earn more by selling services, learning and building real things."}
    return {"ok": True, "price": price, "name": b[1], "sector": b[2],
            "revenue": b[4], "kind": b[7]}

def listing_dividend(listing_id, global_month):
    b = LISTING[listing_id]
    monthly = b[4] * b[5] / 12.0 * 0.5     # revenue * margin / 12, half flows to you
    return max(0, round(monthly))

def coach_book(coach_id):
    c = COACH[coach_id]
    return {"id": c[0], "name": c[1], "title": c[2], "specialty": c[3],
            "rate": c[4], "bio": c[5]}

# NPC mentor: real LLM when configured, else deterministic coach fallback
import llm as LLM
MENTOR_SYSTEM = ("You are the AI business mentor inside EMPIRE ONE, a business RPG where "
    "players build real skills and businesses. Be direct, practical and motivating. "
    "Give actionable advice on sales, negotiation, leadership, investing, and the "
    "player's actual current situation. Keep answers under 120 words and end with one "
    "concrete next action.")

def npc_mentor(question, memory, llm_on):
    if llm_on:
        ctx = ("Recent real connections/context: " + (", ".join(memory[-6:]) if memory else "none yet") + ".")
        ans = LLM.chat(MENTOR_SYSTEM, ctx + "\nPlayer asks: " + question)
        if ans:
            return {"kind": "llm", "reply": ans.strip(), "notes": "Answered by live LLM mentor (EMP)."}
    # deterministic fallback — honest, no fake LLM
    fallbacks = {
        "sales": ("Close on the next interaction. Use the AIDA structure: hook attention, "
                  "build desire, then one clean ask. Ask one more question before you pitch — "
                  "curiosity outsells cleverness."),
        "negotiation": ("Before you counter, answer three things the other side wants. Then "
                        "anchor first and let them move toward you. Never accept silence discomfort."),
        "leadership": ("Hire for judgment, not just skill. Write down the ONE decision only you "
                       "should make, and push everything else down."),
        "invest": ("Don't buy what you haven't modeled. If the numbers are 'easy', the risk is "
                   "hidden. Ask about customer concentration before you ever value an asset."),
        "finance": ("Know your burn. Runway = cash / monthly burn. If it's under 6 months, cut "
                    "cost before you hunt for revenue."),
        "default": ("Run the numbers, then talk to a customer today. Action beats analysis — "
                    "every real connection you make earns you XP and opens a door."),
    }
    q = question.lower()
    key = "default"
    for k in ("sales","negotiation","leadership","invest","finance"):
        if k in q: key = k
    return {"kind": "fallback", "reply": fallbacks[key],
            "notes": "LLM not configured — use the deterministic coach. Set OPENROUTER_API_KEY for the live mentor."}


# ----------------------------------------------------------------------------- Real World Missions + lifelong coach memory
from data.missions import MISSIONS, MISSION

def mission_meta(m):
    return {"id":m[0],"title":m[1],"task":m[2],"skill":m[3],"submit_xp":m[4],
            "verified_xp":m[5],"verified_cash":m[6],"skill_deltas":m[7]}

def mission_submit(p, mission_id):
    m=MISSION[mission_id]
    return {"submit_xp":m[4],"note":"Real-world mission submitted. A sponsor/operator verifies the evidence before the big payout."}

def mission_verify(skills, mission_id):
    m=MISSION[mission_id]
    skills=add_skill(skills, m[7])
    return {"xp":m[5],"cash":m[6],"skills":m[7]}

def coach_card(p):
    """Lifelong mentor memory: builds a personal snapshot of the player from their whole
    journey so the coach greets them and targets their real weaknesses. Deterministic;
    a live LLM uses this as context when a key is set."""
    sk=p.get("skills") or {}
    ranked=sorted(sk.items(), key=lambda kv: -kv[1]) if sk else []
    strengths=[k for k,v in ranked[:2]] or ["getting started"]
    growth=[k for k,v in ranked[-2:]] if ranked else ["sales","finance"]
    deals=p.get("deals_done",0); xp=p.get("xp",0)
    books_done=[v for v in (p.get("books") or {}).values() if (v or {}).get("minutes",0)>0]
    parts=["You started in %s." % p.get("city","your city")]
    if books_done: parts.append("You've studied %d book(s)."%len(books_done))
    if deals: parts.append("You've closed %d deal(s)."%deals)
    if p.get("npc_memory"): parts.append("Recent: "+p["npc_memory"][-1][:80])
    # weakest skill as next focus
    weak = min(sk, key=sk.get) if sk else "finance"
    narrative=(f"{p.get('handle','Founder')}, you've become solid at {strengths[0]}. "
               f"Your next lever is {weak} — that's where the upside hides.")
    return {"names":strengths,"strengths":strengths,"growth_areas":growth,
            "weakest":weak,"narrative":narrative,"context":". ".join(parts)}

def coach_focus(p):
    """Targeted deterministic advice on the player's weakest skill."""
    card=coach_card(p); w=card["weakest"]
    fb={"sales":"Close on the next call: one clean ask after you've asked a question they care about.",
        "negotiation":"Before you move, write down what the other side actually wants. Anchor first.",
        "finance":"Recompute your runway tonight: cash divided by monthly burn. Under 6 months = act.",
        "leadership":"Write the one decision only you should make. Everything else gets delegated.",
        "communication":"Lead with the result, then the context. Leaders make it easy to decide.",
        "strategy":"Name the single customer segment that pays you best and double down there.",
        "operations":"Cut one cost this week and measure it. Operations is made of small wins.",
        "mindset":"Book 30 minutes daily for deep work before you open the phone."}.get(w,
        "Run the numbers, then talk to a customer today.")
    return {"weakest":w,"advice":fb}


# ----------------------------------------------------------------------------- live events
from data.events import EVENTS, EVENT

def event_meta(e):
    return {"id":e,"type":EVENT[e]["type"],"title":EVENT[e]["title"],"blurb":EVENT[e]["blurb"],
            "cadence":EVENT[e]["cadence"],"skill":EVENT[e]["skill"],"base_xp":EVENT[e]["base_xp"],
            "base_cash":EVENT[e]["base_cash"],"min_level":EVENT[e]["min_level"]}

def enter_event(p, eid, month):
    """Deterministic event outcome seeded by (player, event, month). Reward scales with the
    player's RELEVANT skill — high skill = better placements, never arbitrary RNG outcomes."""
    if eid not in EVENT: return {"ok":False,"error":"unknown event"}
    if not p.get("business"): return {"ok":False,"error":"start a business before competing"}
    e=EVENT[eid]
    if p.get("level",1) < e["min_level"]:
        return {"ok":False,"error":f"Needs Level {e['min_level']} (you're L{p.get('level',1)}). Earn XP + deals."}
    skill=e["skill"]; lvl=p.get("skills",{}).get(skill,15)
    # seeded luck 0..15 (stable per player+event+month so it's fair & repeatable)
    _s=int(hashlib.md5(f"{p.get('id','')}|{eid}|{month}".encode()).hexdigest()[:8],16)
    luck=(_s%1600)/100.0
    score=20+min(70,lvl*0.95)+luck            # 20..~105
    score=min(100,score)
    if score>=85: rank,placed=1,"🏆 Podium (top 3)"
    elif score>=62: rank,placed=2,"Top half finish"
    else: rank,placed=3,"Competitive showing"
    scale=0.5+score/100.0
    xp=int(e["base_xp"]*scale); cash=int(e["base_cash"]*scale)
    note=(f"You drew on your {skill} rating ({lvl}) to place well. {placed}.")
    return {"ok":True,"event":e["title"],"skill":skill,"skill_level":lvl,"score":round(score,0),
            "rank":rank,"placed":placed,"xp":xp,"cash":cash,"note":note}

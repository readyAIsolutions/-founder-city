"""
FOUNDER CITY — connected supply-chain economy (Phase A #1).
Commodities with deterministic price cycles, industry production-chains (inputs -> outputs),
and dependency relationships. AI provides opportunities/characters; the RULES ENGINE sets all
prices and costs (never AI-invented). Prices are seeded deterministic per commodity + month.
"""
import hashlib, math

# commodity: id -> (name, base_price_per_unit, volatility, cycle_months)
COMMODITIES = {
    "fuel":          ("Fuel",           4.20, 0.38, 9),
    "grain":         ("Grain",          1.10, 0.22, 14),
    "lumber":        ("Lumber",         3.80, 0.26, 16),
    "steel":         ("Steel",          5.50, 0.30, 11),
    "cotton":        ("Cotton",         2.40, 0.20, 13),
    "tech_comp":     ("Tech Components",12.00, 0.34, 6),
    "food_inputs":   ("Food Ingredients",1.80, 0.18, 12),
    "packaging":     ("Packaging",      0.90, 0.14, 10),
    "energy":        ("Energy",         0.14, 0.40, 7),
    "goods":         ("Finished Goods", 8.00, 0.16, 15),
}

# industry: id -> {name, kind: produce|consume, inputs: {commodity: qty}, output: commodity or None}
INDUSTRIES = {
    "farm":        {"name":"Farm","kind":"produce","inputs":{"fuel":2,"labor":1},"output":"food_inputs"},
    "lumber_mill": {"name":"Lumber Mill","kind":"produce","inputs":{"fuel":1.5,"labor":1},"output":"lumber"},
    "steel_mill":  {"name":"Steel Mill","kind":"produce","inputs":{"energy":18,"labor":1},"output":"steel"},
    "textile":     {"name":"Textile Mill","kind":"produce","inputs":{"cotton":4,"energy":6,"labor":1},"output":"goods"},
    "tech_maker":  {"name":"Tech Components Maker","kind":"produce","inputs":{"tech_comp":0,"labor":1,"energy":5},"output":"tech_comp"},
    "furniture":   {"name":"Furniture Factory","kind":"consume","inputs":{"lumber":2,"steel":0.4,"labor":2,"packaging":0.5},"output":"goods"},
    "restaurant":  {"name":"Restaurant","kind":"consume","inputs":{"food_inputs":3,"packaging":1,"labor":2},"output":None},
    "retail":      {"name":"Retail Store","kind":"consume","inputs":{"goods":1,"packaging":0.3,"labor":1},"output":None},
    "logistics":   {"name":"Logistics","kind":"consume","inputs":{"fuel":5,"labor":1},"output":None},
    "ecom":        {"name":"E-commerce","kind":"consume","inputs":{"goods":1,"tech_comp":0.2,"packaging":0.8,"labor":1},"output":None},
}

# which starter business consumes which industry's inputs (for monthly exposure)
BIZ_TO_INDUSTRY = {
    "food_truck":"restaurant", "ecom_store":"ecom", "lawn_care":"logistics",
    "digital_agency":"tech_maker", "consulting":"tech_maker", "cleaning":"logistics",
    "tutoring":"tech_maker", "dropshipping":"ecom", "flipping":"retail", "fitness":"logistics",
}

# ~ deterministic price index for a commodity at a given global month
def _seed(cid):
    return int(hashlib.md5(cid.encode()).hexdigest()[:8], 16)

def commodity_price(cid, month):
    name, base, vol, period = COMMODITIES[cid]
    phase = _seed(cid) % 360
    wave = math.sin((month + phase) * 2*math.pi / period) * vol      # cyclical
    noise = ((_seed(cid) + month*7919) % 1000) / 1000.0 - 0.5        # -0.5..0.5
    noise *= vol * 0.5
    ix = 1.0 + wave + noise
    return round(base * max(0.55, min(1.6, ix)), 3)

def input_basket(industry, month):
    """Return [{commodity, name, price, qty, cost}] + total, at current market prices."""
    ind = INDUSTRIES[industry]
    items=[]; total=0.0
    for cid, qty in ind["inputs"].items():
        if cid == "labor":  # labor is a cost-ish input; index ~1 (handled before price lookup)
            cost = qty * 220.0
            items.append({"commodity":"labor","name":"Labor","price":220.0,"qty":qty,"cost":round(cost,2),"is_labor":True})
            continue
        price = commodity_price(cid, month)
        if False: pass
        else:
            cost = price*qty; total += cost
            items.append({"commodity":cid,"name":COMMODITIES[cid][0],"price":price,"qty":qty,"cost":round(cost,2)})
    return {"industry":industry,"name":ind["name"],"items":items,
            "material_cost":round(total,2),"total_cost":round(total + sum(i["cost"] for i in items if i.get("is_labor")),2)}

def materials_mod(industry, month):
    """Multiplier on the materials bill vs a baseline (month 0) — the 'input-cost pressure'."""
    if industry not in INDUSTRIES: return 1.0
    base = input_basket(industry, 0)["material_cost"]
    now  = input_basket(industry, month)["material_cost"]
    return round(now / base, 3) if base else 1.0

def market_snapshot(month):
    prices=[]
    for cid in COMMODITIES:
        p=commodity_price(cid, month); base=COMMODITIES[cid][1]
        prices.append({"id":cid,"name":COMMODITIES[cid][0],"price":p,
                       "index":round(p/base,2), "trend": "up" if p>base else ("down" if p<base else "flat")})
    chain=[]
    for iid, ind in INDUSTRIES.items():
        chain.append({"id":iid,"name":ind["name"],"kind":ind["kind"],
                      "inputs":list(ind["inputs"].keys()),"output":ind["output"]})
    return {"month":month,"prices":prices,"chain":chain}

def supplier_offers(business_id, city, month, limit=4):
    """NPC suppliers bidding to sell a business its inputs, priced off the market index."""
    industry = BIZ_TO_INDUSTRY.get(business_id)
    if not industry or industry not in INDUSTRIES: return []
    ind = INDUSTRIES[industry]
    offers=[]
    names=["Pioneer Supply Co.","Northstar Distributors","Lakeshore Depot","Meridian Foods","Anchor Logistics","Santiago Materials"]
    for i,(cid,qty) in enumerate(list(ind["inputs"].items())[:limit]):
        if cid=="labor": continue
        price=commodity_price(cid, month)
        offer_price=round(price*(1.0 + ((_seed(cid)*7+i)%10)/100.0 - 0.05), 3)  # slight discount/competition
        offers.append({"commodity":cid,"name":COMMODITIES[cid][0],
                       "market":price,"offer":offer_price,
                       "qty":qty,"supplier":names[i % len(names)]})
    return offers

# ------------------------------------------------------------------ producer businesses (players as suppliers)
# id -> {name, industry, output, units_per_month, setup_cost, blurb}
PRODUCERS = {
    "farm":      {"name":"Farm","industry":"farm","output":"food_inputs","units_per_month":600,"setup_cost":2200,
                  "blurb":"Grow food ingredients. Inputs: fuel + labor. You sell what you produce."},
    "lumber":    {"name":"Lumber Mill","industry":"lumber_mill","output":"lumber","units_per_month":650,"setup_cost":3100,
                  "blurb":"Cut and mill lumber. Feeds furniture factories and builders."},
    "steel":     {"name":"Steel Mill","industry":"steel_mill","output":"steel","units_per_month":420,"setup_cost":4600,
                  "blurb":"Produce steel. Energy-hungry; feeds heavy industry."},
    "tech":      {"name":"Tech Components Maker","industry":"tech_maker","output":"tech_comp","units_per_month":120,"setup_cost":3800,
                  "blurb":"Manufacture tech components for digital & e-commerce businesses."},
    "textile":   {"name":"Textile & Goods Mill","industry":"textile","output":"goods","units_per_month":300,"setup_cost":3000,
                  "blurb":"Weave cotton into finished goods for distributors and retail."},
}
PRODUCER_OUTPUT = {v["output"]: k for k, v in PRODUCERS.items()}

# deterministic base demand per commodity (units/month the market will absorb)
def base_demand(cid, month):
    """Units/month the market absorbs. Cheaper than usual => more bought; dearer => less.
    Cheap bulk goods trade in bigger volumes than high-value components."""
    import hashlib
    seed = int(hashlib.md5(("demand|"+cid).encode()).hexdigest()[:8], 16)
    base_p = COMMODITIES[cid][1] if cid in COMMODITIES else 1.0
    rel = commodity_price(cid, month) / base_p            # 1.0 = normal price
    elasticity = max(0.35, min(1.9, 1.0 + (1.0 - rel) * 1.1))
    volume = {"food_inputs":1050,"lumber":300,"steel":215,"tech_comp":80,"goods":210,"cotton":600,
              "grain":900,"fuel":700,"packaging":800,"energy":3000}.get(cid, 400)
    return max(40, int(volume * elasticity * (1.0 + (seed % 20) / 100.0)))


def producer_monthly(prod_id, city, month, selling_price, col_ix=None, biz_ix=None, demand_units=None, cash=None):
    """Run one production month for a player-owned producer.
    Units sold = min(produced, market demand for the commodity). Returns full economics."""
    pr = PRODUCERS[prod_id]
    produced = pr["units_per_month"]
    dem = demand_units if demand_units is not None else base_demand(pr["output"], month)
    sold = min(produced, dem)
    revenue = sold * selling_price
    basket = input_basket(pr["industry"], month)
    expenses = basket["total_cost"] + 0.05 * pr["setup_cost"] + 60.0   # inputs + upkeep scaled to plant size
    net = revenue - expenses
    return {"producer":pr["name"],"output":pr["output"],"produced":produced,"demand":dem,
            "sold":sold,"unsold":produced-sold,"revenue":round(revenue,2),
            "expenses":round(expenses,2),"net":round(net,2),
            "input_cost":round(basket["total_cost"],2),"price":selling_price}

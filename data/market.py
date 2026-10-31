"""
EMPIRE ONE — the living business world.
- NPC COMPANIES that behave like real businesses: they post service contracts and you
  can earn their trust until you own their rights.
- FREELANCE CONTRACTS you sell your services against (web dev, marketing, sales, ops, finance).
- REAL-COACH MARKETPLACE: real humans listing paid coaching sessions.
- REAL-BUSINESS RIGHTS MARKET: real businesses listed so players can buy the rights/equity.
"""

# ---------------------------------------------------------------- NPC companies
# id, name, sector, base_reputation, blurb
NPC_COMPANIES = [
    ("nimbus_saas",     "Nimbus Cloud (Virtual SaaS)",      "Software / SaaS",        30,
     "Growth-stage software company. They need marketing and product talent to scale."),
    ("redline_mfg",     "Redline Manufacturing (Virtual)",  "Manufacturing",          25,
     "Regional manufacturer (the one for sale in the deal room). Needs sales & operations."),
    ("elyria_d2c",      "Elyria Beauty (Virtual)",          "D2C E-commerce",         28,
     "Direct-to-consumer cosmetics brand fighting for shelf space and ad efficiency."),
    ("copperline_log",  "Copperline Logistics (Virtual)",   "Logistics",              22,
     "Freight and warehousing operator running on thin margins — needs efficiency."),
    ("brightpath_hlth", "Brightpath Health (Virtual)",      "Health & Care",          35,
     "Virtual-care provider growing fast. Needs customer success and sales leaders."),
]

# ---------------------------------------------------------------- freelance contracts (sell your services)
CONTRACTS = [
    # id, company_id, title, service, skills_used, budget, difficulty(1-5), days
    ("c_web1",  "nimbus_saas",     "Rebuild the SaaS landing page",       "web_dev",    ["strategy","operations"], 2200, 3, 5),
    ("c_mkt1",  "nimbus_saas",     "Launch a demo-to-customer funnel",    "marketing",  ["sales","communication"], 1800, 3, 6),
    ("c_mkt2",  "elyria_d2c",      "UGC social media campaign",           "marketing",  ["sales","communication"], 1500, 2, 4),
    ("c_dev2",  "elyria_d2c",      "Shopify checkout optimization",       "web_dev",    ["operations","finance"],   2000, 3, 5),
    ("c_sales1","redline_mfg",     "Win 2 enterprise supply contracts",   "sales",      ["sales","negotiation"],    2600, 4, 7),
    ("c_ops1",  "redline_mfg",     "Cut production waste 15%",            "consulting", ["operations","finance"],    2400, 4, 6),
    ("c_ops2",  "copperline_log",  "Re-route fleet to cut costs",         "consulting", ["operations","strategy"],   2100, 4, 5),
    ("c_fin1",  "copperline_log",  "Fix the cash-flow model",             "finance",    ["finance","negotiation"],   1900, 3, 4),
    ("c_cs1",   "brightpath_hlth", "Design a client-success playbook",    "consulting", ["communication","operations"],1700, 2, 4),
    ("c_sales2","brightpath_hlth", "Onboard 3 clinic partners",           "sales",      ["sales","communication"],   2300, 3, 6),
]
SERVICE_LABEL = {"web_dev":"Web / Product", "marketing":"Marketing",
                 "sales":"Sales", "consulting":"Strategy / Ops", "finance":"Finance"}

# ---------------------------------------------------------------- real-coach marketplace
# id, name, title, specialty, rate_per_hr, bio
COACHES = [
    ("coach_maya", "Maya Delacroix", "Sales Director",    "sales",        85,
     "17 yrs B2B sales. Built a $40M ARR motion. Coaches closing calls live."),
    ("coach_ron",  "Ron Castellano", "Founder / Ex-VC",   "negotiation",  120,
     "Ex-VC turned founder. Nails term sheets, cap tables and dilution."),
    ("coach_ina",  "Ina Okafor",     "CEO & Coach",       "leadership",   95,
     "Scales founder-led teams to director-level structure without the burn."),
    ("coach_dev",  "Dev Park",       "Fractional CFO",    "finance",      110,
     "Fractional CFO for seed-stage. Unit economics, runway and fundraising."),
]

# ---------------------------------------------------------------- real-business rights market
# id, name, sector, price, revenue, margin, verified, kind, note
LISTINGS = [
    ("biz_bakery",  "Golden Crumb Bakery",            "Food & Retail",  45000, 120000, 0.18, True, "real",
     "Owner retiring. 6-yr client base. Real storefront; rights purchase is real equity via escrow."),
    ("biz_shopify", "Maple & Pine E-Store",           "E-commerce",     62000, 168000, 0.22, True, "real",
     "Dropship + branded goods, 14k/mo traffic. Verified revenue docs."),
    ("biz_mfg",     "Redline Manufacturing (Rights)", "Manufacturing", 90000, 300000, 0.20, True, "npc",
     "Fully own the virtual manufacturer you've been dealing with (ties to the deal room)."),
    ("biz_saas",    "Nimbus Cloud (Rights)",          "Software / SaaS",75000, 220000, 0.35, True, "npc",
     "Acquire a controlling stake in the virtual SaaS. Earns recurring + dividends."),
    ("biz_clean",   "Dustless Cleaning Co.",          "Services",        28000, 96000, 0.24, False,"real",
     "Recurring commercial cleaning contracts. Rights pending owner KYC."),
]
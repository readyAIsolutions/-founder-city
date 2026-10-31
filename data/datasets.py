"""
EMPIRE ONE — static datasets.
Real US geography for the "start here, relocate with your capital" mechanic.
COL = cost-of-living index (100 = national average). BIZ = local business-opportunity index (0-100).
"""

# name, state, lat, lon, COL, BIZ, metro_pop_millions
CITIES = [
    ("New York",     "NY", 40.7128, -74.0060, 187, 92, 19.0),
    ("Los Angeles",  "CA", 34.0522, -118.2437, 162, 88, 13.2),
    ("Chicago",      "IL", 41.8781, -87.6298, 114, 78, 9.4),
    ("Houston",      "TX", 29.7604, -95.3698, 101, 80, 7.1),
    ("Phoenix",      "AZ", 33.4484, -112.0740, 103, 76, 4.9),
    ("Philadelphia", "PA", 39.9526, -75.1652, 109, 74, 6.1),
    ("San Antonio",  "TX", 29.4252, -98.4936,  91, 72, 2.6),
    ("San Diego",    "CA", 32.7157, -117.1611, 152, 84, 3.3),
    ("Dallas",       "TX", 32.7767, -96.7970,  98, 86, 7.8),
    ("San Jose",     "CA", 37.3382, -121.8863, 159, 90, 2.0),
    ("Austin",       "TX", 30.2672, -97.7431, 113, 94, 2.4),
    ("Jacksonville", "FL", 30.3322, -81.6557,  95, 70, 1.6),
    ("Fort Worth",   "TX", 32.7555, -97.3308,  94, 74, 2.1),
    ("Columbus",     "OH", 39.9612, -82.9988,  92, 72, 2.2),
    ("Charlotte",    "NC", 35.2271, -80.8431,  97, 82, 2.7),
    ("Indianapolis", "IN", 39.7684, -86.1581,  89, 72, 2.1),
    ("Seattle",      "WA", 47.6062, -122.3321, 149, 91, 4.0),
    ("Denver",       "CO", 39.7392, -104.9903, 114, 88, 3.0),
    ("Washington",   "DC", 38.9072, -77.0369, 160, 90, 6.3),
    ("Boston",       "MA", 42.3601, -71.0589, 139, 88, 4.9),
    ("Nashville",    "TN", 36.1627, -86.7816, 102, 84, 2.1),
    ("Detroit",      "MI", 42.3314, -83.0458,  91, 74, 4.3),
    ("Portland",     "OR", 45.5152, -122.6784, 121, 78, 2.5),
    ("Oklahoma City","OK", 35.4676, -97.5164,  88, 72, 1.4),
    ("Las Vegas",    "NV", 36.1699, -115.1398, 107, 74, 2.3),
    ("Louisville",   "KY", 38.2527, -85.7585,  93, 70, 1.3),
    ("Memphis",      "TN", 35.1495, -90.0490,  90, 70, 1.3),
    ("Baltimore",    "MD", 39.2904, -76.6122, 103, 72, 2.8),
    ("Milwaukee",    "WI", 43.0389, -87.9065,  96, 72, 1.6),
    ("Albuquerque",  "NM", 35.0844, -106.6504,  92, 68, 0.9),
    ("Tucson",       "AZ", 32.2226, -110.9747,  94, 68, 1.0),
    ("Sacramento",   "CA", 38.5816, -121.4944, 117, 76, 2.4),
    ("Kansas City",  "MO", 39.0997, -94.5786,  93, 74, 2.2),
    ("Atlanta",      "GA", 33.7490, -84.3880, 102, 88, 6.3),
    ("Miami",        "FL", 25.7617, -80.1918, 114, 84, 6.1),
    ("Orlando",      "FL", 28.5383, -81.3792, 102, 78, 2.7),
    ("Tampa",        "FL", 27.9506, -82.4572, 102, 78, 3.2),
    ("Minneapolis",  "MN", 44.9778, -93.2650, 109, 82, 3.7),
    ("St. Louis",    "MO", 38.6270, -90.1994,  94, 74, 2.8),
    ("Pittsburgh",   "PA", 40.4406, -79.9959,  97, 72, 2.4),
    ("Cincinnati",   "OH", 39.1031, -84.5120,  95, 74, 2.3),
    ("Salt Lake City","UT",40.7608, -111.8910, 106, 78, 2.6),
    ("Boise",        "ID", 43.6150, -116.2023,  99, 80, 0.8),
    ("Raleigh",      "NC", 35.7796, -78.6382, 103, 84, 1.5),
    ("Fargo",        "ND", 46.8772, -96.7898,  95, 74, 0.3),
    ("Cheyenne",     "WY", 41.1400, -104.8202,  98, 70, 0.1),
    ("Billings",     "MT", 45.7833, -108.5007,  96, 72, 0.2),
    ("Anchorage",    "AK", 61.2181, -149.9003, 121, 64, 0.4),
    ("Honolulu",     "HI", 21.3069, -157.8583, 170, 80, 1.0),
    ("Des Moines",   "IA", 41.5868, -93.6250,  93, 74, 0.7),
]

# id, name, category, start_cost_usd, gross_margin(0-1), demand_driver(1-5), blurb
BUSINESSES = [
    ("food_truck",  "Food Truck",        "Food & Hospitality", 1400, 0.62, 3, "High foot-traffic, low overhead. Margins live or die on your location."),
    ("ecom_store",  "E-Commerce Store",  "Retail",             1200, 0.48, 4, "Online storefront. Scale fast, but shipping + ad costs eat margins."),
    ("lawn_care",   "Lawn Care",         "Services",            700, 0.72, 2, "Cheapest to start. Recurring local customers, weather-dependent."),
    ("digital_agency", "Digital Agency", "Professional Svcs",  900, 0.80, 4, "Sell websites/ads/marketing. High margin, you must win clients."),
    ("consulting",  "Consulting",        "Professional Svcs",  800, 0.85, 3, "Sell your expertise. Almost no inventory, entirely relationship-driven."),
    ("cleaning",    "Cleaning Service",  "Services",            600, 0.70, 3, "Steady demand everywhere. Labor-heavy, low barriers."),
    ("tutoring",    "Tutoring",          "Education",           500, 0.82, 2, "Local + online students. High margin, capped by your hours."),
    ("dropshipping","Dropshipping",      "Retail",             800, 0.35, 4, "No inventory. Global reach, razor-thin margin, fierce competition."),
    ("flipping",    "Resale / Flipping", "Trade",               900, 0.55, 3, "Buy low, sell higher. Cash-sensitive, needs sharp deal instinct."),
    ("fitness",     "Fitness Coaching",  "Health & Wellness",  700, 0.88, 2, "Online + in-person coaching. Premium pricing, niche audiences."),
]

LEVELS = [
    (1, "The Hustler",  "Start a business, find customers, make your first profit."),
    (2, "The Deal Maker", "Negotiate contracts, learn persuasion and due diligence."),
    (3, "The Investor", "Buy property/companies, analyze financials, manage risk."),
    (4, "The Mogul",    "Build corporations, hire teams, expand globally, own markets."),
]

DEFAULT_START = 5000.0
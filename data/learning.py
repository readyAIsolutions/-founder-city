"""
EMPIRE ONE — Learning Lab content.
Audio-book curriculum (with Audible links) and Sales/CEO spoken-classes.
Every item teaches skills (skill: skill-points) and yields XP + a one-time
earned-money completion bonus (anti-exploit: minutes give XP/skill only,
money is a one-time BOOK bonus, not infinite per-minute cash).
"""

# id, title, author, category, hours, skill_deltas, one_time_cash
BOOKS = [
    ("rich_dad_poor_dad", "Rich Dad Poor Dad", "Robert Kiyosaki", "Money & Mindset",
     6.5, {"finance": 10, "mindset": 8, "sales": 4}, 1500),
    ("think_and_grow_rich", "Think and Grow Rich", "Napoleon Hill", "Mindset & Sales",
     8.0, {"sales": 9, "mindset": 10, "leadership": 4}, 1800),
    ("the_e-myth", "The E-Myth Revisited", "Michael Gerber", "Entrepreneurship",
     7.0, {"operations": 9, "leadership": 6, "finance": 4}, 1600),
    ("zero_to_one", "Zero to One", "Peter Thiel", "Strategy & Innovation",
     6.0, {"strategy": 10, "finance": 5, "mindset": 5}, 1800),
    ("how_to_win_friends", "How to Win Friends & Influence People", "Dale Carnegie", "Communication",
     6.0, {"sales": 8, "communication": 10, "leadership": 5}, 1500),
    ("atomic_habits", "Atomic Habits", "James Clear", "Execution",
     5.5, {"mindset": 8, "operations": 7, "leadership": 3}, 1200),
    ("the_48_laws", "The 48 Laws of Power", "Robert Greene", "Strategy",
     7.5, {"strategy": 9, "sales": 7, "communication": 4}, 1700),
    ("lean_startup", "The Lean Startup", "Eric Ries", "Entrepreneurship",
     7.0, {"operations": 9, "finance": 6, "strategy": 6}, 1700),
]
# Audible product search URL builders (deep-link to the title search so it works without API keys)
AUDIBLE_SEARCH = "https://www.audible.com/search?keywords={}"

# id, title, category, minutes, skill_deltas, cash, exercise
CLASSES = [
    ("close_the_deal",  "Close the Deal — Sales Script Mastery",   "Sales",   25,
     {"sales": 12, "communication": 10}, 900,
     "Write one pitch email for YOUR real business using the AIDA structure taught in-class."),
    ("ceo_communication", "Speak Like a CEO — Boardroom & Investor", "Leadership", 30,
     {"communication": 12, "leadership": 10}, 1000,
     "Record a 60-second investor pitch for a real idea. Paste the transcript for review."),
    ("negotiator_psych", "The Psychology of Negotiation",          "Negotiation", 28,
     {"negotiation": 12, "sales": 6}, 950,
     "Roleplay one negotiation from your real life in text form and plan your counter-offers."),
    ("pitch_the_vc",     "Pitching VCs & Raising Capital",         "Finance",    35,
     {"finance": 10, "communication": 8, "leadership": 8}, 1100,
     "Build a 3-line funding ask: how much, for what, what's the return."),
]

LEVEL_STEPS = [
    (1000,  "Sailor"),
    (3000,  "Merchant"),
    (7000,  "Tycoon"),
    (14000, "Banker"),
    (24000, "Mogul"),
    (40000, "Investor Icon"),
]
# v4 — expanded self-improvement / reading
BOOKS += [
    ("magic_words", "The Magic of Selling (Magic Words)", "Sales Classic", "Sales Performance",
     5.0, {"sales": 10, "communication": 8, "negotiation": 5}, 1400),
    ("the_psych_of_money", "The Psychology of Money", "Morgan Housel", "Money & Mindset",
     6.5, {"finance": 10, "mindset": 7}, 1600),
    ("never_split_diff", "Never Split the Difference", "Chris Voss", "Negotiation",
     7.0, {"negotiation": 12, "sales": 7, "communication": 5}, 1700),
    ("the_7_habits", "The 7 Habits of Highly Effective People", "Stephen Covey", "Effectiveness",
     10.0, {"leadership": 9, "mindset": 8, "operations": 5}, 1800),
    ("cashflow_quadrant", "Rich Dad's CASHFLOW Quadrant", "Robert Kiyosaki", "Investing",
     6.5, {"finance": 10, "investing": 8, "mindset": 5}, 1600),
    ("sales_bible", "The Sales Bible", "Jeffrey Gitomer", "Sales Performance",
     8.0, {"sales": 12, "persuasion": 8, "communication": 6}, 1750),
]
CLASSES += [
    ("read_business_books", "Read Business Books for Life", "Reading", 40,
     {"mindset": 8, "strategy": 6, "finance": 5}, 0,
     "Read a full business book, then pass the comprehension test in-game to certify it."),
]

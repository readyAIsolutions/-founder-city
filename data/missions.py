"""
FOUNDER CITY — Real World Missions (the centrepiece).
Voluntary challenges players complete outside the virtual world. AI helps review
submissions, but consequential verification is a human/operator step (evidence-based).
Participation XP on submit; bigger verified payout on confirmation.
"""
# id, title, task, skill, submit_xp, verified_xp, verified_cash, skill_deltas
MISSIONS = [
    ("m_bizplan", "Write a real business plan",
     "Create a legitimate 1-page business plan for a real idea. Paste the doc/Notion/Gdoc link — no need to share financials.",
     "strategy", 150, 1300, 1500, {"strategy": 12, "finance": 6}),
    ("m_research", "Interview 3 real potential customers",
     "Talk to three real people about a problem you want to solve. Submit your notes (names optional).",
     "market", 150, 900, 1000, {"sales": 10, "communication": 5}),
    ("m_salespitch", "Deliver a practice sales presentation",
     "Record or rehearse a short sales pitch for a real product/idea. Submit the transcript or practice log.",
     "communication", 150, 1000, 1100, {"communication": 12, "sales": 8}),
    ("m_course", "Complete an accredited course",
     "Finish a real course — online or local (business, finance, sales, or your trade). Submit proof of completion.",
     "learning", 150, 1200, 900, {"mindset": 8, "finance": 6}),
    ("m_prototype", "Build a working product prototype",
     "Build a real prototype — software, physical, service or brand. Submit a link or photo.",
     "operations", 150, 1600, 2000, {"operations": 14, "strategy": 8}),
    ("m_teamcheck", "Collaborate on a real project",
     "Work with real people on a real project. Submit a short report on what you built together.",
     "leadership", 150, 1300, 1500, {"leadership": 12, "communication": 6}),
]
MISSION = {m[0]: m for m in MISSIONS}
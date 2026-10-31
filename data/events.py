"""
FOUNDER CITY — live events scaffold (Fortnite-style recurring engagement).
Events are deterministic: entry outcome is seeded by (player, event, month) and driven by the
player's RELEVANT skill — never by RNG that ignores their actual ability.
"""

# id -> {type, title, blurb, cadence, skill, base_xp, base_cash, min_level}
EVENTS = {
    "evt_neg10": {
        "type":"tournament","title":"Weekly Negotiation Tournament — 'Procurement Push'",
        "blurb":"Haggle for the week's biggest supply contract against rivals. Your negotiation rating decides the margin you can win.",
        "cadence":"weekly","skill":"negotiation","base_xp":650,"base_cash":750,"min_level":1},
    "evt_sales10": {
        "type":"tournament","title":"Sales Championship — 'Big-Client Week'",
        "blurb":"Close the week's flagship client. Prospecting, objection-handling and your sales rating stack the odds.",
        "cadence":"weekly","skill":"sales","base_xp":550,"base_cash":680,"min_level":1},
    "evt_pitch10": {
        "type":"event","title":"Startup Pitch Night",
        "blurb":"Pitch your business to a virtual panel. Communication + leadership determine how the room receives you.",
        "cadence":"monthly","skill":"communication","base_xp":800,"base_cash":1150,"min_level":2},
    "evt_expand10": {
        "type":"challenge","title":"Regional Expansion Challenge",
        "blurb":"Plan and fund an expansion into a neighboring market. Strategy + finance decide how smoothly you land.",
        "cadence":"monthly","skill":"strategy","base_xp":950,"base_cash":1250,"min_level":2},
}
EVENT = {k: v for k, v in EVENTS.items()}
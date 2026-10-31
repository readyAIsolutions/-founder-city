# FOUNDER CITY — Game Design Document

**Working title:** Founder City *(formerly EMPIRE ONE)*
**Tagline:** Build a virtual empire. Develop real skills. Create real opportunities.
**Genre:** Massively-multiplayer entrepreneurial life-simulation / business RPG + professional network.
**Status:** Living GDD — grounded in a running MVP at `http://localhost:8010`.

> Design principle (from research on GTA VI, Fortnite, The Sims 4, SimCity, Cities: Skylines II,
> Roblox, Virtonomics & business sims): **GTA's immersion + The Sims's personal lives + SimCity's
> economy + Fortnite's social engagement + Roblox's creativity + AI-powered business education —
> welded into ONE connected world.**
>
> Founder City is *not* another GTA or SimCity. It's a business-life simulation where the economy,
> the social world, and the education system are the SAME system.

---

## 0. Executive summary

Founder City is a multiplayer entrepreneurial world where players live, work, compete, create
businesses, develop real skills, and form real professional relationships. It is designed to be
**entertainment first**, with business education woven into the gameplay — the player learns by
doing, negotiating, failing, and compounding.

Three features define the product:

1. **An AI world that remembers you.** Characters, rivals, and the mentor respond to your history
   and decisions (persistent memory).
2. **One persistent, connected economy.** Businesses have real dependencies; players cooperate and
   compete inside consistent accounting.
3. **Your gameplay improves your real-world abilities.** Learning, practice, and *verified*
   achievements become part of progression and, optionally, real evidence.

The revenue target is **US$100k MRR**, to be proven through retention and recurring gross margin —
not by a fancy city. Visual quality attracts; compelling loop + meaningful progression + community retires.

---

## 1. Player fantasy & core loop

**The fantasy:** "I start with nothing in my real hometown. Over months of smart decisions I build a
regional business, then a national corporation, and I get measurably better at business — for real."

**First 30 minutes (must be fun immediately, no 10-hour tutorial):**
1. Create a character — pick a hometown, career interests, a personal goal.
2. Receive a first opportunity — an AI business owner offers a commission-based sales job.
3. Talk to a first customer (text, or voice when live) — discover needs, negotiate a sale.
4. Get a first reward — fictional income, coaching, new opportunities unlocked.
5. Meet a player — visit the local business lounge, find a partnership.
6. Start a business — use earnings + skills to launch a small company.

**Meta-loop:** *Explore → Opportunity → Act (run a month / close a deal / do a mission) → Economic
consequence → Coaching + skill growth → New, harder opportunity.*

The player chooses *how* to win:
- Become an emperor (own everything), a specialist (category king), a networker (coordinate others),
  or an investor (own equity without operating). Specialists are first-class, not second-class.

---

## 2. The ten major systems

Adapted (not copied) from the reference games.

| # | System | Inspired by | Status in build |
|---|--------|-------------|-----------------|
| 1 | **Living open world** — walk/drive/explore a business city, offices, conferences, nightlife | GTA | Map foundation live (17,105 cities, search, relocation); 3D district planned |
| 2 | **Personal life & lifestyle** — avatar, home, property, vehicles, friends, social status | The Sims | Property/rights purchasing live; avatar & home-lifestyle planned |
| 3 | **Realistic business economy** — start companies, hire, negotiate, acquire, expand | Capitalism Lab / Virtonomics | MVP live |
| 4 | **Multiplayer competition & events** — sales champs, pitch comps, expos, seasons | Fortnite | Live-events scaffolding planned |
| 5 | **Property & city development** — commercial buildings, neighbourhoods, factories, infrastructure | SimCity / CSII | Rights market live; infra layer planned |
| 6 | **AI characters with persistent memory** — customers, bankers, investors, competitors, coach | *signature* | **Live** (coach memory) |
| 7 | **Entrepreneur university** — books, courses, challenges, demonstrated skills | *real-world value* | **Live** (Learn + read-tests) |
| 8 | **Founder/Empire Passport** — professional profile, verified achievements, collaboration history | *real-world value* | **Live** (Passport) |
| 9 | **Player-created businesses** — shops, offices, products, ads; moderated marketplace later | Roblox | Creator-storefront planned |
| 10 | **Real-world business bridge** — mentors, collaborators, cofounders; game skill as evidence, not guarantee | *signature* | Live (missions, linkedin, coach/rights markets) |

---

## 3. The Living Career System (signature differentiator)

Unlike fixed classes, players can **change careers and run multiple businesses**, with one evolving
character sheet. Example path: *virtual car salesperson → dealership manager → own a dealership →
expand into financing and manufacturing.*

Ten career tracks available and changeable:
Entrepreneur/Founder · Sales professional · CEO/Executive · Investor/Financial analyst ·
Real-estate developer · Manufacturer · Logistics operator · Marketing specialist ·
Engineer/Technology founder · Business consultant.

As a character's demonstrated skills grow, the AI coach raises the difficulty of the challenges it
generates (adaptive difficulty).

---

## 4. The connected economy (more important than the giant map)

Lesson from Cities: Skylines II: model the *relationships* between production, distribution,
retail, customers, financing and transportation — not isolated numbers.

Example chain:
```
Player-owned manufacturer (furniture, Chicago) → Player-owned distributor → Retail stores → Customers
        ↓                                         ↓                             ↓
   Sales revenue                        transportation costs                demand
        ↓                                         ↓                             ↓
   Hiring & expansion                     margins collapse if fuel↑      if demand collapses, cut output
        ↓                                         ↓
   Banks & financing                    if a supplier goes bankrupt, find a new source
```

**HARD RULE (the financial engine):** AI creates believable *characters and events*;
it **never invents financial results.** All money, revenue, margins, debt, prices and ownership use
one **consistent, auditable accounting + economic rules engine.** This is already the architecture
(NPC contracts and monthly_sim are deterministic calculations; LLM is used for personas/opportunities
only). This is the difference between a game and a slot machine.

**Implementation today:** monthly business simulation (revenue/rent/labor/materials + market cycle),
freelance contract execution, negotiation settlements, rights/dividends, XP-band trade. The
player-to-player dependency graph (producers sell to retailers) is the next economic layer.

---

## 5. Scalable city system (three layers)

Goal: support *every* US city without building thousands of full 3D maps.

| Layer | Experience | Priority |
|-------|-----------|----------|
| **National map** | Select cities, inspect markets, move HQ, plan expansion | **Launch** |
| **Local business district** | Walk around, meet players, operate businesses, events | **Launch in one test city (e.g., a US metro)** |
| **Detailed city world** | Transportation, commercial property, housing, neighbourhoods, landmarks | **Long-term** |

Each non-flagship city has documented, distinct *simulated conditions* (business index, COL,
competitive density) rather than a bespoke 3D map — so hundreds of cities are playable now and
flagship worlds are developed as the community grows.

---

## 6. AI character system (persistent memory)

**Already live:** the lifelong AI coach builds a personal memory card (strengths, weakest skill,
deals, books, meetings) and greets each player by name with targeted next-action advice. Executives
(Vera Alvarez/CFO, Marcus Bell/VP Sales, Priya Nair/Founder, Ingrid Solberg/Ops, Omar Haddad/Investor)
have personas + ElevenLabs voice ids and answer as live businesspeople when an LLM key is set
(honest deterministic fallback otherwise).

**Planned:** customers, bankers, rivals, and competitors each hold a persistent memory of prior
conversations and deals. Reputation is earned through *collaboration and results*, never purchased.

---

## 7. Entrepreneur university & the learning engine

**Participation vs certification:** reading a book earns participation XP; *proving* understanding
earns skill certification. Otherwise players click through to collect points.

- Books (Audible-linked): Think & Grow Rich, Rich Dad Poor Dad, The Magic of Selling, Never Split
  the Difference, Cashflow Quadrant, Psychology of Money, + — **live**.
- Listening minutes → XP + skill; finishing → money + passport certification — **live**.
- Comprehension test (read a real book) → verified skill — **live**.
- Audiobook upload (evidence) — **live** (verify gate).
- Classes: Sales scripts, Speak-Like-a-CEO, Negotiation psychology, Pitch VCs — **live**.
- **Planned academies:** CEO, Sales, Investor, Marketing + a **Women's Entrepreneurship Academy**
  (mentorship groups, women-led networks, leadership dev, case studies).

Skill system (negotiation, sales, finance, communication, leadership, strategy, operations,
mindset, investing, persuasion) is taught and *tested in practical simulations*, not video badges.

---

## 8. Found Passport / Founder Network

A professional profile separate from the character:
interests, verified achievements, business experience, demonstrated skills, collaboration history,
and reputation. In-game network ("Empire/Founder Network") lets players:
- Search by city, industry, skill, interest
- Find partners & mentors
- Recruit teammates to operate virtual companies
- Form clubs, chambers, investment-education groups
- Attend virtual conferences/networking events
- Build problem-solving portfolios
- Apply for real opportunities posted by verified businesses

**Status in build:** Passport live; XP-band matchmaking + player messaging live; LinkedIn linking
(+XP) live. Full in-game network (search by industry/interest, clubs, conferences) is the next build.

**LinkedIn reality:** use optional sign-in + basic profile with the user's consent; build our own
networking features because advanced LinkedIn access (connections/messages) is restricted and
unreliable — we do **not** depend on unavailable permissions.

---

## 9. Multiplayer architecture

- Backend: FastAPI + SQLite (single process now; scales to Postgres + async workers).
- Player identity, companies, contracts, market, rights, messaging, missions persist server-side.
- Multiplayer interaction today: shared economy affects, XP-band matching, player-to-player
  messaging. Planned: real-time business lounge presence, player-owned storefronts selling to other
  players, cooperative missions, tournaments.
- **Design rule:** the same economic engine furnishes NPC and player-facing results so there is one
  fair economic truth that no AI can distort.

---

## 10. Real-world bridge & trust boundary

Bridge (consenting, verified adults): find mentors/collaborators/cofounders; real opportunities
posted by verified businesses; **Real World Missions** (the centrepiece) — write a real business
plan, interview real customers, deliver a real pitch, complete a real course, build a real
prototype, collaborate with real people. Submissions earn participation XP now; a **human/operator
verifier** confirms the big XP + money + reputation. Players never share sensitive financials or
personal customer info.

**What is intentionally OUT of the initial release (compliance / fraud / trust):**
1. Real-money investments or securities trading.
2. Real cash-out of fictional game wealth.
3. Unverified claims that players are qualified professionals based solely on gameplay.
4. Real settlement (coaches, business-rights, payouts) stays gated behind real provider
   credentials (Stripe/PayPal + onboarding) until configured.

**Firm rule:** a virtual billionaire is *never* presented as a trusted real investment advisor;
game points are *supporting evidence of skill*, not proof of professional competence.

---

## 11. Retention loops (why players return)

- **Daily:** new customers, contracts, challenges, coaching.
- **Weekly:** negotiation tournaments, business competitions.
- **Monthly:** regional expansion opportunities, economic events.
- **Social:** partnerships, clubs, conferences, cooperative missions.
- **Long-term:** real skill development and career progression.

Rewards are tied to **good decisions and meaningful achievements**, not time-served or spend.

---

## 12. Player progression

- **XP + level** (dual-gate: need both XP and closed deals): L1 Hustler → L2 Deal Maker →
  L3 Investor → L4 Mogul. **Live.**
- **Skills** grow from deals, books, classes, missions; feed negotiation odds + coach focus. **Live.**
- **Net worth** from cash, equity, owned rights, dividends. **Live.**
- **Reputation** earned via verified achievements. **Live.**
- XP sources now: books/classes/tests (real learning), deals, contracts, real meetings, LinkedIn,
  verified real-world attestations, Real World Missions.

---

## 13. Monetization (path to $100k MRR)

| Stream | Model |
|--------|-------|
| **Free game** | Build a large community (volume = moat) |
| **Founder Pro** | ~$29/mo: advanced simulations, AI coaching, professional tools |
| **Founder Academy** | Premium training for schools/business programs/companies |
| **Later (consent-gated)** | Verified businesses pay for recruiting / talent discovery |

Metrics to track from day one: paying-user retention, acquisition cost, **AI cost per active
player**, recurring gross margin. 3,449 paying members × $29 ≈ $100k MRR — a target, not a
guarantee; validated before heavy spend.

---

## 14. MVP vs later priorities

| Feature | MVP | Later |
|---|---|---|
| One explorable 3D business district | | ✓ (flagship city) |
| Three starter business types | ✓ | |
| AI sales & negotiation characters | ✓ | |
| Persistent mentor memory | ✓ | |
| Accounting & economic simulation | ✓ | |
| Multiplayer business lounge | ✓ (matching+msg) | richer |
| Founder Passport profiles | ✓ | |
| Business learning challenges | ✓ | |
| Hundreds of selectable cities | ✓ (17,105) | |
| Cars & extensive lifestyle | | ✓ |
| Player-created buildings/products | | ✓ |
| Real-world matchmaking | ✓ (missions/LinkedIn) | deeper |
| Advanced city government/infrastructure | | ✓ |

Note: the MVP is already substantial; per GDD we'd still re-scope after estimating production
resources, but the running build already covers the MVP row almost entirely.

---

## 15. Tech & first playable build

**Tech stack now:** Python FastAPI + SQLite, deterministic economic engine, LLM router (OpenRouter/
OpenAI), ElevenLabs voice gateway, Stripe/PayPal payout gateway, vanilla-JS dark/noir UI. Data:
17,105-city GeoNames US map, book/class/mission/market datasets. Launch: `start.sh`.

**First playable build (the deliverable that exists):** character + hometown, business creation &
monthly ops, AI negotiation + coach, Learn Lab, Real World Missions, Founder Passport + XP-band
network, Money (earned wallet + gated payouts), Nation (city search/explore + LLM-backed
executives + voice), Market (rights), Coaches (booking). All verified end-to-end in-browser.

**Roadmap**
> **Phase A STATUS — connected supply-chain economy: DONE & LIVE** (commodities, dependency
> chains, input-cost pressure, supply contracts). **Player-as-producer storefronts: DONE & LIVE**
> (5 producer businesses; P2P purchase + wallet transfer). **Live events: DONE & LIVE.**
> **Network discovery: DONE & LIVE.** **Stylized 3D business district: DONE & LIVE** — a walkable,
> clickable isometric district per city (HQ, lounge, market, corporate park, deal room, bank).
>
> ✅ **Phase A is COMPLETE** (all no-keys systems built and verified): connected supply chain,
> producer storefronts, live events, network discovery, 3D district.
- **AI is now LIVE (OpenRouter key configured).** Mentor, NPC executives and businesspeople
  answer through a real LLM (`deepseek/deepseek-chat` with fallbacks). Key lives only in the
  git-ignored `.env`.
- **Interaction is text-first.** Everything is typed today. Voice (ElevenLabs TTS) and voice-to-text
  are **future features** — hooks stay in the code but no UI triggers them yet.
- **Remaining unlocks:** ElevenLabs voices + voice-to-text (future), and a public deploy URL.
- **Phase B:** accreditation partnerships, verified mentors, course marketplace, tournaments.
- **Phase C:** international trade, large corporations, advanced economic events, education edition
  (sandbox config + Women's Entrepreneurship Academy).

---

## 16. Key decisions locked

1. **Adult, entrepreneur-first.** School/teen edition = future **sandbox config** (no real money,
   gated social, educator dashboard), not a present split.
2. **Financial engine never invented by AI.** Consistent, auditable accounting everywhere.
3. **Fictional ≠ real wealth/qualifications.** Hard separation, gated real-money paths.
4. **Real World Missions = centrepiece.** Evidence + human verification at the real/fiction seam.
5. **Retention before spectacle.** Validate the loop, progression and community against $100k/MRR.

---

## 17. One question for the next phase of design

Should the first flagship **3D business district** be stylized/procedural (ship across many cities
cheaply, recommended now) or photorealistic (more spectacle, higher cost, fewer cities first)?
Recommendation: **stylized/procedural first**, with one halo photorealistic flagship district later —
consistent with the "economic connectivity over giant map" priority.
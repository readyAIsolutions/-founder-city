# Founder City (formerly EMPIRE ONE) — Build your empire. Master the game. Change your reality.

The entrepreneurial RPG + business network. Start with $5,000, build a business in a living
city mapped to **real America**, negotiate deals with an AI that reacts and coaches you, and
relocate your operation using your own capital — all in one connected world where your
**Empire Passport** turns play into real networking.

## Learning, money & the real-world bridge (v2)

- **Learning Lab** — log listening minutes on a curriculum that includes **Rich Dad Poor Dad**,
  **Think and Grow Rich**, *The E-Myth*, *Zero to One*, *How to Win Friends*, *Atomic Habits*,
  *The 48 Laws* and *The Lean Startup* (deep-linked to **Audible**). Minutes earn **XP + skill
  points**; finishing a book pays a **one-time earned-money bonus** and certifies your passport.
- **Speak Like a Salesman & CEO** — spoken classes on sales scripts, boardroom/investor language,
  negotiation psychology and pitching VCs. Complete the real exercise, pass (60+), and earn
  earned-money + certified communication skills.
- **Real-world bridge** — submit a live link to a real business/software you built; a sponsor
  verifies it and you earn **+$3,000** to your wallet and **+2,500 XP**.
- **Earned wallet & cash-out (Stripe / PayPal)** — every player holds an earned-money wallet.
  Connect a Stripe account or PayPal email. **Honest by design:** payouts stay **pending** and no
  money moves until real provider credentials are configured (`STRIPE_SECRET_KEY`, `PAYPAL_CLIENT_ID/SECRET`).
  Watch the server startup for processor status at `/api/payments/status`.
- **Level = XP + deals (dual gate)** — you climb only when you have BOTH the experience points AND
  the closed deals (L2: 1k XP + 1 deal; L3: 7k XP + 3 deals; L4: 24k XP + 6 deals).

## Payment integration (needs your credentials to go live)

Real payouts are implemented in `payments.py` (Stripe Connect transfers + PayPal REST payouts)
and activate only when these environment variables exist at server start:

```
STRIPE_SECRET_KEY=sk_live_...        # enables real Stripe transfers
PAYPAL_CLIENT_ID=... PAYPAL_SECRET=... PAYPAL_MODE=sandbox|live
```

Until then every payout request is recorded as **pending** with a clear message. To go live you
must also complete Stripe Connect / PayPal merchant onboarding + KYC and store each player's
connected account id (the `/payout/connect` endpoint holds that reference).

## Run it

```
cd /home/nova/empire-one
python3 -m uvicorn server:app --host 0.0.0.0 --port 8010
```

(Or: `./start.sh`)

Open:
- **Investor / demo landing + live stats dashboard:**  `http://localhost:8010/`
- **Playable game:**                            `http://localhost:8010/game`

## What's real and working (verified end-to-end)

- **Anchor to real America** — geolocate to start in *your* town/state, or pick from 50 real
  US cities (lat/lon, cost-of-living index, business-opportunity index, metro population).
- **The "$5,000 you're born with" relocation rule** — moving your business to another city
  costs you **real capital** from your money. Local moves are cheap; cross-country is
  expensive; high-COL cities cost more to enter. Not enough cash? Earn more first.
- **10 starter businesses** with distinct cost, margin and demand — starting one deducts
  from your cash, then simulates monthly operations with **real economics**: revenue,
  rent (local COL), labor, materials, overhead and a **live market cycle** (boom/slump).
- **AI negotiation engine** — buy a company or lease a storefront against an AI counterpart
  with a real personality (greedy/eager/tough/straight), hidden financials and *hidden risk*
  (e.g. one customer = 43% of revenue). Ask due-diligence questions, make offers, field
  counters and walkaways.
- **AI coach review (the killer feature)** — after every deal, your mentor scores you on
  *negotiation*, *due diligence* and *communication* and spells out what you missed — like
  the customer-concentration you never asked about.
- **Empire Passport** — a professional profile separate from your character: verified
  industry, demonstrated skills, reputation, and a business network you build by closing deals.
- **Investor dashboard** — live global stats, economy value, relocations, deals closed and a
  live leaderboard, all visible on the landing page.

## Stack

- **Backend:** Python FastAPI + SQLite (single process, no external deps beyond fastapi/uvicorn)
- **Game engine:** `engine.py` — pure, seeded, deterministic (unit-testable) geo/business/negotiation logic
- **Datasets:** `data/datasets.py` — real US cities + business catalog
- **Frontend:** vanilla JS + dark/noir cinematic CSS (no build step)

## Honest limits (this is an MVP, not the full vision)

- Multiplayer is single-player localhost right now; no account system, payments, or identity
  verification. It is **not** deployed publicly yet — investors can only reach it once you
  deploy (see below).
- "AI" negotiation is a **deterministic rules engine**, not an LLM — it reliably simulates a
  counterpart + coach without any API key. Wiring it to a real LLM router for open-ended
  voice/text negotiation is the natural next increment.
- Real securities/investment activity is intentionally **out** of the game (Canada/US
  registration concerns); investing here is simulated company/property acquisition only.
- No real-money transactions, no verified real-world matchmaking yet — those come after MVP validation.

## Deployment (to let real investors in)

The API + static site are a single FastAPI process — deploy anywhere you like:
- **Render.com / Railway / Fly.io** — point at `uvicorn server:app`, add the `empire.db` is auto-created.
- **Vercel/Netlify** need an adapter (or serve static + a backend separately).
- Quick public demo while iterating: a tunnel e.g. `cloudflared tunnel --url http://localhost:8010`.

Then hand investors the public URL — `/` is the pitch + live dashboard, `/game` is the playable demo.
## Living world — players, NPCs, coaches & reality (v3)

- **NPC companies act like real businesses.** They post freelance contracts (web dev, marketing,
  sales, ops, finance). Sell your services to them — take a contract, deliver, get paid + XP +
  trust. High trust unlocks owning their rights.
- **Real-business rights marketplace.** Real and virtual businesses are listed for sale. Buy the
  rights with your earned wallet → hold equity + in-game dividends. Real settlement via Stripe/PayPal
  when creds are live (records are kept regardless).
- **Paid real-coach marketplace.** Real expert coaches (sales, negotiation, leadership, finance)
  list hourly rates. Book a live session on Google Meet/Zoom, paid from your earned wallet.
- **Merge reality with the game.** Connect Google Meet / Zoom / Slack; log a real meeting and the
  recording/notes fold into your NPC mentor's knowledge. **Every real connection earns XP** (the
  more real people you meet, the more XP).
- **AI Business Mentor (EMP).** An NPC mentor that advises on sales, negotiation, leadership and
  investing. When `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) is set it answers through a **live LLM**
  and remembers your logged meetings; without a key it honestly falls back to deterministic coaching
  (no fake LLM). Requires the meet/slack/zoom creds + Stripe/PayPal + LLM key to go fully live.

## Nationwide USA + AI at the core (v4)
- **The map is all of America.** data/us_cities.json holds **17,105 real US cities** (GeoNames:
  name, state, lat/lon) across all 51 states/territories. Start or relocate anywhere. Each city has
  an AI-generated ecology (local businesses + national corporations), a business-opportunity index,
  and a cost-of-living factor that flows into the sim.
- **LLM-backed businesspeople & characters** who think/respond like real executives. Live LLM needs
  `OPENROUTER_API_KEY`/`OPENAI_API_KEY`; **ElevenLabs** voices need `ELEVENLABS_API_KEY`.
- **XP-band network**: match & message players within ~15% of your XP.
- **Verifiable reading**: expanded books (Think & Grow Rich, Rich Dad, The Magic of Selling, Never
  Split the Difference, Cashflow Quadrant, +). Upload the audiobook or pass a comprehension test.
- **LinkedIn** link → +800 XP.
- See `docs/AI_AT_THE_CORE.md` for the AI strategy.

## Connected supply-chain economy (Phase A #1) — LIVE
- **Commodity markets with deterministic prices.** Fuel, grain, lumber, steel, cotton, tech
  components, food inputs, packaging, energy, finished goods — each has a seeded price cycle
  (index up/down). AI never invents these; the rules engine sets them.
- **Industry dependency chains.** Producers (farm, lumber mill, steel mill, textile, tech maker)
  feed consumers (furniture factory, restaurant, retail, logistics, e-commerce). Each consumes
  real inputs at market prices.
- **Input-cost pressure in your own business.** Run a month and your materials bill tracks the
  commodity market — when inputs spike, margins compress (observed: net went $104 → -$125 when
  input costs rose ~40%).
- **Supply contracts.** NPC suppliers (Pioneer Supply Co., Northstar Distributors, …) bid to sell
  you inputs; sign a contract to lock the price and trim your input bill ~7%. Duplicate contracts
  are rejected.
- **Economy tab** shows the live commodity board, the supply-chain graph, your exposure, and offers.

## Player-as-producer storefronts (Phase A #2) — LIVE
- **Start a producer business.** Farm, Lumber Mill, Steel Mill, Tech Components Maker, Textile &
  Goods Mill — each produces a commodity and consumes real inputs.
- **Surplus posts to the player supply market.** Every production month, unsold output is offered
  to all players at a price near market.
- **Real player-to-player commerce.** A player running a consuming business (restaurant, factory,
  e-commerce, retail, logistics) can BUY from another player's offer — the money flows wallet-to-
  wallet. Verified: MillOwner's steel sold 30u to FactoryOwner → MillOwner wallet +$150.60.
- **Locked supply.** Buyers who purchase get their input locked ~7% cheaper; NPC suppliers remain in
  the same market so it's one economy. Producers and buyers share the same demand/supply truth.

## Live events + in-network discovery (Phase A #3) — LIVE
- **Live events & competitions.** Weekly negotiation/sales tournaments + monthly startup-pitch and
  regional-expansion challenges. Outcomes are seeded deterministically by your actual skill (never
  RNG) — high skill = better placements, podium bonuses. Entering is gated on having a business and
  level; each event pays XP + money once per cycle and blocks re-entry.
- **In-network discovery.** Search players by name, city, industry, or interest (set from your
  profile). Founder City's "LinkedIn meets the virtual world" is now searchable.

## Stylized 3D business district (Phase A #4) — LIVE
- **District tab** renders your city as a walkable isometric business street (WASD/arrows to walk,
  click a building to enter). One district per city, showing Your HQ, Marketplace, Deal Room,
  Business Lounge, Corporate Park (the city's corporations), Learning Hall, and Bank.
- Fully browser-native canvas rendering — no 3D engine dependency, works offline. This is the
  GDD's "local business district" middle tier; the national map + detailed flagship worlds sit
  around it on the same playable world.

## Live LLM (OpenRouter) — ON
- `OPENROUTER_API_KEY` is now configured (stored in git-ignored `.env`, loaded by `start.sh`).
  The AI business mentor, NPC executives, and businesspeople answer through a **live LLM**
  (`deepseek/deepseek-chat` by default, with fallbacks) instead of the deterministic fallback.
- **Security:** the key lives only in `.env` (git-ignored), never in source or committed files.
  To rotate: edit `.env` and restart.

## Interaction model: TEXT-FIRST (as of this build)
- **All in-game interaction is typed.** Talk to the AI mentor and NPC executives by typing;
  everything is text. No voice controls in the UI.
- **Voice is a FUTURE feature** (ElevenLabs TTS for characters, and voice-to-text for the player).
  The integration hooks remain in `payments.py`/`nation.py` and the `speak` endpoint, but nothing
  in the UI triggers them yet. Planned for a later release when an ElevenLabs key + speech-to-text
  provider are added.

## Audit pass: security, anti-exploit, balance
- Player handles are sanitised server-side; the UI escapes all player-supplied text (no HTML injection).
- Verification of real-world missions/attestations is operator-only (needs `FC_ADMIN_TOKEN` in `.env`);
  players can no longer self-verify for XP/money. Review queue: `python3 fc_operator.py list`.
- Fixed: negative/zero supply purchases, messaging yourself, duplicate mission submits, unlimited book XP.
- Rebalanced: starter businesses pay back in ~1-8 months (city size matters); producers 2-6 months; market demand now scales by commodity.
- Regression: `python3 tests/smoke_test.py` (server running).

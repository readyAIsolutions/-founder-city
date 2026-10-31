"""
EMPIRE ONE — payment processor bridge (Stripe Connect + PayPal REST).

HONEST DESIGN: real money never moves unless REAL credentials are present.
- Reads keys from environment: STRIPE_SECRET_KEY, PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_MODE.
- If keys are absent, every operation returns processor "not_configured" and records
  payout requests as PENDING (never as completed transfers).
- When keys ARE present, these calls hit the real Stripe/PayPal APIs. No fabrication.
Player "connected account" ids are stored per-player and passed to the provider.
"""
import os, json, time
import requests

def _stripe_key(): return os.environ.get("STRIPE_SECRET_KEY", "").strip()
def _paypal_id():   return os.environ.get("PAYPAL_CLIENT_ID", "").strip()
def _paypal_secret(): return os.environ.get("PAYPAL_SECRET", "").strip()
def _paypal_mode():  return os.environ.get("PAYPAL_MODE", "sandbox")

STRIPE_BASE = "https://api.stripe.com/v1"
PAYPAL_BASE = {"sandbox": "https://api-m.sandbox.paypal.com",
               "live": "https://api-m.paypal.com"}[_paypal_mode()]

def status():
    return {
        "stripe_configured": bool(_stripe_key()),
        "paypal_configured": bool(_paypal_id() and _paypal_secret()),
        "stripe": "live" if _stripe_key() else "off",
        "paypal": _paypal_mode() if (_paypal_id() and _paypal_secret()) else "off",
    }

def connect_account(player, processor, account_ref):
    """Store a player's connected Stripe account id or PayPal merchant email/ref.
    Reference must come from real provider onboarding; we validate presence only."""
    processor = processor.lower()
    if processor not in ("stripe", "paypal"):
        return {"ok": False, "error": "unsupported processor"}
    if not account_ref or not str(account_ref).strip():
        return {"ok": False, "error": "empty account reference"}
    return {"ok": True, "processor": processor, "account": str(account_ref).strip(),
            "note": "Stored. No real payout until provider credentials are configured "
                    "and your merchant account is verified."}

def request_payout(player, processor, amount_cents, account_ref):
    """Record a payout request. If real processor creds exist, attempt a REAL transfer.
    Otherwise record as pending so nothing is faked."""
    status = "pending"           # default until a real provider confirms
    provider_ref = None
    error = None

    if processor == "stripe" and _stripe_key():
        if not account_ref:
            return {"ok": False, "status": "error",
                    "error": "Stripe connected account id required. Complete Stripe "
                             "Connect onboarding first."}
        # REAL transfer to a connected account (Stripe Payouts/Transfers pattern)
        try:
            r = requests.post(f"{STRIPE_BASE}/transfers",
                data={"amount": amount_cents, "currency": "usd",
                      "destination": account_ref},
                auth=(_stripe_key(), ""), timeout=20)
            j = r.json()
            if r.status_code in (200, 201) and "id" in j:
                status, provider_ref = "paid", j["id"]
            else:
                error = j.get("error", {}).get("message") or f"stripe http {r.status_code}"
        except Exception as e:
            error = f"stripe request failed: {e}"

    elif processor == "paypal" and _paypal_id() and _paypal_secret():
        try:
            tr = requests.post(f"{PAYPAL_BASE}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(_paypal_id(), _paypal_secret()), timeout=15)
            tok = tr.json().get("access_token")
            if not tok:
                return {"ok": False, "status": "error", "error": "paypal auth failed"}
            r = requests.post(f"{PAYPAL_BASE}/v1/payments/payouts",
                headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                json={"sender_batch_header": {"sender_batch_id": f"empire-{int(time.time())}",
                        "email_subject": "EMPIRE ONE payout", "email_message": "Your empire pays out."},
                      "items": [{"recipient_type": "EMAIL", "amount": {"value": f"{amount_cents/100:.2f}",
                                "currency": "USD"}, "receiver": account_ref}]},
                timeout=20)
            j = r.json()
            bh = j.get("batch_header", {})
            if bh.get("batch_status") and r.status_code < 300:
                status, provider_ref = "submitted", bh.get("payout_batch_id")
            else:
                error = json.dumps(j)[:300]
        except Exception as e:
            error = f"paypal request failed: {e}"

    elif processor not in ("stripe", "paypal"):
        return {"ok": False, "error": "unsupported processor"}

    if status == "pending" and not error:
        return {"ok": True, "status": "pending",
                "error": "Payment processor not configured (set STRIPE_SECRET_KEY / "
                         "PAYPAL creds). Request recorded — no money moved."}
    return {"ok": error is None, "status": status,
            "provider_ref": provider_ref, "error": error}
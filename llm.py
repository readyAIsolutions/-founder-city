"""
FOUNDER CITY — LLM router for NPC intelligence & the AI business mentor.

Reality-first: talks to a REAL LLM only when credentials are configured.
- Reads env: OPENROUTER_API_KEY (or OPENAI_API_KEY) + optional LLM_MODEL.
- Robust: retries with backoff and tries a fallback model, so live answers are reliable rather
  than flaky. Returns None only if every attempt fails -> callers fall back to deterministic
  content (never fakes that an LLM answered when none did).

Compatible with OpenRouter / OpenAI / any OpenAI-compatible gateway.
"""
import os, json, time
import requests


def _key():
    return (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()

def _base():
    if os.environ.get("OPENROUTER_API_KEY"):
        return "https://openrouter.ai/api/v1"
    return "https://api.openai.com/v1"

def _default_model():
    if os.environ.get("OPENROUTER_API_KEY"):
        return "deepseek/deepseek-chat"      # cheap + fast + reliable on OpenRouter
    return "gpt-4o-mini"

def _model():
    return os.environ.get("LLM_MODEL") or _default_model()

def configured():
    return bool(_key())

def _attempt(model, headers, payload, timeout):
    r = requests.post(f"{_base()}/chat/completions",
                      headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def chat(system, user, temperature=0.7, max_tokens=400):
    """Return assistant text, or None if no LLM is configured / every attempt fails."""
    k = _key()
    if not k:
        return None
    headers = {"Authorization": f"Bearer {k}", "Content-Type": "application/json"}
    if os.environ.get("OPENROUTER_API_KEY"):
        headers["HTTP-Referer"] = "http://localhost:8010"
        headers["X-Title"] = "FounderCity"
    models = []
    if os.environ.get("LLM_MODEL"): models.append(os.environ["LLM_MODEL"])
    models.append(_default_model())
    # fallbacks: try configured, then 1-2 reliable cheaper models
    fb = ["deepseek/deepseek-chat", "openai/gpt-4o-mini", "mistralai/mistral-small-3.1-24b-instruct"]
    for m in fb:
        if m not in models:
            models.append(m)
            break
    payload = {"temperature": temperature, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}
    last_err = None
    for attempt in range(6):
        model = models[min(attempt, len(models) - 1)]
        pl = dict(payload); pl["model"] = model
        try:
            return _attempt(model, headers, pl, timeout=45)
        except requests.exceptions.HTTPError as e:
            last_err = e
            code = e.response.status_code if e.response is not None else 0
            if code == 429 or code >= 500:
                time.sleep(0.6 * (attempt + 1))   # rate-limit / server backoff
                continue
            if code == 400 and "model" in str(getattr(e.response, "text", "")):
                continue                          # bad model id -> try next model
            return None
        except Exception as e:
            last_err = e
            time.sleep(0.4)
    # give up but note why (cosmetic, not surfaced to players as a hard error)
    return None
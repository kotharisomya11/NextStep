"""
JUGAAD #1: session-wide cost guard.

The brief asks for a call-count limit on tools like search. What it
doesn't ask for: a limit on actual COST across a whole session. One call
on a giant pasted WhatsApp export costs far more than several short
calls, so a raw call-count cap alone can still let a session burn through
a lot of budget unnoticed. This tracks real token usage per session and
stops before the next Gemini call, instead of failing silently or mid-call.

In-memory only (resets on server restart) -- fine for this prototype;
swap for Redis/DB if this ever needs to survive restarts.
"""

import os
import time

MAX_CALLS = int(os.getenv("BUDGET_MAX_CALLS", 15))
MAX_TOKENS = int(os.getenv("BUDGET_MAX_TOKENS", 30000))

_sessions: dict[str, dict] = {}


class BudgetExceeded(Exception):
    pass


def _get(session_id: str) -> dict:
    return _sessions.setdefault(session_id, {"calls": 0, "tokens": 0, "started_at": time.time()})


def check(session_id: str):
    s = _get(session_id)
    if s["calls"] >= MAX_CALLS or s["tokens"] >= MAX_TOKENS:
        raise BudgetExceeded(
            f"This session hit its budget limit ({s['calls']} calls / {s['tokens']} tokens used; "
            f"limits are {MAX_CALLS} calls / {MAX_TOKENS} tokens)."
        )


def track(session_id: str, tokens_used: int):
    s = _get(session_id)
    s["calls"] += 1
    s["tokens"] += tokens_used


def status(session_id: str) -> dict:
    return dict(_get(session_id))
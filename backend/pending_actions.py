"""
JUGAAD #2: stale-draft invalidation.

The brief covers confirming before an irreversible action runs. What it
doesn't cover: what happens to an OLD unconfirmed draft when the user's
situation changes before they get around to confirming it. Without this,
a user could confirm a message that was drafted based on outdated
information (e.g. the deadline changed, but they approve the old draft
anyway). Every new /agent call for a session marks any earlier pending
action for that session as "stale" so it can never be blindly confirmed.

In-memory only, same caveat as budget.py.
"""

import time
import uuid

_pending: dict[str, dict] = {}


def add_pending(session_id: str, tool: str, payload: dict) -> str:
    action_id = str(uuid.uuid4())
    _pending[action_id] = {
        "session_id": session_id,
        "tool": tool,
        "payload": payload,
        "status": "pending",
        "created_at": time.time(),
    }
    return action_id


def invalidate_stale(session_id: str) -> int:
    count = 0
    for action in _pending.values():
        if action["session_id"] == session_id and action["status"] == "pending":
            action["status"] = "stale"
            count += 1
    return count


def confirm(action_id: str) -> dict:
    action = _pending.get(action_id)
    if not action:
        return {"status": "unknown_action"}
    if action["status"] == "executed":
        # idempotent: confirming twice (e.g. a retried request) never re-sends
        return {"status": "already_executed", "action": action}
    if action["status"] == "stale":
        return {"status": "stale",
                "message": "This draft is out of date because the situation changed. Ask NextStep again."}
    if action["status"] == "cancelled":
        return {"status": "cancelled"}
    action["status"] = "executed"
    action["executed_at"] = time.time()
    return {"status": "executed", "action": action}


def cancel(action_id: str) -> dict:
    action = _pending.get(action_id)
    if not action:
        return {"status": "unknown_action"}
    if action["status"] == "pending":
        action["status"] = "cancelled"
    return {"status": action["status"], "action": action}
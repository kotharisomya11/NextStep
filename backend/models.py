from pydantic import BaseModel
from typing import Optional


class PendingAction(BaseModel):
    tool: str
    recipient: str = ""
    purpose: str = ""
    draft_text: str = ""


class AgentResponse(BaseModel):
    understanding: str
    reason: str
    ask: str
    recommend: str
    next_step: str

    # --- added for the 7 shared scenarios ---
    urgency: str = "medium"                # "low" | "medium" | "high"
    risk_flag: bool = False                # true if user shows signs of emotional crisis
    out_of_scope: bool = False             # true if request is unrelated misuse
    injection_detected: bool = False       # true if pasted content tried to instruct the AI
    confidence: float = 0.5

    # If the model wants to draft something that would need a human's OK
    # before anything is sent, it fills this in instead of just doing it.
    pending_action: Optional[PendingAction] = None
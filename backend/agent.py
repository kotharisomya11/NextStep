from backend.provider.gemini_provider import GeminiProvider
from backend.budget import BudgetExceeded
from backend import pending_actions
from backend.safety import AT_RISK_SUPPORT_MESSAGE, OUT_OF_SCOPE_MESSAGE


class NextStepAgent:

    def __init__(self):
        self.provider = GeminiProvider()

    def run(self, user_input: str, session_id: str = "default"):
        # Jugaad #2: a new message for this session means any earlier
        # unconfirmed draft is now potentially outdated.
        invalidated = pending_actions.invalidate_stale(session_id)

        try:
            response = self.provider.generate(user_input, session_id=session_id)
        except BudgetExceeded as e:
            return {"status": "budget_exceeded", "message": str(e)}

        # --- safety gates: deterministic Python, not trusted to LLM wording ---
        if response.risk_flag:
            return {
                "status": "support_mode",
                "understanding": response.understanding,
                "reason": "The user may be in emotional distress.",
                "ask": "",
                "recommend": AT_RISK_SUPPORT_MESSAGE,
                "next_step": "",
            }

        if response.out_of_scope:
            return {
                "status": "out_of_scope",
                "understanding": response.understanding,
                "reason": "Request is unrelated to a personal situation.",
                "ask": "",
                "recommend": OUT_OF_SCOPE_MESSAGE,
                "next_step": "",
            }

        result = {
            "status": "ok",
            "understanding": response.understanding,
            "reason": response.reason,
            "ask": response.ask,
            "recommend": response.recommend,
            "next_step": response.next_step,
            "urgency": response.urgency,
            "confidence": response.confidence,
            "injection_detected": response.injection_detected,
            "stale_actions_invalidated": invalidated,
        }

        if response.pending_action:
            action_id = pending_actions.add_pending(
                session_id=session_id,
                tool=response.pending_action.tool,
                payload=response.pending_action.model_dump(),
            )
            result["pending_action"] = {
                "action_id": action_id,
                **response.pending_action.model_dump(),
                "requires_confirmation": True,
            }

        return result

    def confirm_action(self, action_id: str):
        return pending_actions.confirm(action_id)

    def cancel_action(self, action_id: str):
        return pending_actions.cancel(action_id)
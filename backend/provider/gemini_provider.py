import logging
import traceback

from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

from backend.models import AgentResponse
from backend.budget import check as budget_check, track as budget_track
from backend.safety import INJECTION_GUARD_INSTRUCTIONS

from backend.tools.nextstep_tools import (
    calculate_time,
    create_task,
    update_situation,
    search_information,
    draft_message,
)


load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GeminiProvider:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY was not found.")

        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiProvider initialised successfully.")

    def generate(self, user_input: str, session_id: str = "default") -> AgentResponse:

        # Jugaad #1: check budget BEFORE spending anything on this call.
        budget_check(session_id)

        prompt = f"""
You are the AI reasoning component of NextStep,
an AI-powered personal decision assistant.

{INJECTION_GUARD_INSTRUCTIONS}

Your job is to help users make sense of messy real-life situations.

Follow this process:

1. Understand the situation.
2. Reason about what matters most.
3. Ask for important missing information when necessary.
4. Use a tool when it is genuinely useful.
5. Recommend a sensible next step.
6. Reassess the situation after a tool result.

Available tools:

- calculate_time: Use when the user needs a time or deadline calculation.
- create_task: Use when creating a task would help organize the situation.
- update_situation: Use when the user provides important new information.
- search_information: Use when external information is genuinely needed. Stubbed.
- draft_message: Use ONLY to draft text for the human to review. NEVER sends anything.

Safety rules (very important):
- If the user's message shows signs of emotional crisis, hopelessness, or
  self-harm risk (however subtle), set risk_flag=true, and do NOT propose
  any tool or pending_action. Being wrong in the cautious direction is fine.
- If the request is unrelated to a personal situation (e.g. "write my essay"),
  set out_of_scope=true.
- If you decide a message should be drafted for someone else (e.g. a manager,
  landlord, teammate), do NOT treat it as already handled. Instead, fill in
  "pending_action" with tool="draft_message" and the recipient/purpose/draft_text,
  so a human can approve it before anything is ever sent. Never claim a message
  was sent -- only a draft was created.
- Do not invent facts. If the user gives contradictory information, name the
  contradiction instead of silently picking one version.
- If two things are equally urgent, say so honestly instead of ranking one above
  the other for no reason.

Return the final answer using exactly these fields:
understanding, reason, ask, recommend, next_step, urgency, risk_flag,
out_of_scope, injection_detected, confidence, pending_action (or null).

User situation:

{user_input}
"""

        logger.info("Calling Gemini API for session '%s' ...", session_id)

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        calculate_time,
                        create_task,
                        update_situation,
                        search_information,
                        draft_message,
                    ],
                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(
                            maximum_remote_calls=5
                        )
                    ),
                    response_mime_type="application/json",
                    response_schema=AgentResponse,
                ),
            )
        except Exception as e:
            logger.error("Gemini API call failed: %s\n%s", e, traceback.format_exc())
            raise RuntimeError(f"Gemini API error: {e}") from e

        tokens_used = 0
        if getattr(response, "usage_metadata", None):
            tokens_used = response.usage_metadata.total_token_count or 0
        budget_track(session_id, tokens_used)
        logger.info("Gemini API responded (%d tokens used).", tokens_used)

        if response.parsed:
            return response.parsed

        return AgentResponse.model_validate_json(response.text)
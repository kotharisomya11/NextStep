import logging
import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from pydantic import BaseModel
from backend.agent import NextStepAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NextStep AI Decision Assistant",
    description="AI-powered agent for understanding situations, reasoning about next steps, and assisting users with actions.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = NextStepAgent()


class UserRequest(BaseModel):
    message: str
    session_id: str = "default"   # send the same value across calls to test budget + staleness





@app.post("/agent")
def run_agent(request: UserRequest):
    try:
        return agent.run(request.message, request.session_id)
    except Exception as e:
        logger.error(
            "Error in /agent for session '%s': %s\n%s",
            request.session_id, e, traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Backend error: {e}",
            },
        )


@app.post("/agent/confirm/{action_id}")
def confirm_action(action_id: str):
    try:
        return agent.confirm_action(action_id)
    except Exception as e:
        logger.error("Error in /agent/confirm/%s: %s\n%s", action_id, e, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Backend error: {e}"},
        )


@app.post("/agent/cancel/{action_id}")
def cancel_action(action_id: str):
    try:
        return agent.cancel_action(action_id)
    except Exception as e:
        logger.error("Error in /agent/cancel/%s: %s\n%s", action_id, e, traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Backend error: {e}"},
        )

# Serve the frontend statically
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
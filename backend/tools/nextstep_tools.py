from datetime import datetime, timedelta
from typing import Dict, Any


tasks = {}
situations = {}


def calculate_time(
    start_time: str,
    end_time: str
) -> Dict[str, Any]:
    """
    Calculate the amount of time between two timestamps.

    Expected format:
    YYYY-MM-DD HH:MM
    """

    start = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    end = datetime.strptime(end_time, "%Y-%m-%d %H:%M")

    if end < start:
        return {
            "success": False,
            "error": "End time cannot be before start time."
        }

    duration = end - start

    total_minutes = int(duration.total_seconds() / 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    return {
        "success": True,
        "start_time": start_time,
        "end_time": end_time,
        "total_minutes": total_minutes,
        "hours": hours,
        "minutes": minutes
    }


def create_task(
    title: str,
    deadline: str = None
) -> Dict[str, Any]:
    """
    Create a task in memory.

    Tasks are reversible, so creating a task does not require
    confirmation in our current design.
    """

    task_id = f"TASK-{len(tasks) + 1}"

    task = {
        "task_id": task_id,
        "title": title,
        "deadline": deadline,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    tasks[task_id] = task

    return {
        "success": True,
        "message": "Task created successfully.",
        "task": task
    }


def update_situation(
    situation_id: str,
    information: str
) -> Dict[str, Any]:
    """
    Store or update information about a user's situation.
    """

    if situation_id not in situations:
        situations[situation_id] = {
            "situation_id": situation_id,
            "information": [],
            "updated_at": None
        }

    situations[situation_id]["information"].append(information)
    situations[situation_id]["updated_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "message": "Situation updated successfully.",
        "situation": situations[situation_id]
    }


def search_information(
    query: str
) -> Dict[str, Any]:
    """
    Stubbed information-search tool.

    In the challenge, this can later be connected to a real
    search/API service. For now, it returns a safe mock result.
    """

    return {
        "success": True,
        "query": query,
        "source": "stub",
        "results": [
            {
                "title": "Mock search result",
                "summary": (
                    "This is a placeholder result. "
                    "A real information-search service can be connected later."
                )
            }
        ]
    }


def draft_message(
    recipient: str,
    purpose: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    Draft a message without sending it.

    Drafting is reversible.
    Sending the message would be a separate consequential action
    and would require explicit user confirmation.
    """

    message = f"Hi {recipient},\n\n"

    if context:
        message += f"{context}\n\n"

    message += f"I wanted to discuss {purpose} with you.\n\n"
    message += "Please let me know when you are available.\n\n"
    message += "Thank you."

    return {
        "success": True,
        "recipient": recipient,
        "purpose": purpose,
        "draft": message,
        "status": "draft",
        "requires_confirmation_before_sending": True
    }
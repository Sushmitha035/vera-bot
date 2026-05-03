from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uuid

app = FastAPI()

sessions: Dict[str, Dict[str, Any]] = {}

# ---------------------------
# Models
# ---------------------------
class ContextRequest(BaseModel):
    merchant: dict
    trigger: dict

class TickRequest(BaseModel):
    session_id: str

class ReplyRequest(BaseModel):
    session_id: str

# ---------------------------
# Logic
# ---------------------------

def classify_trigger(event: str):
    e = event.lower()

    if "rating" in e or "review" in e:
        return "reputation"
    elif "sales" in e or "footfall" in e:
        return "growth"
    elif "festival" in e:
        return "festival"
    elif "competitor" in e:
        return "competition"
    else:
        return "general"


def decide_actions(trigger_type, business_type):
    actions = []

    if trigger_type == "reputation":
        actions = [
            "Respond to recent negative reviews with clear resolution",
            "Ask satisfied customers for Google reviews",
            "Improve service quality based on feedback",
            "Upload 10+ high-quality photos to your listing",
            "Highlight best-selling dishes"
        ]

    elif trigger_type == "growth":
        actions = [
            "Run targeted weekday discount campaigns",
            "Promote offers via WhatsApp broadcast",
            "List your business on discovery platforms",
            "Create combo deals to increase order value",
            "Highlight popular items"
        ]

    elif trigger_type == "festival":
        actions = [
            "Launch a limited-time festive offer",
            "Promote offers on social channels",
            "Create special combo packages",
            "Decorate listing with festive visuals",
            "Send offers to repeat customers"
        ]

    elif trigger_type == "competition":
        actions = [
            "Offer better-value combos than nearby competitors",
            "Highlight unique selling points",
            "Run limited-time competitive pricing",
            "Improve online rating visibility",
            "Promote customer testimonials"
        ]

    else:
        actions = [
            "Improve online presence with updated information",
            "Run targeted promotional campaigns",
            "Engage actively with customers",
            "Enhance listing visuals and content",
            "Track and improve customer feedback"
        ]

    return actions


def generate_response(event, actions):
    msg = f"Hey! I noticed {event}.\n\n"
    msg += "Here’s what I recommend (in order of impact):\n\n"

    for i, act in enumerate(actions, 1):
        act_lower = act.lower()

        if "review" in act_lower:
            reason = "→ helps rebuild customer trust and improve your rating"
        elif "photo" in act_lower or "visual" in act_lower:
            reason = "→ improves visibility and attracts more customers"
        elif "combo" in act_lower:
            reason = "→ increases order value and simplifies decisions"
        elif "offer" in act_lower or "discount" in act_lower:
            reason = "→ drives more walk-ins and conversions"
        elif "highlight" in act_lower:
            reason = "→ guides customers and boosts conversions"
        else:
            reason = "→ improves overall business performance"

        msg += f"{i}. {act} {reason}\n"

    msg += "\nStart with the first 2 actions for quickest results."

    return msg


# ---------------------------
# Endpoints
# ---------------------------

@app.post("/v1/context")
def context(req: ContextRequest):
    session_id = str(uuid.uuid4())

    event = req.trigger.get("event", "").strip()
    if not event:
        event = "general business issue"

    sessions[session_id] = {
        "event": event,
        "merchant": req.merchant
    }

    return {"session_id": session_id}


@app.post("/v1/tick")
def tick(req: TickRequest):
    return {"status": "ok"}


@app.post("/v1/reply")
def reply(req: ReplyRequest):
    session = sessions.get(req.session_id)

    if not session:
        return {"error": "Invalid session_id"}

    event = session["event"]
    merchant = session["merchant"]

    trigger_type = classify_trigger(event)

    actions = decide_actions(
        trigger_type,
        merchant.get("category", "").lower()
    )

    message = generate_response(event, actions)

    return {"message": message}


@app.get("/v1/healthz")
def health():
    return {"status": "ok"}


@app.get("/v1/metadata")
def metadata():
    return {
        "bot_name": "vera-smart",
        "version": "final",
        "description": "High-quality deterministic merchant assistant"
    }

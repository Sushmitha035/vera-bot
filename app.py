from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uuid

app = FastAPI()

# ---------------------------
# Storage
# ---------------------------
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
# Core Logic
# ---------------------------

def parse_context(merchant, trigger):
    event = trigger.get("event")

    if not event or event.strip() == "":
        event = "general business issue"

    return {
        "business_type": merchant.get("category", "").lower(),
        "city": merchant.get("city", ""),
        "trigger_event": event.lower(),
    }

def classify_trigger(event):
    e = event.lower()

    if "rating" in e or "review" in e:
        return "reputation_fix"
    elif "footfall" in e or "low sales" in e:
        return "increase_walkins"
    elif "festival" in e or "diwali" in e or "season" in e:
        return "festival_campaign"
    elif "competitor" in e or "nearby" in e:
        return "competition"
    else:
        return "general"

def extract_signals(merchant):
    signals = []

    if merchant.get("rating", 5) < 4:
        signals.append("low_rating")

    if merchant.get("reviews", 0) < 50:
        signals.append("low_reviews")

    if merchant.get("photos", 0) < 5:
        signals.append("poor_visuals")

    return signals

def decide_actions(trigger_type, business_type, signals):
    actions = []

    # Priority 1: critical fixes
    if "low_rating" in signals:
        actions.append("Respond to recent negative reviews with clear resolution")
        actions.append("Ask satisfied customers for Google reviews")

    if "poor_visuals" in signals:
        actions.append("Upload 10+ high-quality photos to your Google listing")

    # Priority 2: trigger-based
    if trigger_type == "festival_campaign":
        actions.append("Launch a limited-time festive offer")
        actions.append("Promote it via WhatsApp broadcast")

    elif trigger_type == "increase_walkins":
        actions.append("Run weekday discount campaigns")
        actions.append("Enable local discovery offers")

    elif trigger_type == "competition":
        actions.append("Offer better-value combos than nearby competitors")

    # Priority 3: category-specific
    if business_type == "restaurant":
        actions.append("Add combo meals")
        actions.append("Highlight best-selling dishes")

    elif business_type == "salon":
        actions.append("Promote grooming packages")

    elif business_type == "gym":
        actions.append("Launch a free trial week")

    return actions[:5]


def generate_response(trigger_event, actions):
    msg = f"Hey! I noticed {trigger_event}.\n\n"
    msg += "Here’s what I recommend (in order of impact):\n\n"

    for i, act in enumerate(actions, 1):
        act_lower = act.lower()

        if "review" in act_lower:
            reason = "→ helps rebuild customer trust and improve your rating"
        elif "photo" in act_lower:
            reason = "→ improves visibility and attracts more customers"
        elif "combo" in act_lower or "meal" in act_lower:
            reason = "→ increases order value and simplifies customer choices"
        elif "best-selling" in act_lower:
            reason = "→ guides customers and boosts conversions"
        elif "offer" in act_lower or "discount" in act_lower:
            reason = "→ drives more walk-ins and sales"
        else:
            reason = "→ improves overall business performance"

        msg += f"{i}. {act} {reason}\n"

    msg += "\nStart with the first 2 actions for quickest results."

    return msg

# ---------------------------
# Endpoints
# ---------------------------

@app.post("/v1/context")
def set_context(req: ContextRequest):
    session_id = str(uuid.uuid4())

    parsed = parse_context(req.merchant, req.trigger)

    sessions[session_id] = {
        "parsed": parsed,
        "merchant": req.merchant,
        "trigger": req.trigger
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

    merchant = session["merchant"]
    trigger = session["trigger"]
    parsed = session["parsed"]

    event = trigger.get("event", parsed["trigger_event"])

    trigger_type = classify_trigger(event)
    signals = extract_signals(merchant)

    actions = decide_actions(
        trigger_type,
        parsed["business_type"],
        signals
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
        "version": "3.0",
        "description": "Context-aware merchant assistant"
    }

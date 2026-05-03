from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uuid

app = FastAPI()

sessions: Dict[str, Dict[str, Any]] = {}
 
class ContextRequest(BaseModel):
    merchant: dict
    trigger: dict

class TickRequest(BaseModel):
    session_id: str

class ReplyRequest(BaseModel):
    session_id: str

# -------- LOGIC -------- #

def parse_context(merchant, trigger):
    return{
        "business_type": merchant.get("category", "").lower(),
        "city": merchant.get("city", ""),
        "trigger_event": trigger.get("event", "some recent issue").lower(),
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

def decide_actions(trigger_type, business_type):
    ACTIONS = {
        "reputation_fix": [
            "Reply to last 5 negative reviews with apology and fix",
            "Ask happy customers for Google reviews",
            "Upload 10 high-quality photos on Google"
        ],
        "festival_campaign": [
            "Create a limited-time festive offer",
            "Bundle your best-selling items",
            "Promote via WhatsApp broadcast"
        ],
        "increase_walkins": [
            "Run weekday discounts",
            "Enable local offers on magicpin",
            "Improve storefront visibility"
        ],
        "general": [
            "Improve online presence",
            "Run targeted promotions"
        ]
    }

    CATEGORY = {
        "restaurant": ["Add combo meals", "Highlight best-selling dishes"],
        "salon": ["Offer grooming packages", "Promote weekend slots"],
        "gym": ["Launch free trial week", "Promote transformation stories"]
    }

    actions = ACTIONS.get(trigger_type, []) + CATEGORY.get(business_type, [])
    return actions[:5]

def generate_response(parsed, actions):
    msg = f"Hey! I noticed {parsed['trigger_event']}.\n\n"
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

# -------- ENDPOINTS -------- #

@app.post("/v1/context")
def set_context(req: ContextRequest):
    session_id = str(uuid.uuid4())

    parsed = parse_context(req.merchant, req.trigger)

    sessions[session_id] = {
        "parsed": parsed
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

    parsed = session["parsed"]
    trigger_type = classify_trigger(parsed["trigger_event"])
    actions = decide_actions(trigger_type, parsed["business_type"])
    message = generate_response(parsed, actions)

    return {"message": message}

@app.get("/v1/healthz")
def health():
    return {"status": "ok"}

@app.get("/v1/metadata")
def metadata():
    return {
        "bot_name": "vera-lite",
        "version": "1.0",
        "status": "running"
    }

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import stripe

load_dotenv()
app = FastAPI(title="ZenithCordAI API")

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://zenithcordai.vercel.app")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_FREE = os.getenv("PRICE_FREE", "")
PRICE_STARTER = os.getenv("PRICE_STARTER", "")
PRICE_PRO = os.getenv("PRICE_PRO", "")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you like
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactBody(BaseModel):
    name: str
    email: EmailStr
    message: str

class DemoBody(BaseModel):
    message: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/contact")
async def contact(body: ContactBody):
    # You can plug email/DB here later
    print("CONTACT:", body.dict())
    return {"ok": True}

@app.post("/demo-chat")
async def demo_chat(body: DemoBody):
    msg = body.message.lower()
    if "price" in msg or "cost" in msg:
        return {"reply": "Starter £25/mo • Pro £49/mo. Cancel anytime."}
    if "hello" in msg or "hi" in msg:
        return {"reply": "Hi! I’m ZenithCordAI 🤖 — ask me about plans or features."}
    return {"reply": "ZenithCordAI captures leads & books calls 24/7. Ask about pricing or features!"}

@app.post("/create-checkout-session")
async def create_checkout_session(req: Request):
    if not stripe.api_key:
        return {"error": "Missing STRIPE_SECRET_KEY"}

    data = await req.json()
    plan = (data or {}).get("plan", "starter")
    price_id = {"free": PRICE_FREE, "starter": PRICE_STARTER, "pro": PRICE_PRO}.get(plan, "")

    try:
        if price_id:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=FRONTEND_URL + "/pricing?success=true",
                cancel_url=FRONTEND_URL + "/pricing?canceled=true",
            )
        else:
            # fallback one-time checkout if you haven't created Stripe Price IDs yet
            amount = 0
            if plan == "starter":
                amount = 2500  # £25.00
            elif plan == "pro":
                amount = 4900  # £49.00
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "gbp",
                        "product_data": {"name": f"ZenithCordAI {plan.capitalize()}"},
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }],
                success_url=FRONTEND_URL + "/pricing?success=true",
                cancel_url=FRONTEND_URL + "/pricing?canceled=true",
            )
        return {"url": session.url}
    except Exception as e:
        return {"error": str(e)}

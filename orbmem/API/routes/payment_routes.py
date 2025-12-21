# orbmem/API/routes/payment_routes.py

import razorpay
from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from orbmem.core.config import load_config
from orbmem.db.api_keys import create_api_key
from orbmem.db.postgres import SessionLocal
from orbmem.utils.exceptions import DatabaseError
from orbmem.core.auth import _verify_firebase_token  # ✅ REAL verification

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

cfg = load_config()

if not cfg.razorpay:
    raise RuntimeError("Razorpay is not configured")

razorpay_client = razorpay.Client(
    auth=(cfg.razorpay.key_id, cfg.razorpay.key_secret)
)

router = APIRouter(
    prefix="/v1/payments",
    tags=["Payments"]
)

# --------------------------------------------------
# CREATE RAZORPAY ORDER
# --------------------------------------------------

@router.post("/create-order")
def create_order(
    payload: dict,
    x_firebase_token: str = Header(..., alias="X-Firebase-Token"),
):
    """
    Creates a Razorpay order.
    Firebase-authenticated user only.
    """

    user = _verify_firebase_token(x_firebase_token)
    uid = user["uid"]

    plan = payload.get("plan", "monthly")

    amount_map = {
        "monthly": 49900,  # ₹499
        "yearly": 499900,  # ₹4999
    }

    if plan not in amount_map:
        raise HTTPException(status_code=400, detail="Invalid plan")

    try:
        order = razorpay_client.order.create({
            "amount": amount_map[plan],
            "currency": "INR",
            "receipt": f"orbmem_{uid}",
            "notes": {
                "uid": uid,
                "plan": plan,
            }
        })

        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "razorpay_key": cfg.razorpay.key_id,  # ✅ frontend expects this
        }

    except Exception as e:
        print("Razorpay order error:", e)
        raise HTTPException(status_code=500, detail="Failed to create order")


# --------------------------------------------------
# VERIFY PAYMENT + ISSUE API KEY
# --------------------------------------------------

@router.post("/verify")
def verify_payment(
    payload: dict,
    x_firebase_token: str = Header(..., alias="X-Firebase-Token"),
):
    """
    Verifies Razorpay payment and issues API key.
    """

    user = _verify_firebase_token(x_firebase_token)
    uid = user["uid"]

    payment_id = payload.get("razorpay_payment_id")
    order_id = payload.get("razorpay_order_id")
    signature = payload.get("razorpay_signature")

    if not payment_id or not order_id or not signature:
        raise HTTPException(status_code=400, detail="Missing payment fields")

    # -----------------------------
    # VERIFY RAZORPAY SIGNATURE
    # -----------------------------
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature,
        })
    except Exception as e:
        print("Signature verification failed:", e)
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    db = SessionLocal()

    try:
        # -----------------------------
        # DISABLE OLD API KEYS
        # -----------------------------
        db.execute(
            text("UPDATE api_keys SET is_active = FALSE WHERE user_id = :uid"),
            {"uid": uid}
        )
        db.commit()

        # -----------------------------
        # CREATE NEW API KEY
        # -----------------------------
        raw_key = create_api_key(
            user_id=uid,
            plan="paid",
            is_unlimited=True
        )

        return {
            "api_key": raw_key,
            "message": "Payment successful. API key generated.",
        }

    except Exception as e:
        db.rollback()
        print("DB error:", e)
        raise DatabaseError("Failed to finalize payment")

    finally:
        db.close()
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
    Verify Razorpay payment (idempotent, atomic).
    Safe for frontend; webhook may also process same payment.
    """

    # --------------------------------------------------
    # AUTH
    # --------------------------------------------------
    user = _verify_firebase_token(x_firebase_token)
    uid = user["uid"]

    payment_id = payload.get("razorpay_payment_id")
    order_id = payload.get("razorpay_order_id")
    signature = payload.get("razorpay_signature")

    if not payment_id or not order_id or not signature:
        raise HTTPException(status_code=400, detail="Missing payment fields")

    # --------------------------------------------------
    # VERIFY SIGNATURE
    # --------------------------------------------------
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": order_id,
            "razorpay_signature": signature,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # --------------------------------------------------
    # FETCH ORDER (DO NOT TRUST CLIENT)
    # --------------------------------------------------
    try:
        order = razorpay_client.order.fetch(order_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Order fetch failed")

    notes = order.get("notes", {})

    if notes.get("uid") != uid:
        raise HTTPException(status_code=403, detail="Order/User mismatch")

    # 🔒 Normalize plan to avoid case issues
    plan = notes.get("plan", "paid").lower()

    # --------------------------------------------------
    # ATOMIC DATABASE TRANSACTION
    # --------------------------------------------------
    db = SessionLocal()
    try:
        # 1️⃣ IDEMPOTENCY CHECK
        already_processed = db.execute(
            text("""
                SELECT 1
                FROM payments
                WHERE razorpay_payment_id = :pid
                LIMIT 1
            """),
            {"pid": payment_id}
        ).fetchone()

        if already_processed:
            return {
                "status": "ok",
                "message": "Payment already processed"
            }

        # 2️⃣ RECORD PAYMENT (LOCKS PAYMENT ID)
        db.execute(
            text("""
                INSERT INTO payments (
                    user_id,
                    razorpay_payment_id,
                    order_id,
                    amount,
                    plan
                )
                VALUES (:uid, :pid, :oid, :amt, :plan)
            """),
            {
                "uid": uid,
                "pid": payment_id,
                "oid": order_id,
                "amt": order["amount"],
                "plan": plan,
            }
        )

        # 3️⃣ REVOKE OLD KEYS
        db.execute(
            text("""
                UPDATE api_keys
                SET is_active = FALSE
                WHERE user_id = :uid
            """),
            {"uid": uid}
        )

        # 4️⃣ CREATE NEW API KEY (INLINE, SAME SESSION)
        from orbmem.db.api_keys import generate_api_key

        raw_key, key_hash = generate_api_key()

        db.execute(
            text("""
                INSERT INTO api_keys (
                    user_id,
                    api_key_hash,
                    is_active,
                    is_unlimited,
                    expires_at,
                    plan
                )
                VALUES (
                    :uid,
                    :hash,
                    TRUE,
                    TRUE,
                    NULL,
                    :plan
                )
            """),
            {
                "uid": uid,
                "hash": key_hash,
                "plan": plan,
            }
        )

        # 🧾 PRODUCTION LOG (CRITICAL)
        from orbmem.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info(
            "Payment verified and API key issued",
            extra={
                "uid": uid,
                "payment_id": payment_id,
                "order_id": order_id,
                "plan": plan,
            }
        )

        # ✅ SINGLE COMMIT (NO GHOST KEYS)
        db.commit()

        return {
            "api_key": raw_key,
            "message": "Payment verified. API key issued."
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Payment finalization failed"
        )

    finally:
        db.close()
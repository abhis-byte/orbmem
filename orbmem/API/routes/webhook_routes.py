import hmac
import hashlib
import json
from typing import Optional

from fastapi import APIRouter, Request, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from orbmem.core.config import load_config
from orbmem.db.postgres import SessionLocal
from orbmem.db.api_keys import create_api_key
from orbmem.utils.logger import get_logger

logger = get_logger(__name__)
cfg = load_config()

router = APIRouter(
    prefix="/v1/webhooks",
    tags=["Webhooks"]
)

# --------------------------------------------------
# SIGNATURE VERIFICATION
# --------------------------------------------------

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# --------------------------------------------------
# RAZORPAY WEBHOOK
# --------------------------------------------------

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: Optional[str] = Header(None, alias="X-Razorpay-Event-Id"),
):
    if not x_razorpay_signature:
        logger.warning("Webhook rejected: missing signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature",
        )

    raw_body = await request.body()

    # 1️⃣ Verify Webhook Signature
    if not verify_signature(
        raw_body,
        x_razorpay_signature,
        cfg.razorpay.webhook_secret,
    ):
        logger.warning(
            "Invalid Razorpay webhook signature",
            extra={"event_id": x_razorpay_event_id},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # 2️⃣ Parse Payload
    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error("Webhook payload is not valid JSON")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = data.get("event")

    # 3️⃣ Allow-list supported events
    if event_type not in ("payment.captured", "order.paid"):
        logger.info(
            "Webhook event ignored",
            extra={"event": event_type, "event_id": x_razorpay_event_id},
        )
        return {"status": "ignored"}

    # 4️⃣ Extract Payment Entity Safely
    payment = (
        data.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    payment_id = payment.get("id")
    order_id = payment.get("order_id")
    amount = payment.get("amount")
    notes = payment.get("notes", {})

    uid = notes.get("uid")
    plan = notes.get("plan", "paid")

    if not payment_id or not uid:
        logger.error(
            "Webhook missing required metadata",
            extra={"event_id": x_razorpay_event_id},
        )
        return {"status": "error", "message": "Missing payment metadata"}

    db = SessionLocal()

    try:
        # 5️⃣ Idempotency Check
        already_processed = db.execute(
            text(
                "SELECT 1 FROM payments WHERE razorpay_payment_id = :pid LIMIT 1"
            ),
            {"pid": payment_id},
        ).fetchone()

        if already_processed:
            logger.info(
                "Duplicate webhook ignored",
                extra={"payment_id": payment_id, "uid": uid},
            )
            return {"status": "already_processed"}

        # 6️⃣ Atomic Transaction
        db.execute(
            text("""
                INSERT INTO payments (
                    user_id,
                    razorpay_payment_id,
                    order_id,
                    amount,
                    plan
                )
                VALUES (
                    :uid,
                    :pid,
                    :oid,
                    :amount,
                    :plan
                )
            """),
            {
                "uid": uid,
                "pid": payment_id,
                "oid": order_id,
                "amount": amount,
                "plan": plan,
            },
        )

        db.execute(
            text(
                "UPDATE api_keys SET is_active = FALSE WHERE user_id = :uid"
            ),
            {"uid": uid},
        )

        create_api_key(
            user_id=uid,
            plan=plan,
            is_unlimited=True,
        )

        db.commit()

        logger.info(
            "Webhook processed successfully",
            extra={
                "payment_id": payment_id,
                "uid": uid,
                "event": event_type,
            },
        )

        return {"status": "success"}

    except IntegrityError:
        db.rollback()
        logger.info(
            "Duplicate payment prevented by DB constraint",
            extra={"payment_id": payment_id},
        )
        return {"status": "already_processed"}

    except Exception as e:
        db.rollback()
        logger.error(
            "Webhook processing failed",
            extra={
                "payment_id": payment_id,
                "uid": uid,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal processing error",
        )

    finally:
        db.close()
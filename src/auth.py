from __future__ import annotations

import random
import time


OTP_TTL_SECONDS = 300
MAX_OTP_ATTEMPTS = 3


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def create_otp_state(email: str, customer_id: str) -> dict:
    return {
        "email": email,
        "customer_id": customer_id,
        "otp": generate_otp(),
        "created_at": time.time(),
        "attempts": 0,
    }


def verify_otp(otp_state: dict | None, submitted_otp: str) -> tuple[bool, str]:
    if not otp_state:
        return False, "No OTP session found. Please request a new OTP."

    if time.time() - otp_state["created_at"] > OTP_TTL_SECONDS:
        return False, "OTP expired. Please request a new OTP."

    if otp_state["attempts"] >= MAX_OTP_ATTEMPTS:
        return False, "Maximum OTP attempts exceeded. Please request a new OTP."

    otp_state["attempts"] += 1
    if submitted_otp.strip() == otp_state["otp"]:
        return True, "Authentication successful."

    remaining = MAX_OTP_ATTEMPTS - otp_state["attempts"]
    return False, f"Invalid OTP. Attempts remaining: {remaining}."

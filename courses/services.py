import os
from decimal import Decimal, InvalidOperation

import requests


def paypal_base_url() -> str:
    mode = os.environ.get("PAYPAL_MODE", "sandbox").lower()
    return "https://api-m.paypal.com" if mode == "live" else "https://api-m.sandbox.paypal.com"


def paypal_access_token() -> str:
    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    secret = os.environ.get("PAYPAL_SECRET")

    if not client_id or not secret:
        raise RuntimeError("PayPal credentials are missing.")

    response = requests.post(
        f"{paypal_base_url()}/v1/oauth2/token",
        auth=(client_id, secret),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    response.raise_for_status()

    return response.json()["access_token"]


def verify_and_capture_paypal_order(order_id: str, expected_amount: Decimal) -> str:
    token = paypal_access_token()

    response = requests.post(
        f"{paypal_base_url()}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    status = data.get("status")

    if status not in {"COMPLETED", "APPROVED"}:
        raise ValueError(f"PayPal capture status not acceptable: {status}")

    capture_id = None
    captured_amount = None

    purchase_units = data.get("purchase_units") or []
    if purchase_units:
        payments = purchase_units[0].get("payments") or {}
        captures = payments.get("captures") or []

        if captures:
            capture_id = captures[0].get("id")
            amount = captures[0].get("amount") or {}

            try:
                captured_amount = Decimal(str(amount.get("value")))
            except (InvalidOperation, TypeError):
                captured_amount = None

    if captured_amount is not None and captured_amount != expected_amount:
        raise ValueError(
            f"Amount mismatch. expected={expected_amount} got={captured_amount}"
        )

    return capture_id or order_id
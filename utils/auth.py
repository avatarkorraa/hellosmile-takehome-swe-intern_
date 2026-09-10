"""Fake, dependency-free auth tokens for this exercise.

This is NOT a real JWT implementation and should never be used outside of
this take-home. It exists so the rest of the codebase can create and (once
you implement it) verify tokens without pulling in an external auth library
(no python-jose, no authlib, no Auth0 SDK, ...).

A token looks like:

    <base64url-json-payload>.<hex-hmac-signature>

The payload is a small JSON object with the claims `sub`, `role`
("staff" or "patient"), and optionally `patient_id`.

Everything below is already implemented and ready to use. There is
intentionally no `verify_test_token` / `decode_test_token` function here —
writing that (correctly, using only what's already imported below) is part
of Task 1.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Optional

# Test-only signing key. In a real deployment this would come from a secrets
# manager and would never be committed to source control.
SECRET_KEY = b"hellosmile-take-home-test-secret"


def _sign(payload_b64: bytes) -> str:
    return hmac.new(SECRET_KEY, payload_b64, hashlib.sha256).hexdigest()

def create_test_token(sub: str, role: str, patient_id: Optional[str] = None) -> str:
    """Create a fake auth token with claims {sub, role[, patient_id]}."""
    if role not in ("staff", "patient"):
        raise ValueError("role must be 'staff' or 'patient'")

    claims: dict[str, str] = {"sub": sub, "role": role}
    if patient_id is not None:
        claims["patient_id"] = patient_id

    payload_b64 = base64.urlsafe_b64encode(json.dumps(claims).encode())
    signature = _sign(payload_b64)
    return f"{payload_b64.decode()}.{signature}"


def verify_test_token(token: str) -> dict[str, str]:
    try:
        payload_b64, signature = token.split(".", 1)

        expected_signature = _sign(payload_b64.encode())

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("invalid signature")

        payload = base64.urlsafe_b64decode(payload_b64)
        claims = json.loads(payload)

        if claims.get("role") not in ("staff", "patient"):
            raise ValueError("invalid role")

        return claims

    except Exception as exc:
        raise ValueError("invalid token") from exc

if __name__ == "__main__":
    # Handy for minting tokens to poke the API manually, e.g.:
    #   python -m utils.auth
    print("staff token:  ", create_test_token("staff-1", "staff"))
    print("patient token:", create_test_token("patient-1", "patient", patient_id="4821"))

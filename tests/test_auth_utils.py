"""Minimal example test. Add your own for Task 1 / Task 4."""

import base64
import json

import pytest

from utils.auth import create_test_token


def test_create_test_token_shape():
    token = create_test_token("staff-1", "staff")
    payload_b64, signature = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))

    assert claims == {"sub": "staff-1", "role": "staff"}
    assert len(signature) == 64  # hex-encoded sha256 digest


def test_create_test_token_with_patient_id():
    token = create_test_token("patient-1", "patient", patient_id="4821")
    payload_b64, _ = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))

    assert claims["role"] == "patient"
    assert claims["patient_id"] == "4821"


def test_create_test_token_rejects_invalid_role():
    with pytest.raises(ValueError):
        create_test_token("x", "admin")

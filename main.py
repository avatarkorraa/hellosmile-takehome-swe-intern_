"""HelloSmile take-home starter API.

Runs as-is with `uvicorn main:app --reload`, but `/token` and
`/rooms/active` below are not protected yet — that's Task 1. `PATCH
/context` isn't protected either, same deal.
"""

from __future__ import annotations

from utils.auth import verify_test_token

from fastapi import FastAPI, Header
from pydantic import BaseModel

from bonus import router as bonus_router
from models.context import Context
from utils.livekit_tokens import generate_livekit_token
from fastapi import Depends, HTTPException

app = FastAPI(title="HelloSmile Take-Home API")
app.include_router(bonus_router, prefix="/bonus")

# In-memory mock of "currently active" LiveKit rooms. No database, no cache.
ACTIVE_ROOMS: list[dict[str, str]] = [
    {"room": "dentist-office-1", "participants": "2"},
    {"room": "patient-4821", "participants": "1"},
]

# In-memory clinic context, fetched by the LiveKit agent (Task 2) and
# injected into its instructions.
CONTEXT = Context(
    opening_hours={"mon_fri": "9:00-19:00", "sat": "9:00-13:00", "sun": "closed"},
    location="Via Roma 12, Milano",
    offered_services=["igiene dentale", "otturazioni", "ortodonzia", "implantologia"],
    contact_info={"phone": "+39 02 1234567", "email": "info@hellosmile.it"},
)

# In-memory log of completed calls, reported by the LiveKit agent (Task 2).
CALLS: list[dict[str, object]] = []


class TokenRequest(BaseModel):
    room: str
    identity: str


class CallReport(BaseModel):
    room: str
    transcript: str
    duration_seconds: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def get_current_user(authorization: str | None = Header(default=None),) -> dict[str, str]:

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized",)

    token = authorization[len("Bearer "):]

    try:
        return verify_test_token(token)
    except ValueError:
        raise HTTPException(status_code=401,detail="Unauthorized",)

@app.post("/token")
def issue_token(payload: TokenRequest, user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
    """Issue a real LiveKit token for `payload.room` / `payload.identity`.

    TODO(candidate): there is no auth check here at all right now — anyone
    can request a token for any room and any identity. See Task 1 in the
    README.
    """

    # I pazienti possono accedere solo alla propria stanza
    if user["role"] == "patient":
        patient_id = user.get("patient_id")

        if payload.room != f"patient-{patient_id}":
            raise HTTPException(status_code=403, detail="Forbidden")

    token = generate_livekit_token(room=payload.room, identity=payload.identity)
    return {"room": payload.room, "identity": payload.identity, "token": token}


@app.get("/rooms/active")
def rooms_active() -> list[dict[str, str]]:
    """List active rooms.

    TODO(candidate): this is public right now. See Task 1 in the README.
    """
    return ACTIVE_ROOMS


@app.get("/context")
def get_context() -> Context:
    return CONTEXT


@app.patch("/context")
def update_context(patch: dict) -> Context:
    """Update the clinic context (opening hours, services, ...).

    TODO(candidate): only staff should be able to call this. See Task 1.
    """
    global CONTEXT
    CONTEXT = CONTEXT.model_copy(update=patch)
    return CONTEXT


@app.post("/calls")
def register_call(call: CallReport) -> dict[str, object]:
    """Register a completed call (sent by the LiveKit agent, Task 2)."""
    record = call.model_dump()
    record["id"] = len(CALLS) + 1
    CALLS.append(record)
    return record

@app.get("/calls")
def list_calls() -> list[dict[str, object]]:
    return CALLS

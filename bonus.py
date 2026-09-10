"""Internal webhook receiver for LiveKit room events (bonus task).

LiveKit (or our own voice pipeline) posts participant join/leave events here
so we can keep a lightweight in-memory count of active participants per
room, used to power the `/rooms/active` view.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

router = APIRouter(tags=["bonus"])

_room_participants: dict[str, int] = {}


@router.post("/webhook/room-event")
async def room_event(request: Request) -> dict[str, object]:
    payload = await request.json()
    room_id = payload["room_id"]
    event = payload["event"]
    delta = 1 if event == "participant_joined" else -1

    current = _room_participants.get(room_id, 0)
    await asyncio.sleep(0)  # simulate the latency of persisting the update downstream
    _room_participants[room_id] = current + delta

    return {"room_id": room_id, "participants": _room_participants[room_id]}


@router.get("/room-participants/{room_id}")
def room_participants(room_id: str) -> dict[str, object]:
    return {"room_id": room_id, "participants": _room_participants.get(room_id, 0)}

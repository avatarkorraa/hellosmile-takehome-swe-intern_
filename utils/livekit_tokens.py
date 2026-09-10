"""Real LiveKit access token minting (via the `livekit-api` server SDK).

This talks to no external service: an access token is a JWT signed locally
with your LiveKit API key/secret, so this works even before you have a
LiveKit Cloud project wired up in `.env` — you only need real credentials
once you actually try to *connect* to a room (Task 2).
"""

from __future__ import annotations

from livekit import api

from config import settings


def generate_livekit_token(room: str, identity: str) -> str:
    """Return a real, signed LiveKit access token scoped to `room` for `identity`."""
    grants = api.VideoGrants(room_join=True, room=room)
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(grants)
    )
    return token.to_jwt()

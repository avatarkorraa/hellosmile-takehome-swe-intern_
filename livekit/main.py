import asyncio
import json
import time

import httpx

from config import settings
from livekit import agents
from livekit.agents import Agent, AgentSession, inference, room_io
from livekit.plugins import noise_cancellation, silero


class Assistant(Agent):
    def __init__(self, clinic_context: str) -> None:
        super().__init__(
            instructions=f"""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.

            You are the assistant of a dental clinic called HelloSmile. You answer questions about the knowledge provided in the context.
            Here is the context you can use to answer questions:

            {clinic_context}
            """,
        )

    async def on_enter(self):
        self.session.say(
            "Ciao, sono l'assistente virtuale di HelloSmile! Come posso aiutarti oggi?",
            allow_interruptions=False,
        )


async def entrypoint(ctx: agents.JobContext):
    # Fetch the current clinic context from the API.
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.API_BASE_URL}/context"
        )
        response.raise_for_status()

        clinic_context = json.dumps(
            response.json(),
            ensure_ascii=False,
            indent=2,
        )

    session = AgentSession(
        stt="deepgram/nova-2:it",
        llm="google/gemini-2.5-flash",
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="d609f27f-f1a4-410f-85bb-10037b4fba99",
            language="it",
        ),
        vad=silero.VAD.load(),
    )

    start_time = time.monotonic()

    # Wait until the session closes.
    session_closed = asyncio.Event()

    @session.on("close")
    def on_close(event):
        session_closed.set()

    await session.start(
        room=ctx.room,
        agent=Assistant(clinic_context),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    await session_closed.wait()

    duration = time.monotonic() - start_time

    # Report the completed call to the API.
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.API_BASE_URL}/calls",
            json={
                "transcript": session.history,
                "duration": duration,
            },
        )
        response.raise_for_status()


if __name__ == "__main__":
    if not all([
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
        settings.LIVEKIT_URL,
    ]):
        raise ValueError(
            "LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_URL "
            "must be set in the environment variables."
        )

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )
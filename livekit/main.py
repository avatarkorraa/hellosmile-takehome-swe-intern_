import asyncio
import json
import time

import httpx

from config import settings
from livekit import agents
from livekit.agents import Agent, AgentSession, inference, room_io
from livekit.plugins import noise_cancellation, silero


class Assistant(Agent):
    class Assistant(Agent):
        def __init__(self, clinic_context: str) -> None:
            # Il tono è pensato per una conversazione telefonica: naturale, cordiale e diretto.
            # Le risposte sono brevi per evitare lunghi monologhi difficili da seguire a voce.
            # L'assistente si limita alle attività della clinica e indirizza altrove le richieste fuori scope.
            # In caso di emergenza evita diagnosi o consigli medici e fornisce il contatto dello studio.
            super().__init__(
                instructions=f"""
    You are the voice assistant of HelloSmile, a dental clinic.

    This is a phone conversation, not a chat. Speak naturally, warmly, and professionally.
    Keep your answers short and easy to follow when spoken aloud. Avoid long explanations,
    lists, unnecessary details, emojis, markdown, or complex formatting.

    Your main purpose is to help patients with:
    - booking an appointment;
    - rescheduling an appointment;
    - cancelling an appointment.

    If the user asks about something outside these activities, politely explain that you can
    only help with appointments and direct them to contact the clinic using the contact
    information available in the clinic context.

    If the user reports an acute dental emergency, such as severe pain, trauma, or bleeding,
    do not diagnose the condition and do not provide medical advice or treatment instructions.
    Instead, calmly advise the user to contact HelloSmile directly using the clinic's contact
    information from the context.

    Use only the information provided in the clinic context for HelloSmile-specific information.
    Do not invent opening hours, services, contact details, or other clinic information.

    Clinic context:
    {clinic_context}
    """,)

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
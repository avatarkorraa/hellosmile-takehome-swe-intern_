from config import settings
from livekit import agents
from livekit.agents import Agent, AgentSession, inference, room_io
from livekit.plugins import noise_cancellation, silero


class Assistant(Agent):
    def __init__(self) -> None:
        # TODO(candidate, Task 3): this prompt is deliberately mediocre —
        # generic tone, no length constraint, nothing about what's in/out
        # of scope, nothing about dental emergencies. Rewrite it for
        # HelloSmile. You'll likely also want to use the clinic context
        # fetched below (opening hours, services, contact info) instead of
        # hardcoding anything here.
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.

            You are the assistant of a dental clinic called HelloSmile. You answer questions about the knowledge provided in the context.
            Here is the context you can use to answer questions:
            """,
        )

    async def on_enter(self):
        self.session.say(
            "Ciao, sono l'assistente virtuale di HelloSmile! Come posso aiutarti oggi?",
            allow_interruptions=False,
        )


async def entrypoint(ctx: agents.JobContext):
    # TODO(candidate, Task 2): fetch the current clinic context from the API
    # service (GET {settings.API_BASE_URL}/context) and inject it into
    # Assistant's instructions before starting the session, so the agent
    # answers using the *current* opening hours / services / contact info
    # rather than whatever was hardcoded above.

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

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    # TODO(candidate, Task 2): when the session ends, POST the call details
    # (transcript, duration) to {settings.API_BASE_URL}/calls so it shows
    # up for staff. `session.history` has the conversation transcript.
    #
    # Note: `session.start()` returns as soon as the session begins, not
    # when it ends — you'll need to wait for the actual close before
    # reading transcript/duration (see `AgentSession`'s "close" event).


if __name__ == "__main__":
    if not all([settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET, settings.LIVEKIT_URL]):
        raise ValueError(
            "LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_URL must be set in the environment variables."
        )

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
        )
    )

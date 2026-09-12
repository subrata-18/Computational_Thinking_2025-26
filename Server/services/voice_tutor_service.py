import os
import asyncio
import queue
import threading
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("API_KEY1"))

VOICE_SYSTEM_PROMPT = """
You are a friendly, patient AI Computational Thinking Tutor. 
Speak naturally and conversationally. Guide the student through the problems. Keep the conversation in English
"""

def run_voice_session(ws):
    gemini_to_client_queue = queue.Queue()
    session_handle = None

    # 1. Dedicated Sender Thread (Stays alive across all reconnects)
    def ws_sender():
        while True:
            try:
                data = gemini_to_client_queue.get()
                if data is None:
                    break
                ws.send(data)
            except Exception:
                break

    sender_thread = threading.Thread(target=ws_sender, daemon=True)
    sender_thread.start()

    async def _async_voice_session():
        nonlocal session_handle
        loop = asyncio.get_running_loop()
        client_to_gemini_queue = asyncio.Queue()

        # 2. Dedicated Receiver Thread
        def ws_receiver():
            while True:
                try:
                    data = ws.receive()
                    if data is None:
                        break

                    if isinstance(data, bytes) and len(data) > 0:
                        try:
                            if not loop.is_closed():
                                loop.call_soon_threadsafe(client_to_gemini_queue.put_nowait, data)
                        except RuntimeError:
                            break 
                    elif isinstance(data, str) and data == "END_OF_SPEECH":
                        try:
                            if not loop.is_closed():
                                loop.call_soon_threadsafe(client_to_gemini_queue.put_nowait, b"END_OF_SPEECH")
                        except RuntimeError:
                            break
                except Exception:
                    break
            
            try:
                if not loop.is_closed():
                    loop.call_soon_threadsafe(client_to_gemini_queue.put_nowait, None)
            except RuntimeError:
                pass 

        receiver_thread = threading.Thread(target=ws_receiver, daemon=True)
        receiver_thread.start()

        # 3. Resilient Auto-Reconnect Loop
        while True:
            try:
                config_kwargs = {
                    "response_modalities": ["AUDIO"],
                    "system_instruction": types.Content(parts=[types.Part.from_text(text=VOICE_SYSTEM_PROMPT)])
                }
                    
                if session_handle:
                    config_kwargs["session_resumption"] = types.SessionResumptionConfig(handle=session_handle)
                        
                config = types.LiveConnectConfig(**config_kwargs)

                async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-preview-12-2025", config=config) as session:
                    print(f"Connected to Gemini API. Resuming handle: {session_handle}")

                    async def send_to_gemini():
                        while True:
                            data = await client_to_gemini_queue.get()
                            if data is None:
                                return "CLIENT_DISCONNECTED"

                            if data == b"END_OF_SPEECH":
                                await session.send_realtime_input(audio_stream_end=True)
                            else:
                                await session.send_realtime_input(
                                    audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                                )
                            await asyncio.sleep(0.001)

                    async def receive_from_gemini():
                        nonlocal session_handle
                        async for message in session.receive():
                            
                            # Safely extract and save the resumption handle
                            if message.session_resumption_update:
                                if message.session_resumption_update.new_handle:
                                    session_handle = message.session_resumption_update.new_handle
                            
                            # Process audio normally
                            if message.server_content and message.server_content.model_turn:
                                for part in message.server_content.model_turn.parts:
                                    if part.inline_data:
                                        gemini_to_client_queue.put(part.inline_data.data)
                        return "GEMINI_DISCONNECTED"

                    # 4. Use wait() instead of gather() to prevent task leaking
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(send_to_gemini()), asyncio.create_task(receive_from_gemini())],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Kill whichever task got left behind
                    for p in pending:
                        p.cancel()
                        
                    # Break the infinite loop if the browser actually closed the connection
                    results = [d.result() for d in done if not d.exception()]
                    if "CLIENT_DISCONNECTED" in results:
                        print("Browser closed the connection.")
                        break

            except Exception as e:
                print(f"Gemini connection dropped ({e}). Auto-reconnecting...")
                await asyncio.sleep(0.5)
                continue

    try:
        asyncio.run(_async_voice_session())
    except Exception as e:
        print(f"Voice session ended cleanly: {e}")
    finally:
        # 5. Safely kill the browser sender thread ONLY when the entire session is permanently over
        gemini_to_client_queue.put(None)
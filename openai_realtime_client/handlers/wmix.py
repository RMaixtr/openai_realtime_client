import asyncio
import nats
from io import BytesIO

from ..client.realtime_client import RealtimeClient
from pydub import AudioSegment

class WmixHandler:
    def __init__(self):
        self.streaming = False

    async def start_streaming(self, client: RealtimeClient):

        if self.streaming:
            return
        
        self.streaming = True
        self.nc = await nats.connect(servers="nats://localhost:4222")
        self.mic = await self.nc.subscribe("x3.mic.16kpcm")
        
        while self.streaming:
            try:
                # Read raw PCM data
                msg = await self.mic.next_msg(None)
                audio = AudioSegment.from_raw(BytesIO(msg.data), frame_rate=16000, sample_width=16 // 8, channels=1)
                audio = audio.set_frame_rate(24000)
                # Stream directly without trying to decode
                await self.nc.publish("test.speaker.16kpcm", audio.raw_data)
                await client.stream_audio(audio.raw_data)
            except Exception as e:
                print(f"Error streaming: {e}")
                break
            # await asyncio.sleep(0.01)

    def stop_streaming(self):
        """Stop audio streaming."""
        self.streaming = False

    def play_audio(self, audio_data: bytes):
        """Add audio data to the buffer"""
        audio = AudioSegment.from_raw(BytesIO(audio_data), frame_rate=24000, sample_width=16 // 8, channels=1)
        audio = audio.set_frame_rate(16000)
        asyncio.get_running_loop().create_task(self.nc.publish("x3.speaker.16kpcm", audio.raw_data))


    def stop_playback_immediately(self):
        if hasattr(self, "nc"):
            asyncio.get_running_loop().create_task(self.nc.publish("x3.kws.isWeakup", b"true"))

    def cleanup(self):
        """Clean up audio resources"""
        self.stop_playback_immediately()

        self.stop_playback = True

        self.recording = False
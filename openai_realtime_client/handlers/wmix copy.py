import asyncio
import nats
from io import BytesIO

from ..client.realtime_client import RealtimeClient
from pydub import AudioSegment

import numpy as np
from pedalboard import *

class WmixHandler:
    def __init__(self):
        self.streaming = False
        self.board = Pedalboard([
            # 压缩器：降低压缩的强度
            Compressor(threshold_db=-20, ratio=10),
            LadderFilter(mode=LadderFilter.Mode.LPF12, cutoff_hz=1000),
            HighpassFilter(cutoff_frequency_hz=100),
            Convolution("./woolf.wav", 1.0),
            PitchShift(semitones=+12),
            Gain(gain_db=30)
        ])
        self.board.append(Compressor(threshold_db=-25, ratio=10))
        self.board.append(Gain(gain_db=10))
        self.board.append(Limiter())
        self.board[0].threshold_db = -60

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

        audio = np.frombuffer(audio.raw_data, dtype=np.int16).astype(np.float32) / 32768.0  # 归一化
        audio = np.reshape(audio, (1, -1))  # 转换为形状 (channels, samples)
        effected = self.board(audio, 16000)
        effected = (np.clip(effected, -1.0, 1.0) * 32767.0).astype(np.int16).flatten()

        asyncio.get_running_loop().create_task(self.nc.publish("x3.speaker.16kpcm", effected.tobytes()))


    def stop_playback_immediately(self):
        if hasattr(self, "nc"):
            asyncio.get_running_loop().create_task(self.nc.publish("x3.kws.isWeakup", b"true"))

    def cleanup(self):
        """Clean up audio resources"""
        self.stop_playback_immediately()

        self.stop_playback = True

        self.recording = False
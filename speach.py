# STT: Faster-Whisper
from faster_whisper import WhisperModel

model = WhisperModel("medium", device="cpu")
segments, info = model.transcribe("audio.wav", language="zh")
text = " ".join([segment.text for segment in segments])

# TTS: Edge-TTS
import edge_tts
import asyncio

async def speak(text):
    communicate = edge_tts.Communicate(text, "zh-TW-HsiaoChenNeural")
    await communicate.save("output.mp3")

asyncio.run(speak("你好"))
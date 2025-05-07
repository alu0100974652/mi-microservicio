# -*- coding: utf-8 -*-
import io
import re
import asyncio
import tempfile

from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

import soundfile as sf
from TTS.api import TTS
from num2words import num2words
from faster_whisper import WhisperModel

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TTS
tts = TTS(model_name="tts_models/es/css10/vits", progress_bar=False, gpu=False)
NUM_REGEX = re.compile(r'\b\d+\b')

def normalizar_numeros(texto: str) -> str:
    def reemplazar(match):
        numero = int(match.group(0))
        return num2words(numero, lang='es')
    return NUM_REGEX.sub(reemplazar, texto)

@app.post("/generate-audio")
async def generate_audio(request: Request):
    data = await request.json()
    text = data.get("text", "")
    text = normalizar_numeros(text)
    if not text:
        return JSONResponse(content={"error": "No se recibi� texto v�lido"}, status_code=400)
    loop = asyncio.get_running_loop()
    wav = await loop.run_in_executor(None, tts.tts, text)
    sample_rate = tts.synthesizer.output_sample_rate
    buffer = io.BytesIO()
    sf.write(buffer, wav, samplerate=sample_rate, format='WAV')
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/wav")

# STT
model = WhisperModel("small", device="cpu", compute_type="float32")

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".webm") as tmp:
            contents = await audio.read()
            tmp.write(contents)
            tmp.flush()
            loop = asyncio.get_running_loop()
            segments, info = await loop.run_in_executor(None, model.transcribe, tmp.name)
            texto = "".join(segment.text for segment in segments)
            return {"text": texto.strip(), "language": info.language}
    except Exception as e:
        return {"error": str(e)}
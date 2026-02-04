"""Transcription audio avec faster-whisper (chargement au demarrage)"""
from src.config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE
import numpy as np
import threading


class Transcriber:
    def __init__(self):
        self.model = None
        self._ready = threading.Event()
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self):
        from faster_whisper import WhisperModel
        print(f"[Whisper] Chargement du modele '{WHISPER_MODEL}'...")
        self.model = WhisperModel(
            WHISPER_MODEL,
            device=DEVICE,
            compute_type=COMPUTE_TYPE
        )
        print("[Whisper] Modele charge")
        self._ready.set()

    def is_ready(self) -> bool:
        """Retourne True si le modele est charge"""
        return self._ready.is_set()

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcrit l'audio en texte"""
        if audio_data is None or len(audio_data) == 0:
            return ""

        if not self._ready.is_set():
            print("[Whisper] En attente du chargement du modele...")
        self._ready.wait()

        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        segments, info = self.model.transcribe(
            audio_data,
            language=LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
            }
        )

        text = " ".join([segment.text for segment in segments])
        return text.strip()

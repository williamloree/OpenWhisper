"""Transcription audio avec faster-whisper (lazy loading + auto-unload)"""
from src.config import WHISPER_MODEL, LANGUAGE, DEVICE, COMPUTE_TYPE, MODEL_UNLOAD_DELAY
import numpy as np
import threading
import time


class Transcriber:
    def __init__(self):
        self.model = None
        self.last_used = 0
        self._unload_timer = None
        self._lock = threading.Lock()

    def _load_model(self):
        """Charge le modele Whisper"""
        if self.model is None:
            from faster_whisper import WhisperModel
            print(f"Chargement du modele Whisper '{WHISPER_MODEL}'...")
            self.model = WhisperModel(
                WHISPER_MODEL,
                device=DEVICE,
                compute_type=COMPUTE_TYPE
            )
            print("Modele charge")

    def _unload_model(self):
        """Decharge le modele de la RAM"""
        with self._lock:
            if self.model is not None and time.time() - self.last_used >= MODEL_UNLOAD_DELAY:
                self.model = None
                self._unload_timer = None
                print("Modele decharge (inactivite)")

    def _schedule_unload(self):
        """Programme le dechargement du modele"""
        if self._unload_timer is not None:
            self._unload_timer.cancel()
        self._unload_timer = threading.Timer(MODEL_UNLOAD_DELAY, self._unload_model)
        self._unload_timer.daemon = True
        self._unload_timer.start()

    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcrit l'audio en texte"""
        if audio_data is None or len(audio_data) == 0:
            return ""

        with self._lock:
            self._load_model()
            self.last_used = time.time()

        # faster-whisper attend un array numpy float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Transcription
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

        # Recuperation du texte
        text = " ".join([segment.text for segment in segments])

        # Programmer le dechargement
        self._schedule_unload()

        return text.strip()

"""Gestion de l'enregistrement audio"""
import sounddevice as sd
import numpy as np
from src.config import SAMPLE_RATE, CHANNELS


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.stream = None
    
    def start(self):
        """Démarre l'enregistrement audio"""
        self.recording = True
        self.frames = []
        
        def callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            if self.recording:
                self.frames.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=callback,
            dtype='float32'
        )
        self.stream.start()
    
    def stop(self):
        """Arrête l'enregistrement et retourne l'audio"""
        self.recording = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self.frames:
            return None
        
        # Convertir en array numpy
        audio_data = np.concatenate(self.frames, axis=0)
        return audio_data.flatten()
    
    def is_recording(self):
        return self.recording

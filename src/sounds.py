"""Indicateurs sonores pour OpenWhisper"""
import winsound
import ctypes
import threading
import sys
import os


def _get_sound_path(filename):
    """Retourne le chemin du fichier son"""
    if getattr(sys, 'frozen', False):
        # Mode exe: fichier dans le dossier temporaire PyInstaller
        return os.path.join(sys._MEIPASS, filename)
    else:
        # Mode dev: fichier a la racine du projet
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


def _play_mp3(filepath):
    """Joue un fichier MP3 via Windows MCI"""
    winmm = ctypes.windll.winmm
    # Fermer toute instance precedente
    winmm.mciSendStringW('close mp3_sound', None, 0, 0)
    # Ouvrir et jouer le fichier
    winmm.mciSendStringW(f'open "{filepath}" type mpegvideo alias mp3_sound', None, 0, 0)
    winmm.mciSendStringW('play mp3_sound', None, 0, 0)


def play_start_recording():
    """Son de debut d'enregistrement"""
    def _play():
        path = _get_sound_path("open.wav")
        if os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play, daemon=True).start()


def play_start_transcription():
    """Son de debut de transcription"""
    def _play():
        path = _get_sound_path("open.wav")
        if os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    threading.Thread(target=_play, daemon=True).start()


def play_done():
    """Son de fin de transcription"""
    def _play():
        path = _get_sound_path("finish.mp3")
        if os.path.exists(path):
            _play_mp3(path)
    threading.Thread(target=_play, daemon=True).start()

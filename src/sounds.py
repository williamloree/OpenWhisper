"""Indicateurs sonores pour OpenWhisper (cross-platform)"""
import threading
import sys
import os
import platform


def _get_sound_path(filename):
    """Retourne le chemin du fichier son"""
    if getattr(sys, 'frozen', False):
        # Mode exe: fichier dans le dossier temporaire PyInstaller
        return os.path.join(sys._MEIPASS, filename)
    else:
        # Mode dev: fichier dans assets/
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", filename)


def _play_sound_windows(filepath):
    """Joue un fichier audio sur Windows"""
    import ctypes
    ext = os.path.splitext(filepath)[1].lower()

    if ext == '.wav':
        import winsound
        winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        # MP3 via Windows MCI
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW('close mp3_sound', None, 0, 0)
        winmm.mciSendStringW(f'open "{filepath}" type mpegvideo alias mp3_sound', None, 0, 0)
        winmm.mciSendStringW('play mp3_sound', None, 0, 0)


def _play_sound_unix(filepath):
    """Joue un fichier audio sur Linux/macOS"""
    try:
        import subprocess
        system = platform.system()

        if system == 'Darwin':  # macOS
            subprocess.Popen(['afplay', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:  # Linux
            # Essayer plusieurs lecteurs audio
            for player in ['paplay', 'aplay', 'ffplay']:
                try:
                    if player == 'ffplay':
                        subprocess.Popen([player, '-nodisp', '-autoexit', filepath],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.Popen([player, filepath],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
    except Exception:
        pass


def _play_sound(filepath):
    """Joue un fichier audio (cross-platform)"""
    if not os.path.exists(filepath):
        return

    if platform.system() == 'Windows':
        _play_sound_windows(filepath)
    else:
        _play_sound_unix(filepath)


def play_start_recording():
    """Son de debut d'enregistrement"""
    def _play():
        path = _get_sound_path("open.wav")
        _play_sound(path)
    threading.Thread(target=_play, daemon=True).start()


def play_start_transcription():
    """Son de debut de transcription"""
    def _play():
        path = _get_sound_path("open.wav")
        _play_sound(path)
    threading.Thread(target=_play, daemon=True).start()


def play_done():
    """Son de fin de transcription"""
    def _play():
        path = _get_sound_path("finish.mp3")
        _play_sound(path)
    threading.Thread(target=_play, daemon=True).start()

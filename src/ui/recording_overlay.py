"""Overlay d'enregistrement style dictaphone iPhone"""
import tkinter as tk
import platform
import time
import threading
import queue
import numpy as np
from typing import Optional, Tuple

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"


class RecordingOverlay:
    """Overlay flottant affiche pendant l'enregistrement (thread separe)"""

    # Couleurs style iOS Dark
    BG_COLOR = "#1C1C1E"
    TEXT_COLOR = "#FFFFFF"
    RED_COLOR = "#FFAA3A"
    GRAY_COLOR = "#48484A"
    WAVEFORM_COLOR = "#FFAA3A"

    # Dimensions (version mini)
    WIDTH = 70
    HEIGHT = 40
    CORNER_RADIUS = 10
    NUM_BARS = 6

    def __init__(self, saved_position: Optional[Tuple[int, int]] = None):
        self._position = saved_position
        self._is_visible = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._audio_queue = queue.Queue()
        self._final_position: Optional[Tuple[int, int]] = None

    def show(self):
        """Affiche l'overlay dans un thread separe"""
        if self._is_visible:
            return

        self._is_visible = True
        self._stop_event.clear()
        self._final_position = None

        # Vider la queue audio
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        self._thread = threading.Thread(target=self._run_overlay, daemon=True)
        self._thread.start()

    def hide(self) -> Optional[Tuple[int, int]]:
        """Cache l'overlay et retourne la position actuelle"""
        if not self._is_visible:
            return self._final_position

        self._stop_event.set()

        # Attendre que le thread se termine (il se nettoie lui-meme)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._is_visible = False
        return self._final_position

    def update_waveform(self, audio_samples: np.ndarray):
        """Met a jour les donnees de la waveform (thread-safe)"""
        if audio_samples is None or len(audio_samples) == 0:
            return

        try:
            # Limiter la taille de la queue
            if self._audio_queue.qsize() < 10:
                self._audio_queue.put_nowait(audio_samples.copy())
        except queue.Full:
            pass

    def _run_overlay(self):
        """Execute l'overlay dans son propre thread"""
        try:
            # Creer la fenetre
            root = tk.Tk()
            root.withdraw()

            window = tk.Toplevel(root)
            window.title("")
            window.overrideredirect(True)
            window.attributes("-topmost", True)

            # Forcer la mise a jour pour obtenir les dimensions ecran
            window.update_idletasks()

            # Position (centre-haut par defaut)
            if self._position:
                x, y = self._position
            else:
                screen_w = root.winfo_screenwidth()
                x = (screen_w - self.WIDTH) // 2
                y = 30

            window.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
            window.update_idletasks()

            # Transparence
            window.attributes("-alpha", 0.95)

            # Appliquer no-focus sur Windows
            if IS_WINDOWS:
                window.update_idletasks()
                self._apply_no_focus_windows(window)

            # Canvas principal
            canvas = tk.Canvas(
                window,
                width=self.WIDTH,
                height=self.HEIGHT,
                bg=self.BG_COLOR,
                highlightthickness=0
            )
            canvas.pack(fill="both", expand=True)

            # Dessiner le fond arrondi
            self._draw_rounded_rect(canvas, 0, 0, self.WIDTH, self.HEIGHT,
                                   self.CORNER_RADIUS, self.BG_COLOR, self.GRAY_COLOR)

            # Zone waveform (centree, pas de timer ni REC)
            waveform_y = 6
            waveform_height = self.HEIGHT - 12
            waveform_data = np.zeros(self.NUM_BARS)

            # Drag state
            drag_data = {"x": 0, "y": 0}

            def on_drag_start(event):
                drag_data["x"] = event.x
                drag_data["y"] = event.y

            def on_drag_motion(event):
                dx = event.x - drag_data["x"]
                dy = event.y - drag_data["y"]
                new_x = window.winfo_x() + dx
                new_y = window.winfo_y() + dy
                window.geometry(f"+{new_x}+{new_y}")

            canvas.bind("<Button-1>", on_drag_start)
            canvas.bind("<B1-Motion>", on_drag_motion)


            def draw_waveform():
                """Dessine la waveform (5 barres)"""
                canvas.delete("waveform")
                bar_count = len(waveform_data)
                padding = 8
                gap = 4
                total_gap = gap * (bar_count - 1)
                bar_width = (self.WIDTH - 2 * padding - total_gap) / bar_count
                center_y = waveform_y + waveform_height / 2
                max_h = waveform_height / 2

                for i, amp in enumerate(waveform_data):
                    bx = padding + i * (bar_width + gap)
                    # Limiter l'amplitude entre 0 et 1
                    normalized = min(amp, 1.0)
                    h = max(normalized * max_h, 2)
                    # Barres
                    canvas.create_rectangle(
                        bx, center_y - h,
                        bx + bar_width, center_y + h,
                        fill=self.WAVEFORM_COLOR,
                        outline="",
                        tags="waveform"
                    )

            def update():
                """Mise a jour periodique"""
                nonlocal waveform_data

                if self._stop_event.is_set():
                    # Sauvegarder la position avant de fermer
                    try:
                        self._final_position = (window.winfo_x(), window.winfo_y())
                    except Exception:
                        pass
                    # Fermer proprement depuis ce thread
                    try:
                        window.destroy()
                    except Exception:
                        pass
                    try:
                        root.quit()
                    except Exception:
                        pass
                    return

                # Traiter les donnees audio
                try:
                    while True:
                        samples = self._audio_queue.get_nowait()
                        samples = samples.flatten()
                        if len(samples) >= self.NUM_BARS:
                            chunk_size = len(samples) // self.NUM_BARS
                            new_bars = []
                            for i in range(self.NUM_BARS):
                                chunk = samples[i * chunk_size:(i + 1) * chunk_size]
                                # Peak amplitude pour plus de reactivite
                                amp = np.max(np.abs(chunk))
                                new_bars.append(amp)
                            # Amplification massive
                            new_bars = np.array(new_bars) * 150
                            # Remplacement direct pour max reactivite
                            waveform_data = new_bars
                except queue.Empty:
                    # Decroissance rapide pour effet pulse
                    waveform_data = waveform_data * 0.7

                draw_waveform()

                # Planifier la prochaine mise a jour (50ms = 20 fps)
                root.after(50, update)

            # Dessiner la waveform initiale
            draw_waveform()

            # Demarrer les mises a jour
            root.after(100, update)

            # Mainloop
            root.mainloop()

        except Exception as e:
            print(f"[Overlay] Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_visible = False
            # Nettoyer completement tkinter pour eviter les conflits
            try:
                import tkinter as _tk_cleanup
                _tk_cleanup._default_root = None
            except Exception:
                pass

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline):
        """Dessine un rectangle avec coins arrondis"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        canvas.create_polygon(points, fill=fill, outline=outline, smooth=True, width=1)

    def _apply_no_focus_windows(self, window):
        """Empeche la fenetre de prendre le focus (Windows)"""
        try:
            import ctypes

            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_TOPMOST = 0x00000008

            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            new_style = style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"[Overlay] No-focus error: {e}")

    @property
    def is_visible(self) -> bool:
        return self._is_visible

"""Fenetre de configuration avec design moderne"""
import customtkinter as ctk
from typing import Callable, Optional
import threading
import sys
import os
from PIL import Image


# Configuration du theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_asset_path(filename):
    """Retourne le chemin vers un asset"""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", filename)


def get_logo_path():
    """Retourne le chemin vers logo.png"""
    return get_asset_path(os.path.join("img", "logo.png"))


class SettingsWindow:
    """Fenetre de configuration des parametres OpenWhisper"""

    # Couleurs du theme
    BG_COLOR = "#1a1a2e"
    CARD_COLOR = "#16213e"
    ACCENT_COLOR = "#e94560"
    ACCENT_HOVER = "#ff6b6b"
    TEXT_COLOR = "#eaeaea"
    TEXT_MUTED = "#8b8b8b"

    # Options disponibles
    MODELS = ["tiny", "base", "small", "medium", "large-v3"]
    LANGUAGES = [
        ("Francais", "fr"),
        ("English", "en"),
        ("Deutsch", "de"),
        ("Espanol", "es"),
        ("Italiano", "it"),
        ("Portugues", "pt"),
        ("Nederlands", "nl"),
        ("Polski", "pl"),
        ("Русский", "ru"),
        ("中文", "zh"),
        ("日本語", "ja"),
        ("한국어", "ko"),
    ]
    DEVICES = ["cpu", "cuda", "auto"]
    COMPUTE_TYPES = ["int8", "float16", "int8_float16"]

    def __init__(self, settings, on_save_callback: Optional[Callable] = None):
        self.settings = settings
        self.on_save_callback = on_save_callback
        self._is_open = False
        self._thread = None

    def show(self):
        """Affiche la fenetre de settings dans un thread separe"""
        if self._is_open:
            return

        self._is_open = True
        self._thread = threading.Thread(target=self._run_window, daemon=True)
        self._thread.start()

    def _run_window(self):
        """Execute la fenetre dans son propre thread avec mainloop"""
        try:
            # Nettoyer toute instance tkinter/customtkinter precedente
            try:
                import tkinter as tk
                # Detruire les instances orphelines
                if tk._default_root:
                    try:
                        for widget in tk._default_root.winfo_children():
                            widget.destroy()
                        tk._default_root.destroy()
                    except Exception:
                        pass
                    tk._default_root = None
            except Exception:
                pass

            # Reset customtkinter internal state
            try:
                import customtkinter.windows.ctk_tk
                customtkinter.windows.ctk_tk.CTk._current_instance = None
            except Exception:
                pass

            # Attendre un peu pour que tkinter soit proprement nettoye
            import time
            time.sleep(0.1)

            # Creer la fenetre principale
            window = ctk.CTk()
            window.title("OpenWhisper - Parametres")
            window.geometry("500x620")
            window.resizable(False, False)
            window.configure(fg_color=self.BG_COLOR)

            # Charger et appliquer l'icone (logo.png)
            try:
                logo_path = get_logo_path()
                if os.path.exists(logo_path):
                    from PIL import ImageTk
                    icon_img = Image.open(logo_path)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    window.wm_iconphoto(True, icon_photo)
            except Exception as e:
                print(f"[Settings] Impossible de charger l'icone: {e}")

            # Centrer la fenetre
            window.update_idletasks()
            x = (window.winfo_screenwidth() - 500) // 2
            y = (window.winfo_screenheight() - 620) // 2
            window.geometry(f"500x620+{x}+{y}")

            # Variables pour les widgets
            model_var = ctk.StringVar(value=self.settings.whisper_model)

            # Trouver le nom de la langue
            current_code = self.settings.language
            current_name = current_code
            for name, code in self.LANGUAGES:
                if code == current_code:
                    current_name = name
                    break
            language_var = ctk.StringVar(value=current_name)

            device_var = ctk.StringVar(value=self.settings.device)
            compute_var = ctk.StringVar(value=self.settings.compute_type)
            hotkey_var = ctk.StringVar(value=self.settings.hotkey)

            # Header avec logo
            header_frame = ctk.CTkFrame(window, fg_color="transparent", height=80)
            header_frame.pack(fill="x", padx=30, pady=(25, 10))
            header_frame.pack_propagate(False)

            # Charger le logo pour le header
            try:
                logo_path = get_asset_path(os.path.join("img", "logo.png"))
                if os.path.exists(logo_path):
                    logo_img = Image.open(logo_path).resize((50, 50), Image.LANCZOS)
                    logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(50, 50))
                    logo_label = ctk.CTkLabel(header_frame, image=logo_ctk, text="")
                    logo_label.pack(side="left", padx=(0, 15))
            except Exception:
                pass

            # Titre et sous-titre
            title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            title_frame.pack(side="left", fill="y", expand=True)

            title_label = ctk.CTkLabel(
                title_frame,
                text="Parametres",
                font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
                text_color=self.TEXT_COLOR,
                anchor="w"
            )
            title_label.pack(anchor="w")

            subtitle_label = ctk.CTkLabel(
                title_frame,
                text="Configurez votre experience OpenWhisper",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=self.TEXT_MUTED,
                anchor="w"
            )
            subtitle_label.pack(anchor="w")

            # Conteneur principal scrollable
            main_frame = ctk.CTkScrollableFrame(
                window,
                fg_color="transparent",
                scrollbar_button_color=self.CARD_COLOR,
                scrollbar_button_hover_color=self.ACCENT_COLOR
            )
            main_frame.pack(fill="both", expand=True, padx=30, pady=(10, 20))

            # Cards de configuration
            self._create_card(main_frame, "Modele IA", "Choisissez la taille du modele Whisper",
                lambda p: self._create_model_selector(p, model_var))

            self._create_card(main_frame, "Langue", "Langue de transcription",
                lambda p: self._create_language_selector(p, language_var))

            self._create_card(main_frame, "Acceleration", "Configuration materielle",
                lambda p: self._create_device_section(p, device_var, compute_var))

            self._create_card(main_frame, "Raccourci", "Touche pour demarrer/arreter",
                lambda p: self._create_hotkey_entry(p, hotkey_var))

            # Boutons en bas
            button_frame = ctk.CTkFrame(window, fg_color="transparent", height=60)
            button_frame.pack(fill="x", padx=30, pady=(0, 25))
            button_frame.pack_propagate(False)

            def on_cancel():
                self._is_open = False
                window.destroy()

            def on_save():
                self._save_settings(
                    model_var.get(),
                    language_var.get(),
                    device_var.get(),
                    compute_var.get(),
                    hotkey_var.get()
                )
                self._is_open = False
                window.destroy()

            cancel_btn = ctk.CTkButton(
                button_frame,
                text="Annuler",
                width=120,
                height=42,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                fg_color="transparent",
                border_width=2,
                border_color=self.TEXT_MUTED,
                text_color=self.TEXT_COLOR,
                hover_color=self.CARD_COLOR,
                corner_radius=10,
                command=on_cancel
            )
            cancel_btn.pack(side="left")

            save_btn = ctk.CTkButton(
                button_frame,
                text="Sauvegarder",
                width=140,
                height=42,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                fg_color=self.ACCENT_COLOR,
                hover_color=self.ACCENT_HOVER,
                text_color="white",
                corner_radius=10,
                command=on_save
            )
            save_btn.pack(side="right")

            # Callback fermeture
            window.protocol("WM_DELETE_WINDOW", on_cancel)

            # Focus sur la fenetre
            window.focus_force()
            window.lift()
            window.attributes("-topmost", True)
            window.after(100, lambda: window.attributes("-topmost", False))

            # Lancer la mainloop
            window.mainloop()

        except Exception as e:
            print(f"[Settings] Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_open = False
            # Nettoyer tkinter/customtkinter pour eviter les conflits
            try:
                import tkinter as tk
                tk._default_root = None
            except Exception:
                pass
            try:
                import customtkinter.windows.ctk_tk
                customtkinter.windows.ctk_tk.CTk._current_instance = None
            except Exception:
                pass

    def _create_card(self, parent, title: str, subtitle: str, content_creator: Callable):
        """Cree une carte de configuration"""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD_COLOR,
            corner_radius=15
        )
        card.pack(fill="x", pady=(0, 12))

        # Padding interne
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)

        # Titre de la carte
        title_label = ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        title_label.pack(fill="x")

        # Sous-titre
        subtitle_label = ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        subtitle_label.pack(fill="x", pady=(2, 12))

        # Contenu
        content_creator(inner)

    def _create_model_selector(self, parent, model_var):
        """Cree le selecteur de modele avec indicateurs"""
        # Frame pour les boutons radio visuels
        options_frame = ctk.CTkFrame(parent, fg_color="transparent")
        options_frame.pack(fill="x")

        model_info = {
            "tiny": ("Tiny", "Tres rapide", "~1GB RAM"),
            "base": ("Base", "Rapide", "~1GB RAM"),
            "small": ("Small", "Equilibre", "~2GB RAM"),
            "medium": ("Medium", "Precis", "~5GB RAM"),
            "large-v3": ("Large", "Tres precis", "~10GB RAM"),
        }

        for i, model in enumerate(self.MODELS):
            name, speed, ram = model_info.get(model, (model, "", ""))

            btn = ctk.CTkButton(
                options_frame,
                text=name,
                width=80,
                height=36,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color=self.ACCENT_COLOR if model_var.get() == model else "transparent",
                border_width=1,
                border_color=self.ACCENT_COLOR if model_var.get() == model else self.TEXT_MUTED,
                text_color="white" if model_var.get() == model else self.TEXT_MUTED,
                hover_color=self.ACCENT_HOVER,
                corner_radius=8,
                command=lambda m=model: self._select_model(model_var, m, options_frame)
            )
            btn.pack(side="left", padx=(0, 8))

    def _select_model(self, model_var, model, parent):
        """Met a jour la selection du modele"""
        model_var.set(model)
        # Rafraichir les boutons
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                is_selected = widget.cget("text").lower() == model.replace("-v3", "")
                widget.configure(
                    fg_color=self.ACCENT_COLOR if is_selected else "transparent",
                    border_color=self.ACCENT_COLOR if is_selected else self.TEXT_MUTED,
                    text_color="white" if is_selected else self.TEXT_MUTED
                )

    def _create_language_selector(self, parent, language_var):
        """Cree le selecteur de langue"""
        language_names = [name for name, _ in self.LANGUAGES]

        dropdown = ctk.CTkOptionMenu(
            parent,
            values=language_names,
            variable=language_var,
            width=250,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.BG_COLOR,
            button_color=self.ACCENT_COLOR,
            button_hover_color=self.ACCENT_HOVER,
            dropdown_fg_color=self.BG_COLOR,
            dropdown_hover_color=self.ACCENT_COLOR,
            corner_radius=8,
            dynamic_resizing=False
        )
        dropdown.pack(anchor="w")

    def _create_device_section(self, parent, device_var, compute_var):
        """Cree la section device et compute type"""
        # Device
        device_label = ctk.CTkLabel(
            parent,
            text="Processeur",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        device_label.pack(fill="x", pady=(0, 5))

        device_frame = ctk.CTkFrame(parent, fg_color="transparent")
        device_frame.pack(fill="x", pady=(0, 15))

        device_info = {
            "cpu": "CPU",
            "cuda": "GPU NVIDIA",
            "auto": "Auto"
        }

        for device in self.DEVICES:
            btn = ctk.CTkButton(
                device_frame,
                text=device_info.get(device, device),
                width=100,
                height=34,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color=self.ACCENT_COLOR if device_var.get() == device else "transparent",
                border_width=1,
                border_color=self.ACCENT_COLOR if device_var.get() == device else self.TEXT_MUTED,
                text_color="white" if device_var.get() == device else self.TEXT_MUTED,
                hover_color=self.ACCENT_HOVER,
                corner_radius=8,
                command=lambda d=device: self._select_device(device_var, d, device_frame)
            )
            btn.pack(side="left", padx=(0, 8))

        # Compute type
        compute_label = ctk.CTkLabel(
            parent,
            text="Precision",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        compute_label.pack(fill="x", pady=(0, 5))

        compute_dropdown = ctk.CTkOptionMenu(
            parent,
            values=self.COMPUTE_TYPES,
            variable=compute_var,
            width=200,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.BG_COLOR,
            button_color=self.ACCENT_COLOR,
            button_hover_color=self.ACCENT_HOVER,
            dropdown_fg_color=self.BG_COLOR,
            dropdown_hover_color=self.ACCENT_COLOR,
            corner_radius=8,
            dynamic_resizing=False
        )
        compute_dropdown.pack(anchor="w")

    def _select_device(self, device_var, device, parent):
        """Met a jour la selection du device"""
        device_var.set(device)
        device_info = {"cpu": "CPU", "cuda": "GPU NVIDIA", "auto": "Auto"}
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text")
                is_selected = text == device_info.get(device, device)
                widget.configure(
                    fg_color=self.ACCENT_COLOR if is_selected else "transparent",
                    border_color=self.ACCENT_COLOR if is_selected else self.TEXT_MUTED,
                    text_color="white" if is_selected else self.TEXT_MUTED
                )

    def _create_hotkey_entry(self, parent, hotkey_var):
        """Cree le champ de saisie du hotkey"""
        entry = ctk.CTkEntry(
            parent,
            textvariable=hotkey_var,
            width=250,
            height=40,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=self.BG_COLOR,
            border_color=self.TEXT_MUTED,
            text_color=self.TEXT_COLOR,
            placeholder_text="ex: ctrl+space",
            placeholder_text_color=self.TEXT_MUTED,
            corner_radius=8
        )
        entry.pack(anchor="w")

        info = ctk.CTkLabel(
            parent,
            text="Exemples: ctrl+space, alt+r, ctrl+shift+w",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        info.pack(anchor="w", pady=(5, 0))

    def _save_settings(self, model: str, language_name: str, device: str,
                       compute: str, hotkey: str):
        """Sauvegarde les parametres"""
        hotkey = hotkey.strip().lower()

        # Convertir nom de langue en code
        language_code = "fr"
        for name, code in self.LANGUAGES:
            if name == language_name:
                language_code = code
                break

        # Detecter les changements qui necessitent un rechargement du modele
        model_changed = (
            model != self.settings.whisper_model or
            device != self.settings.device or
            compute != self.settings.compute_type
        )
        hotkey_changed = hotkey != self.settings.hotkey

        # Mettre a jour les settings
        self.settings.set("whisper_model", model)
        self.settings.set("language", language_code)
        self.settings.set("device", device)
        self.settings.set("compute_type", compute)
        self.settings.set("hotkey", hotkey)

        # Sauvegarder
        self.settings.save()

        print(f"[Settings] Sauvegarde: model={model}, lang={language_code}, device={device}")

        # Appeler le callback si fourni
        if self.on_save_callback:
            self.on_save_callback(model_changed, hotkey_changed)

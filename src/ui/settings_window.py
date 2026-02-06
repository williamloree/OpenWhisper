"""Fenetre de configuration avec design macOS moderne"""
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
    """Fenetre de configuration des parametres OpenWhisper - Style macOS"""

    # Couleurs macOS-like
    BG_COLOR = "#1e1e1e"  # Fond principal sombre
    SIDEBAR_COLOR = "#2a2a2a"  # Sidebar gauche
    CONTENT_BG = "#242424"  # Fond du contenu
    CARD_COLOR = "#2d2d2d"  # Cartes
    ACCENT_COLOR = "#0a84ff"  # Bleu accent macOS
    ACCENT_HOVER = "#0077ed"
    SUCCESS_COLOR = "#30d158"  # Vert macOS
    TEXT_COLOR = "#ffffff"
    TEXT_MUTED = "#8e8e93"
    BORDER_COLOR = "#3a3a3a"
    HOVER_BG = "#3a3a3a"

    # Options disponibles
    MODELS = ["tiny", "base", "small", "medium", "large-v3"]
    LANGUAGES = [
        ("Français", "fr"),
        ("English", "en"),
        ("Deutsch", "de"),
        ("Español", "es"),
        ("Italiano", "it"),
        ("Português", "pt"),
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
            window.title("Paramètres")
            window.geometry("750x550")
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
            x = (window.winfo_screenwidth() - 750) // 2
            y = (window.winfo_screenheight() - 550) // 2
            window.geometry(f"750x550+{x}+{y}")

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

            # === SIDEBAR (gauche) ===
            sidebar = ctk.CTkFrame(
                window,
                width=200,
                fg_color=self.SIDEBAR_COLOR,
                corner_radius=0
            )
            sidebar.pack(side="left", fill="y")
            sidebar.pack_propagate(False)

            # Logo et titre dans sidebar
            sidebar_header = ctk.CTkFrame(sidebar, fg_color="transparent", height=100)
            sidebar_header.pack(fill="x", pady=(30, 20), padx=20)
            sidebar_header.pack_propagate(False)

            # Charger le logo
            try:
                logo_path = get_asset_path(os.path.join("img", "logo.png"))
                if os.path.exists(logo_path):
                    logo_img = Image.open(logo_path).resize((45, 45), Image.LANCZOS)
                    logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(45, 45))
                    logo_label = ctk.CTkLabel(sidebar_header, image=logo_ctk, text="")
                    logo_label.pack(pady=(0, 8))
            except Exception:
                pass

            app_name = ctk.CTkLabel(
                sidebar_header,
                text="OpenWhisper",
                font=ctk.CTkFont(family="SF Pro Display", size=18, weight="bold"),
                text_color=self.TEXT_COLOR
            )
            app_name.pack()

            # Menu items (style macOS)
            menu_items = [
                ("⚙️", "Général", "general"),
                ("🎤", "Transcription", "transcription"),
                ("⚡", "Performance", "performance"),
                ("⌨️", "Raccourcis", "shortcuts"),
            ]

            selected_section = ctk.StringVar(value="general")

            for icon, label, section_id in menu_items:
                self._create_sidebar_item(sidebar, icon, label, section_id, selected_section)

            # === CONTENU PRINCIPAL (droite) ===
            content_area = ctk.CTkFrame(window, fg_color=self.CONTENT_BG, corner_radius=0)
            content_area.pack(side="right", fill="both", expand=True)

            # Header du contenu
            content_header = ctk.CTkFrame(content_area, fg_color="transparent", height=80)
            content_header.pack(fill="x", padx=35, pady=(25, 10))
            content_header.pack_propagate(False)

            title_label = ctk.CTkLabel(
                content_header,
                text="Paramètres",
                font=ctk.CTkFont(family="SF Pro Display", size=32, weight="bold"),
                text_color=self.TEXT_COLOR,
                anchor="w"
            )
            title_label.pack(anchor="w")

            subtitle_label = ctk.CTkLabel(
                content_header,
                text="Configurez votre expérience OpenWhisper",
                font=ctk.CTkFont(family="SF Pro Text", size=13),
                text_color=self.TEXT_MUTED,
                anchor="w"
            )
            subtitle_label.pack(anchor="w", pady=(5, 0))

            # Séparateur
            separator = ctk.CTkFrame(content_area, height=1, fg_color=self.BORDER_COLOR)
            separator.pack(fill="x", padx=35)

            # Zone scrollable pour les settings
            scroll_frame = ctk.CTkScrollableFrame(
                content_area,
                fg_color="transparent",
                scrollbar_button_color=self.CARD_COLOR,
                scrollbar_button_hover_color=self.HOVER_BG
            )
            scroll_frame.pack(fill="both", expand=True, padx=35, pady=20)

            # === SECTIONS DE CONFIGURATION ===
            
            # Modèle IA
            self._create_macos_section(
                scroll_frame,
                "Modèle d'intelligence artificielle",
                "Sélectionnez le modèle Whisper pour la transcription",
                lambda p: self._create_model_grid(p, model_var)
            )

            # Langue
            self._create_macos_section(
                scroll_frame,
                "Langue de transcription",
                "Langue utilisée pour la reconnaissance vocale",
                lambda p: self._create_language_dropdown(p, language_var)
            )

            # Performance
            self._create_macos_section(
                scroll_frame,
                "Paramètres de performance",
                "Configuration du matériel et de la précision",
                lambda p: self._create_performance_controls(p, device_var, compute_var)
            )

            # Raccourci clavier
            self._create_macos_section(
                scroll_frame,
                "Raccourci clavier",
                "Touche pour démarrer et arrêter l'enregistrement",
                lambda p: self._create_hotkey_control(p, hotkey_var)
            )

            # === BOUTONS DE CONTROLE (style macOS) ===
            button_bar = ctk.CTkFrame(content_area, fg_color=self.SIDEBAR_COLOR, height=70, corner_radius=0)
            button_bar.pack(side="bottom", fill="x")
            button_bar.pack_propagate(False)

            button_container = ctk.CTkFrame(button_bar, fg_color="transparent")
            button_container.pack(fill="x", padx=35, pady=15)

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

            # Bouton Annuler (gauche)
            cancel_btn = ctk.CTkButton(
                button_container,
                text="Annuler",
                width=110,
                height=36,
                font=ctk.CTkFont(family="SF Pro Text", size=13),
                fg_color="transparent",
                border_width=1,
                border_color=self.BORDER_COLOR,
                text_color=self.TEXT_COLOR,
                hover_color=self.HOVER_BG,
                corner_radius=8,
                command=on_cancel
            )
            cancel_btn.pack(side="left")

            # Bouton Enregistrer (droite)
            save_btn = ctk.CTkButton(
                button_container,
                text="Enregistrer",
                width=130,
                height=36,
                font=ctk.CTkFont(family="SF Pro Text", size=13, weight="bold"),
                fg_color=self.ACCENT_COLOR,
                hover_color=self.ACCENT_HOVER,
                text_color="white",
                corner_radius=8,
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

    def _create_sidebar_item(self, parent, icon, label, section_id, selected_var):
        """Crée un item de menu dans la sidebar (style macOS)"""
        is_selected = selected_var.get() == section_id
        
        item = ctk.CTkButton(
            parent,
            text=f"{icon}  {label}",
            width=160,
            height=40,
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            fg_color=self.HOVER_BG if is_selected else "transparent",
            text_color=self.TEXT_COLOR if is_selected else self.TEXT_MUTED,
            hover_color=self.HOVER_BG,
            corner_radius=8,
            anchor="w",
            command=lambda: selected_var.set(section_id)
        )
        item.pack(padx=20, pady=3)

    def _create_macos_section(self, parent, title: str, subtitle: str, content_creator: Callable):
        """Crée une section de configuration style macOS"""
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", pady=(0, 25))

        # Titre de la section
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(family="SF Pro Display", size=17, weight="bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 3))

        # Sous-titre
        subtitle_label = ctk.CTkLabel(
            section_frame,
            text=subtitle,
            font=ctk.CTkFont(family="SF Pro Text", size=12),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        subtitle_label.pack(fill="x", pady=(0, 12))

        # Carte de contenu
        card = ctk.CTkFrame(
            section_frame,
            fg_color=self.CARD_COLOR,
            corner_radius=10,
            border_width=1,
            border_color=self.BORDER_COLOR
        )
        card.pack(fill="x")

        content_wrapper = ctk.CTkFrame(card, fg_color="transparent")
        content_wrapper.pack(fill="x", padx=20, pady=16)

        content_creator(content_wrapper)

    def _create_model_grid(self, parent, model_var):
        """Crée la grille de sélection de modèle (style macOS)"""
        model_info = {
            "tiny": ("Tiny", "Très rapide, ~1GB"),
            "base": ("Base", "Rapide, ~1GB"),
            "small": ("Small", "Équilibré, ~2GB"),
            "medium": ("Medium", "Précis, ~5GB"),
            "large-v3": ("Large", "Très précis, ~10GB"),
        }

        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(fill="x")

        for i, model in enumerate(self.MODELS):
            name, desc = model_info.get(model, (model, ""))
            is_selected = model_var.get() == model

            model_btn = ctk.CTkButton(
                grid_frame,
                text=f"{name}\n{desc}",
                width=120,
                height=65,
                font=ctk.CTkFont(family="SF Pro Text", size=12),
                fg_color=self.ACCENT_COLOR if is_selected else self.BG_COLOR,
                border_width=1,
                border_color=self.ACCENT_COLOR if is_selected else self.BORDER_COLOR,
                text_color="white" if is_selected else self.TEXT_COLOR,
                hover_color=self.ACCENT_HOVER if is_selected else self.HOVER_BG,
                corner_radius=8,
                command=lambda m=model: self._select_model(model_var, m, grid_frame)
            )
            
            # Disposition en ligne avec espacement
            row = i // 3
            col = i % 3
            model_btn.grid(row=row, column=col, padx=6, pady=6, sticky="ew")

        # Configurer les colonnes pour qu'elles s'étendent uniformément
        for col in range(3):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="model")

    def _select_model(self, model_var, model, parent):
        """Met à jour la sélection du modèle"""
        model_var.set(model)
        # Rafraîchir tous les boutons de modèle
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                button_text = widget.cget("text").split("\n")[0]
                is_selected = button_text == model.replace("-v3", "").capitalize() or \
                             (button_text == "Large" and model == "large-v3")
                widget.configure(
                    fg_color=self.ACCENT_COLOR if is_selected else self.BG_COLOR,
                    border_color=self.ACCENT_COLOR if is_selected else self.BORDER_COLOR,
                    text_color="white" if is_selected else self.TEXT_COLOR,
                    hover_color=self.ACCENT_HOVER if is_selected else self.HOVER_BG
                )

    def _create_language_dropdown(self, parent, language_var):
        """Crée le sélecteur de langue (style macOS)"""
        language_names = [name for name, _ in self.LANGUAGES]

        dropdown = ctk.CTkOptionMenu(
            parent,
            values=language_names,
            variable=language_var,
            width=300,
            height=36,
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            dropdown_font=ctk.CTkFont(family="SF Pro Text", size=12),
            fg_color=self.BG_COLOR,
            button_color=self.ACCENT_COLOR,
            button_hover_color=self.ACCENT_HOVER,
            dropdown_fg_color=self.CARD_COLOR,
            dropdown_hover_color=self.HOVER_BG,
            corner_radius=8,
            dynamic_resizing=False
        )
        dropdown.pack(anchor="w")

    def _create_performance_controls(self, parent, device_var, compute_var):
        """Crée les contrôles de performance (style macOS)"""
        # Device selector
        device_label = ctk.CTkLabel(
            parent,
            text="Processeur",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        device_label.pack(fill="x", pady=(0, 8))

        device_frame = ctk.CTkFrame(parent, fg_color="transparent")
        device_frame.pack(fill="x", pady=(0, 18))

        device_info = {
            "cpu": ("CPU", "Processeur uniquement"),
            "cuda": ("GPU", "Accélération NVIDIA"),
            "auto": ("Auto", "Détection automatique")
        }

        for device, (label, desc) in device_info.items():
            is_selected = device_var.get() == device
            
            btn = ctk.CTkButton(
                device_frame,
                text=f"{label}\n{desc}",
                width=140,
                height=55,
                font=ctk.CTkFont(family="SF Pro Text", size=12),
                fg_color=self.ACCENT_COLOR if is_selected else self.BG_COLOR,
                border_width=1,
                border_color=self.ACCENT_COLOR if is_selected else self.BORDER_COLOR,
                text_color="white" if is_selected else self.TEXT_COLOR,
                hover_color=self.ACCENT_HOVER if is_selected else self.HOVER_BG,
                corner_radius=8,
                command=lambda d=device: self._select_device(device_var, d, device_frame)
            )
            btn.pack(side="left", padx=(0, 10))

        # Compute type selector
        compute_label = ctk.CTkLabel(
            parent,
            text="Précision de calcul",
            font=ctk.CTkFont(family="SF Pro Text", size=12, weight="bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        compute_label.pack(fill="x", pady=(0, 8))

        compute_dropdown = ctk.CTkOptionMenu(
            parent,
            values=self.COMPUTE_TYPES,
            variable=compute_var,
            width=250,
            height=36,
            font=ctk.CTkFont(family="SF Pro Text", size=13),
            fg_color=self.BG_COLOR,
            button_color=self.ACCENT_COLOR,
            button_hover_color=self.ACCENT_HOVER,
            dropdown_fg_color=self.CARD_COLOR,
            dropdown_hover_color=self.HOVER_BG,
            corner_radius=8,
            dynamic_resizing=False
        )
        compute_dropdown.pack(anchor="w")

    def _select_device(self, device_var, device, parent):
        """Met à jour la sélection du device"""
        device_var.set(device)
        device_info = {
            "cpu": ("CPU", "Processeur uniquement"),
            "cuda": ("GPU", "Accélération NVIDIA"),
            "auto": ("Auto", "Détection automatique")
        }
        
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                text = widget.cget("text").split("\n")[0]
                label, _ = device_info.get(device, (device, ""))
                is_selected = text == label
                widget.configure(
                    fg_color=self.ACCENT_COLOR if is_selected else self.BG_COLOR,
                    border_color=self.ACCENT_COLOR if is_selected else self.BORDER_COLOR,
                    text_color="white" if is_selected else self.TEXT_COLOR,
                    hover_color=self.ACCENT_HOVER if is_selected else self.HOVER_BG
                )

    def _create_hotkey_control(self, parent, hotkey_var):
        """Crée le contrôle du raccourci clavier (style macOS)"""
        entry_frame = ctk.CTkFrame(parent, fg_color="transparent")
        entry_frame.pack(fill="x")

        entry = ctk.CTkEntry(
            entry_frame,
            textvariable=hotkey_var,
            width=300,
            height=40,
            font=ctk.CTkFont(family="SF Pro Text", size=14),
            fg_color=self.BG_COLOR,
            border_width=1,
            border_color=self.BORDER_COLOR,
            text_color=self.TEXT_COLOR,
            placeholder_text="ex: ctrl+space",
            placeholder_text_color=self.TEXT_MUTED,
            corner_radius=8
        )
        entry.pack(anchor="w")

        hint = ctk.CTkLabel(
            parent,
            text="💡 Exemples: ctrl+space, alt+r, ctrl+shift+w",
            font=ctk.CTkFont(family="SF Pro Text", size=11),
            text_color=self.TEXT_MUTED,
            anchor="w"
        )
        hint.pack(anchor="w", pady=(8, 0))

    def _save_settings(self, model: str, language_name: str, device: str,
                       compute: str, hotkey: str):
        """Sauvegarde les paramètres"""
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
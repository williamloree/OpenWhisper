from src.app import OpenWhisperApp

if __name__ == "__main__":
    app = OpenWhisperApp()
    app.create_tray_icon()
    app.run()

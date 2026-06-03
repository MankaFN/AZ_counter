import customtkinter as ctk

class SettingsWindow:
    def __init__(self, app):
        self.app = app

        self.settings_window = ctk.CTkToplevel()
        self.settings_window.withdraw()

        self.settings_window.title("Settings")
        self.settings_window.geometry("300x270+240+150")

        self._settings_ui()

    def _settings_ui(self):
        self.settings_window.protocol("WM_DELETE_WINDOW", self.app.main_window_show)

    def show(self):
        self.settings_window.deiconify()

    def hide(self):
        self.settings_window.withdraw()
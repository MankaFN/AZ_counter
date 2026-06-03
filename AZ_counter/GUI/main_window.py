import customtkinter as ctk

class MainWindow:
    def __init__(self, app):
        self.app = app

        self.window = ctk.CTkToplevel()
        self.window.withdraw()

        self.window.geometry("1000x600+240+150")
        self.window.title("Az_counter")
        self._main_ui()

    def _main_ui(self):
        self.window.protocol("WM_DELETE_WINDOW", self.app.root.destroy)

        ctk.CTkButton(self.window, text = "⚙️", command = self._settings_window).place(x=10, y=10)

    def _settings_window(self):
        self.app.settings_window_show()

    def hide(self):
        self.window.withdraw()

    def show(self):
        self.window.deiconify()
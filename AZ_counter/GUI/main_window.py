import customtkinter as ctk

class MainWindow:
    def __init__(self, app):
        self.app = app

        self.window = ctk.CTk()
        self.window.geometry("600x600")
        self.window.title("Az_counter")
        self._build_ui()

    def _build_ui(self):
        ctk.CTkButton(self.window, text = "⚙️", command = self._settings_window).place(x=10, y=10)

    def _settings_window(self):
        self.window.destroy()

    def run(self):
        self.window.mainloop()

import customtkinter as ctk

class MainWindow:
    def __init__(self, app):
        self.app = app

        self.window = ctk.CTkToplevel()
        self.window.withdraw()

        self.window.geometry("1000x600+240+150")
        self.window.title("Az_counter")

        self.window.protocol("WM_DELETE_WINDOW", self.app.root.destroy)

    def _main_ui(self):
        ctk.CTkButton(self.window, text="⚙️", width=1, command = self._settings_window).place(x=15, y=15)

        ctk.CTkLabel(self.window, text=self.app.storage.get_login()).place(x=850, y=10)
        ctk.CTkButton(self.window, text="Сменить логин", command = self._login_window).place(x=840, y=40)

    def _settings_window(self):
        self.app.settings_window_show()

    def _login_window(self):
        self.app.login_window_show()

    def show(self):
        self._main_ui()
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()
        for widget in self.window.winfo_children():
            widget.destroy()
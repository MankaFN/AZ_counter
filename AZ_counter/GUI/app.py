import customtkinter as ctk
from GUI.login_window import LoginWindow
from GUI.main_window import MainWindow
from GUI.settings_window import SettingsWindow

class App(ctk.CTk):
    def __init__(self, storage, scraper):
        super().__init__()

        self.storage = storage
        self.scraper = scraper

        self.login_frame = LoginWindow(self, self.storage, self.scraper)
        self.main_frame = MainWindow(self)
        self.settings_frame = SettingsWindow(self)

    def _login_window_show(self):
        self.geometry("350x300")
        self.title("Login")
        
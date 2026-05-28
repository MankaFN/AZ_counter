import customtkinter as ctk

class SettingsWindow:
    def __init__(self, storage, scraper):
        self.storage = storage
        self.scraper = scraper

        self.settings_window = ctk.CTk()
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x300")


    def run(self):
        self.settings_window.mainloop()
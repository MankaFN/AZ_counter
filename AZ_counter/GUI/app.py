from GUI.login_window import LoginWindow
from GUI.main_window import MainWindow
from GUI.settings_window import SettingsWindow
from AI.AI_data_giver import AIMarksData
from AI.AI_predictor import AIPredictor
from customtkinter import CTk

class App:
    def __init__(self, storage, scraper):
        self.storage = storage
        self.scraper = scraper

        self.root = CTk()
        self.root.withdraw()

        self.AI_data_giver = AIMarksData()
        self.AI_predictor = AIPredictor(self.AI_data_giver)

        self.login_window = LoginWindow(self)
        self.main_window = MainWindow(self)
        self.settings_window = SettingsWindow(self)

        if self.storage.has_data():
            self.main_window_show()
        else:
            self.login_window_show()

        self.root.mainloop()

    def settings_window_show(self):
        self.main_window.hide()
        self.settings_window.show()

    def login_window_show(self):
        self.main_window.hide()
        self.login_window.show()

    def main_window_show(self):
        self.settings_window.hide()
        self.login_window.hide()
        self.main_window.show()
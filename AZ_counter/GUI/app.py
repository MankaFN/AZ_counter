from AZ_counter.GUI.login_window import LoginWindow
from AZ_counter.GUI.main_window import MainWindow
from AZ_counter.GUI.settings_window import SettingsWindow
from AZ_counter.AI.AI_data_giver import AIMarksData
from AZ_counter.AI.AI_predictor import AIPredictor
from customtkinter import CTk


class App:
    def __init__(self, storage, scraper):
        self.storage = storage
        self.scraper = scraper

        self.root = CTk()
        self.root.withdraw()

        self.AI_data_giver = AIMarksData(window_size=self.storage.get_window_size())
        self.AI_predictor = AIPredictor(self.AI_data_giver)

        self.login_window = LoginWindow(self)
        self.main_window = MainWindow(self)
        self.settings_window = SettingsWindow(self)

        if self.storage.has_data():
            self.main_window_show()
        else:
            self.login_window_show()

        self.root.mainloop()

    def quit_app(self):
        self.root.quit()

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

    def ai_retrain(self, window_size):
        self.AI_data_giver = AIMarksData(window_size=window_size)
        self.AI_predictor = AIPredictor(self.AI_data_giver)
        self.storage.set_window_size(window_size)

    def ai_predictor(self, subject: str, n: int = 1):
        marks = self.storage.marks_give()
        predict = []
        for _ in range(n):
            predict.append(self.AI_predictor.predict(marks, subject))
            marks[subject][0].append(f"{predict[-1]}1")
        return predict

    def get_marks(self):
        return self.storage.marks_give()
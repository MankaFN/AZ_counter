import customtkinter as ctk
from services.scraper import NetworkError, AuthError
from CTkMessagebox import CTkMessagebox

class LoginWindow(ctk.CTkFrame):
    def __init__(self, parent, storage, scraper):
        super().__init__(parent)

        self.storage = storage
        self.scraper = scraper

        self.login_window = ctk.CTk()
        self.login_window.title("Login")
        self.login_window.geometry("350x300")

        self._login_entry = None
        self._password_entry = None
        self._trimester_box = None
        self._show_browser_var = ctk.BooleanVar(value=False)

        self._login_ui()

    def _login_ui(self):
        ctk.CTkLabel(self.login_window, text="Логин").place(x=80, y=10)
        self._login_entry = ctk.CTkEntry(self.login_window, width=200)
        self._login_entry.place(x=60, y=40)

        ctk.CTkLabel(self.login_window, text="Пароль").place(x=80, y=70)
        self._password_entry = ctk.CTkEntry(self.login_window, show="•", width=200)
        self._password_entry.place(x=60, y=100)

        ctk.CTkLabel(self.login_window, text="Триместр").place(x=125, y=130)
        self._trimester_box = ctk.CTkComboBox(self.login_window, values=["1 - полугодие", "2 - полугодие"], state="readonly")
        self._trimester_box.place(x=100, y=160)

        self._show_browser_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self.login_window, text="Показать вход", variable=self._show_browser_var, checkbox_width=20, checkbox_height=20, corner_radius=4).place(x=220, y=220)

        ctk.CTkButton(self.login_window, text="Войти", command = lambda: self._register(self._login_entry.get(), self._password_entry.get(), self._trimester_box.get(), self._show_browser_var.get())).place(x=70, y=216)

    def _message_show(self, message, icon):
        CTkMessagebox(title="Ошибка", message=message, icon=icon, font=("Arial", 14))
        self.login_window.focus_force()
        self._login_entry.focus_force()

    def _register(self, login: str, password: str, trim: str, screen_show: bool):
        if not login or not password:
            self._message_show("Введите логин и пароль", "warning")
        else:
            try:
                marks_grade = self.scraper.scrape(login, password, int(trim[0]) if trim else None, screen_show)
                self.storage.save_marks(marks_grade["marks"])
                self._message_show("Успешный вход", "check")

            except NetworkError:
                self._message_show("Отсутствует подключение к интеренуту", "cancel")

            except AuthError:
                self._message_show("Неверный логин или пароль", "cancel")

    def run(self):
        self.login_window.mainloop()
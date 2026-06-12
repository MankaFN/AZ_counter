import customtkinter as ctk
from AZ_counter.logic.calculator import Calculator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from AZ_counter.logic.charts import avg_score_schedule

class MainWindow:
    def __init__(self, app):
        self.app = app
        self.marks = None
        self.calculator = None

        self.window = ctk.CTkToplevel()
        self.window.withdraw()

        self.window.geometry("1000x600+240+150")
        self.window.title("Az_counter")

        self.window.protocol("WM_DELETE_WINDOW", self.app.quit_app)

    def _main_ui(self):
        ctk.CTkButton(self.window, text="⚙️", width=1, command = self._settings_window).place(x=15, y=15)

        ctk.CTkLabel(self.window, text=self.app.storage.get_login()).place(x=850, y=10)
        ctk.CTkButton(self.window, text="Сменить логин", command = self._login_window).place(x=840, y=40)

        ctk.CTkLabel(self.window, text="Графики", font=("Arial", 18, "bold")).place(x=260, y=100)

        ctk.CTkLabel(self.window, text="График среднего балла по предмету").place(x=185, y=155)
        subject_avg_score = ctk.CTkComboBox(self.window, values = [i for i in self.marks if len(self.marks[i][0]) > 1])
        subject_avg_score.place(x=230, y=185)
        ctk.CTkButton(self.window, text="Построить", width=6, command=lambda: self._avg_score_subject_show(subject_avg_score.get())).place(x=260, y=220)

        ctk.CTkLabel(self.window, text = "Предсказать оценки").place(x=530, y=250)
        marks_predict = ctk.CTkEntry(self.window)
        marks_predict.place(x=800, y = 300)
        subject_predict = ctk.CTkComboBox(self.window, values = [i for i in self.marks if len(self.marks[i][0]) >= 1])
        subject_predict.place(x=530, y=300)
        ctk.CTkButton(self.window, text="Предсказать", command=lambda: self._marks_predict(subject_predict.get(), marks_predict.get())).place(x=530, y=400)


    def _settings_window(self):
        self.app.settings_window_show()

    def _login_window(self):
        self.app.login_window_show()

    def _marks_predict(self, subject, n):
        try:
            predict = self.app.ai_predictor(subject, int(n))
            print(predict)
        except ValueError:
            pass

    def _avg_score_subject_show(self, subject_avg_score):
        avg_score_history = self.calculator.avg_score_history(subject_avg_score)
        fig = avg_score_schedule(avg_score_history)
        self._open_chart_window(fig, subject_avg_score)

    @staticmethod
    def _open_chart_window(fig, title):
        chart_window = ctk.CTkToplevel()
        chart_window.geometry("1200x800")
        chart_window.title(title)

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, chart_window)
        toolbar.update()

        toolbar.pack(side="top", fill="x")
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)


    def show(self):
        self.marks = self.app.get_marks()
        self.calculator = Calculator(self.marks)
        self._main_ui()
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()
        for widget in self.window.winfo_children():
            widget.destroy()
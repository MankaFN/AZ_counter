import ast
from  pytorch_tabnet.tab_model import TabNetClassifier
import numpy as np

subjects = {
    "id0": ["физика"],
    "id1": ["алгебра", "практикум по геометрии", "геометрия", "информатика"],
    "id2": ["география", "история", "литература", "обществознание"],
    "id3": ["биология", "химия"],
    "id4": ["русский язык", "английский язык"]
}

grades = {
    "8": 0,
    "10": 1
}

class AIMarksPredict:
    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.model = TabNetClassifier()
        try:
            self.model.load_model('./best_tabnet.zip')
        except FileNotFoundError:
            self.ai_retraining()

    def ai_retraining(self):
        X, Y = self._data_read()
        self._ai_retraining(X, Y)


    def _data_read(self) -> tuple:
        X, Y = [], []
        subject = 0
        grade = 1

        with open("AI_data/marks_data.txt", "r") as data_file:
            for lines in data_file.readlines():
                if len(lines) > 6:
                    lines = lines.split(" = ")

                    for sub in subjects:
                        if lines[0] in subjects[sub]:
                            subject = int(sub[-1])
                            break
                        elif sub == list(subjects.keys())[-1]:
                            subject = int(list(subjects.keys())[-1][-1])+1

                    lines = ast.literal_eval(lines[1])

                    for i in range(len(lines[0]) - self.window_size):
                        data_for_learn = []
                        for j in range(self.window_size):

                            if not lines[0][i+j].isdigit() or lines[0][i+j][1] == "0":
                                data_for_learn = []
                                break

                            data_for_learn.append(int(lines[0][i+j][0]))
                            data_for_learn.append(int(lines[0][i+j][1]))

                        if data_for_learn and lines[0][i+self.window_size].isdigit() and lines[0][i+self.window_size][1] != "0":
                            data_for_learn.append(subject)
                            data_for_learn.append(grades[str(grade)])
                            data_for_learn.append(self._skips(lines[1]))
                            data_for_learn.append(self._avg_ball(lines[0][:i + self.window_size]))
                            data_for_learn.append(self._trend(data_for_learn))
                            data_for_learn.append(self._standard_deviation(data_for_learn))

                            X.append(data_for_learn)
                            Y.append(int(lines[0][i + self.window_size][0]))

                elif len(lines) > 2:
                    grade = int(lines)

        return (X, Y)

    def _skips(self, line: str) -> float:
        return round(int(line.split("/")[0])/int(line.split("/")[1])*100, 1)

    def _avg_ball(self, line: list) -> float:
        marks_sum = 0
        marks_count = 0

        for i in line:
            marks_sum += int(i[0])*int(i[1])
            marks_count += int(i[1])

        return round(marks_sum/marks_count, 2)

    def _trend(self, X: list) -> int:
        for i in range(0, self.window_size*2, 2):
            if X[i] != 0:
                return X[(self.window_size-1)*2] - X[i]
        return 0

    def _standard_deviation(self, X: list) -> float:

        valid_elements = [X[i] for i in range(0, self.window_size * 2, 2) if X[i] != 0]
        n = len(valid_elements)
        if n <= 1:
            return 0.0

        arithmetic_mean = sum(valid_elements) / n
        deviation = sum((i - arithmetic_mean) ** 2 for i in valid_elements) / (n - 1)

        return round(deviation ** 0.5, 2)


    def _ai_retraining(self, X, Y):
        from sklearn.model_selection import train_test_split
        import pandas as pd

        X_train, X_valid, Y_train, Y_valid = train_test_split(X, Y, test_size=0.15, random_state=42)

        X_train = np.array(X_train)
        Y_train = np.array(Y_train)
        X_valid = np.array(X_valid)
        Y_valid = np.array(Y_valid)

        print(pd.Series(Y_train).value_counts())

        cat_idxs = [self.window_size*2, self.window_size*2+1]
        cat_dims = [len(subjects)+1, len(grades)]

        self.model = TabNetClassifier(
            n_d=32,
            n_a=32,
            n_steps=7,
            gamma=1.5,
            cat_idxs=cat_idxs,
            cat_dims=cat_dims,
            lambda_sparse=1e-4,
            optimizer_params=dict(lr=1e-2),
            scheduler_params=dict(step_size=15, gamma=0.8)
        )

        self.model.fit(
            X_train=X_train, y_train=Y_train,
            eval_set=[(X_valid, Y_valid)],
            eval_name=['valid'],
            max_epochs=100,
            patience=20,
            batch_size=16,
            virtual_batch_size=8
        )

        self.model.save_model('./best_tabnet')
        explain_matrix, masks = self.model.explain(X_valid)

        # Усредняем маски по всем наблюдениям в тестовой выборке
        global_importance = np.mean(explain_matrix, axis=0)

        # Создаем таблицу DataFrame
        feature_importance_df = pd.DataFrame({
            'Feature': ["Оценка1", "коэффицент1", "Оценка2", "коэффицент2", "Оценка3", "коэффицент3", "Оценка4", "коэффицент4", "Оценка5", "коэффицент5", "предмет", "класс", "скипы", "средний балл", "тренд", "станд отклон"],  # Замените на список названий ваших колонок
            'Importance': global_importance
        })

        # Сортируем от самых влияющих к наименее влияющим
        feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False).reset_index(
            drop=True)

        # Выводим топ самых влияющих параметров
        print(feature_importance_df.head(16))

    def ai_predict(self, marks: dict, grade: int) -> int:

        model = TabNetClassifier()
        model.load_model('./best_tabnet.zip')

        X_pred = []

        subject = next(iter(marks))

        marks[subject][0] = [i for i in marks[subject][0] if (i.isdigit() and str(i[1]) != "0")]

        marks_length = len(marks[subject][0])

        if marks_length-self.window_size >= 0:
            for i in marks[subject][0][marks_length-self.window_size:]:
                X_pred.append(int(str(i)[0]))
                X_pred.append(int(str(i)[1]))

        else:
            for i in range((self.window_size-marks_length)*2):
                X_pred.append(0)

            for i in marks[subject][0]:
                X_pred.append(int(str(i)[0]))
                X_pred.append(int(str(i)[1]))

        subject_id = 0

        for sub in subjects:
            if subject.lower() in subjects[sub]:
                subject_id = int(sub[-1])
                break
            elif sub == list(subjects.keys())[-1]:
                subject_id = int(list(subjects.keys())[-1][-1]) + 1

        X_pred.append(subject_id)
        X_pred.append(grades[str(grade)])
        X_pred.append(self._skips(marks[subject][1]))
        X_pred.append(self._avg_ball(marks[subject][0]))
        X_pred.append(self._trend(X_pred))
        X_pred.append(self._standard_deviation(X_pred))

        X_pred = np.array([X_pred])

        return int(self.model.predict(X_pred)[0])

AI = AIMarksPredict(5)
AI.ai_retraining()
print(AI.ai_predict({"алгебра": [['51', '41', '31', '41', '51', '51', '21', '51', '51', '34', '51', '51', '51', '51', '51', '21', '51', '51', '34', '41', '51', '31'], '9/108']}, 10))
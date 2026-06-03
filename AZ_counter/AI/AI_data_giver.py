import ast

SEED = 67

class AIMarksData:
    def __init__(self, window_size: str = "5", path: str = "AI/AI_data/marks_data.txt"):
        self.window_size = int(window_size)
        self.path = path
        self.X, self.Y = self._data_read()

    def _data_read(self) -> tuple:
        X, Y = [], []

        with open(self.path, "r") as data_file:
            for lines in data_file.readlines():
                if len(lines) > 6:
                    lines = lines.split(" = ")
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
                            data_for_learn.append(self._avg_ball(lines[0][:i + self.window_size]))
                            data_for_learn.append(self._trend(data_for_learn))
                            data_for_learn.append(self._standard_deviation(data_for_learn))

                            X.append(data_for_learn)
                            Y.append(int(lines[0][i + self.window_size][0]))

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

    def _smart_split(self, X, Y, test_size=0.2, val_size=0):
        from sklearn.model_selection import train_test_split
        if val_size == 0:
            X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=test_size, random_state=SEED)
            return (X_train, X_test, y_train, y_test)

    def ai_data_block_1(self):
        Y = [y//4 for y in self.Y]
        return self._smart_split(self.X, Y, 0.3)

    def ai_data_block_2(self):
        X, Y = [], []
        for i in range(len(self.X)):
            if self.Y[i] == 2 or self.Y[i] == 3:
                X.append(self.X[i])
                Y.append(self.Y[i])

        return self._smart_split(X, Y, 0.3)

    def ai_data_block_3(self):
        X, Y = [], []
        for i in range(len(self.X)):
            if self.Y[i] == 4 or self.Y[i] == 5:
                X.append(self.X[i])
                Y.append(self.Y[i])

        return self._smart_split(X, Y, 0.3)


    def ai_data_predict(self, marks: dict) -> list:
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

        X_pred.append(self._avg_ball(marks[subject][0]))
        X_pred.append(self._trend(X_pred))
        X_pred.append(self._standard_deviation(X_pred))

        return X_pred
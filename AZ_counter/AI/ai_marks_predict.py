import ast
import json
from pathlib import Path
from typing import Any

import numpy as np
from xgboost import XGBClassifier


AI_DIR = Path(__file__).resolve().parent
DATA_PATH = AI_DIR / "AI_data" / "marks_data.txt"
MODEL_PATH = AI_DIR / "best_xgboost.json"
META_PATH = AI_DIR / "best_xgboost_meta.json"

subjects = {
    "id0": ["физика"],
    "id1": ["алгебра", "практикум по геометрии", "геометрия", "информатика"],
    "id2": ["география", "история", "литература", "обществознание"],
    "id3": ["биология", "химия"],
    "id4": ["русский язык", "английский язык"],
}

grades = {
    "8": 0,
    "10": 1,
}

LABEL_TO_CLASS = {2: 0, 3: 1, 4: 2, 5: 3}
CLASS_TO_LABEL = {value: key for key, value in LABEL_TO_CLASS.items()}


def _is_valid_mark(mark: Any) -> bool:
    return isinstance(mark, str) and len(mark) >= 2 and mark.isdigit() and mark[1] != "0"


def _subject_id(subject: str) -> int:
    normalized = subject.lower()
    for group_id, names in subjects.items():
        if normalized in names:
            return int(group_id[-1])
    return len(subjects)


def default_xgboost_params() -> dict[str, Any]:
    return {
        "objective": "multi:softprob",
        "num_class": 4,
        "eval_metric": "mlogloss",
        "tree_method": "hist",
        "max_depth": 2,
        "learning_rate": 0.05,
        "n_estimators": 80,
        "min_child_weight": 3,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_lambda": 5.0,
        "reg_alpha": 0.5,
        "gamma": 0.2,
        "random_state": 42,
        "n_jobs": -1,
    }


def tuned_xgboost_params() -> dict[str, Any]:
    params = default_xgboost_params()
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
            params.update(meta.get("selected_params", {}))
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return params


class AIMarksPredict:
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.model = XGBClassifier(**tuned_xgboost_params())
        if MODEL_PATH.exists():
            self.model.load_model(str(MODEL_PATH))
        else:
            self.ai_retraining()

    def ai_retraining(self) -> None:
        X, y, _groups = self._data_read()
        self._ai_retraining(X, y)

    def _data_read(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        X: list[list[float]] = []
        y: list[int] = []
        groups: list[int] = []
        current_grade: int | None = None
        group_index = 0

        with DATA_PATH.open("r", encoding="utf-8") as data_file:
            for raw_line in data_file:
                line = raw_line.strip()
                if not line:
                    continue

                if line in grades:
                    current_grade = int(line)
                    continue

                if current_grade is None or " = " not in line:
                    continue

                subject_name, raw_payload = line.split(" = ", 1)
                try:
                    marks_line, skips_line = ast.literal_eval(raw_payload)
                except (SyntaxError, ValueError):
                    continue

                subject = _subject_id(subject_name)
                grade_id = grades[str(current_grade)]
                group_index += 1

                for i in range(len(marks_line) - self.window_size):
                    window = marks_line[i : i + self.window_size]
                    target = marks_line[i + self.window_size]
                    if not all(_is_valid_mark(mark) for mark in window):
                        continue
                    if not _is_valid_mark(target):
                        continue

                    target_label = int(target[0])
                    if target_label not in LABEL_TO_CLASS:
                        continue

                    history = [mark for mark in marks_line[: i + self.window_size] if _is_valid_mark(mark)]
                    features = self._build_features(window, subject, grade_id, skips_line, history)
                    X.append(features)
                    y.append(LABEL_TO_CLASS[target_label])
                    groups.append(group_index)

        return np.asarray(X, dtype=float), np.asarray(y, dtype=int), np.asarray(groups, dtype=int)

    def _build_features(
        self,
        marks_line: list[str],
        subject: int,
        grade: int,
        skips_line: str,
        avg_line: list[str] | None = None,
    ) -> list[float]:
        features: list[float] = []
        for mark in marks_line:
            features.append(float(mark[0]))
            features.append(float(mark[1]))

        features.append(float(subject))
        features.append(float(grade))
        features.append(self._skips(skips_line))
        features.append(self._avg_ball(avg_line if avg_line is not None else marks_line))
        features.append(self._trend(features))
        features.append(self._standard_deviation(features))
        return features

    def _skips(self, line: str) -> float:
        try:
            skipped, total = line.split("/", 1)
            skipped_count = int(skipped)
            total_count = int(total)
        except (AttributeError, ValueError):
            return 0.0
        if total_count == 0:
            return 0.0
        return round(skipped_count / total_count * 100, 1)

    def _avg_ball(self, line: list[str]) -> float:
        valid_marks = [mark for mark in line if _is_valid_mark(mark)]
        if not valid_marks:
            return 0.0

        marks_sum = sum(int(mark[0]) * int(mark[1]) for mark in valid_marks)
        marks_count = sum(int(mark[1]) for mark in valid_marks)
        if marks_count == 0:
            return 0.0
        return round(marks_sum / marks_count, 2)

    def _trend(self, X: list[float]) -> float:
        for i in range(0, self.window_size * 2, 2):
            if X[i] != 0:
                return X[(self.window_size - 1) * 2] - X[i]
        return 0.0

    def _standard_deviation(self, X: list[float]) -> float:
        valid_elements = [X[i] for i in range(0, self.window_size * 2, 2) if X[i] != 0]
        n = len(valid_elements)
        if n <= 1:
            return 0.0

        arithmetic_mean = sum(valid_elements) / n
        deviation = sum((i - arithmetic_mean) ** 2 for i in valid_elements) / (n - 1)
        return round(deviation**0.5, 2)

    def _ai_retraining(self, X: np.ndarray, y: np.ndarray) -> None:
        if len(X) == 0:
            raise ValueError("Cannot train XGBoost model: dataset is empty.")

        self.model = XGBClassifier(**tuned_xgboost_params())
        self.model.fit(X, y)
        self.model.save_model(str(MODEL_PATH))

    def ai_predict(self, marks: dict, grade: int) -> int:
        subject_name = next(iter(marks))
        subject_marks, skips_line = marks[subject_name]
        valid_marks = [mark for mark in list(subject_marks) if _is_valid_mark(mark)]

        marks_length = len(valid_marks)
        if marks_length >= self.window_size:
            marks_window = valid_marks[-self.window_size :]
        else:
            marks_window = ["00"] * (self.window_size - marks_length) + valid_marks

        subject = _subject_id(subject_name)
        grade_id = grades.get(str(grade), grades["10"])
        X_pred = np.asarray([self._build_features(marks_window, subject, grade_id, skips_line, valid_marks)], dtype=float)
        predicted_class = int(self.model.predict(X_pred)[0])
        return CLASS_TO_LABEL.get(predicted_class, 2)

AI = AIMarksPredict()
AI.ai_retraining()
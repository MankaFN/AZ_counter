import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import randint, uniform
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import ParameterSampler, StratifiedGroupKFold
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from AI.ai_marks_predict import (
    AIMarksPredict,
    CLASS_TO_LABEL,
    MODEL_PATH,
    default_xgboost_params,
)


AI_DIR = Path(__file__).resolve().parent
META_PATH = AI_DIR / "best_xgboost_meta.json"
REPORT_PATH = AI_DIR / "XGBOOST_TUNING_REPORT.md"


def _model_params(params: dict[str, Any], random_state: int = 42) -> dict[str, Any]:
    base = default_xgboost_params()
    base.update(params)
    base["random_state"] = random_state
    return base


def _fit_predict(
    params: dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_valid: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[np.ndarray, XGBClassifier]:
    model = XGBClassifier(**_model_params(params))
    model.fit(X_train, y_train, sample_weight=sample_weight)
    return model.predict(X_valid), model


def _evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 6),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
    }


def _class_distribution(y: np.ndarray) -> dict[str, int]:
    counts = Counter(int(CLASS_TO_LABEL[int(label)]) for label in y)
    return {str(label): counts.get(label, 0) for label in sorted(CLASS_TO_LABEL.values())}


def _select_best(results: list[dict[str, Any]]) -> dict[str, Any]:
    best_f1 = max(result["validation_macro_f1"] for result in results)
    candidates = [result for result in results if result["validation_macro_f1"] >= best_f1 - 0.02]
    return min(
        candidates,
        key=lambda result: (
            result["train_validation_gap"],
            result["params"]["max_depth"],
            result["params"]["n_estimators"],
        ),
    )


def _write_report(meta: dict[str, Any]) -> None:
    params_lines = "\n".join(f"- `{key}`: `{value}`" for key, value in meta["selected_params"].items())
    distribution_lines = "\n".join(
        f"- Оценка `{label}`: train `{counts['train']}`, validation `{counts['validation']}`, test `{counts['test']}`"
        for label, counts in meta["class_distribution"].items()
    )

    report = f"""# XGBoost tuning report

## Шаги настройки

1. Собран датасет из `AI/AI_data/marks_data.txt` с окном последних `{meta["window_size"]}` оценок.
2. Целевые оценки `2`, `3`, `4`, `5` закодированы во внутренние классы `0..3`.
3. Внешнее разбиение сделано первым fold из `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`.
4. На train-части выполнен `ParameterSampler(n_iter=40, random_state=42)`.
5. Для каждой конфигурации использован внутренний `StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=43)`.
6. На каждом внутреннем fold применялись `compute_sample_weight('balanced', y_train_fold)`.
7. Выбор: лучший validation macro F1, затем конфигурации в пределах `0.02` от лучшей с минимальным train-validation gap, затем меньшие `max_depth` и `n_estimators`.

## Эффект параметров

- `max_depth`: ограничивает сложность деревьев; меньшие значения снижают риск переобучения.
- `learning_rate`: уменьшает вклад каждого дерева; низкие значения обычно требуют больше деревьев.
- `n_estimators`: число деревьев; слишком большое значение увеличивает риск переобучения.
- `min_child_weight`: повышает минимальную массу листа и делает модель консервативнее.
- `subsample`: сэмплирует строки для дерева и снижает variance.
- `colsample_bytree`: сэмплирует признаки для дерева и снижает зависимость от отдельных признаков.
- `reg_lambda`: L2-регуляризация весов листьев.
- `reg_alpha`: L1-регуляризация весов листьев.
- `gamma`: минимальный выигрыш для split; рост значения режет слабые разбиения.

## Итоговые метрики

- Train macro F1: `{meta["metrics"]["train"]["macro_f1"]}`, accuracy: `{meta["metrics"]["train"]["accuracy"]}`
- Validation macro F1: `{meta["metrics"]["validation"]["macro_f1"]}`, accuracy: `{meta["metrics"]["validation"]["accuracy"]}`
- Test macro F1: `{meta["metrics"]["test"]["macro_f1"]}`, accuracy: `{meta["metrics"]["test"]["accuracy"]}`
- Inner CV validation macro F1: `{meta["selection"]["validation_macro_f1"]}`
- Inner CV train macro F1: `{meta["selection"]["train_macro_f1"]}`
- Train-validation gap: `{meta["selection"]["train_validation_gap"]}`

## Class distribution

{distribution_lines}

## Selected params

{params_lines}
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    predictor = AIMarksPredict.__new__(AIMarksPredict)
    predictor.window_size = 5
    X, y, groups = AIMarksPredict._data_read(predictor)
    if len(X) == 0:
        raise ValueError("Dataset is empty.")

    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx, test_idx = next(outer.split(X, y, groups))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    groups_train = groups[train_idx]

    param_distributions = {
        "max_depth": [2, 3, 4],
        "learning_rate": uniform(0.025, 0.125),
        "n_estimators": randint(50, 151),
        "min_child_weight": [1, 2, 3, 5, 7],
        "subsample": uniform(0.65, 0.35),
        "colsample_bytree": uniform(0.65, 0.35),
        "reg_lambda": uniform(1.0, 9.0),
        "reg_alpha": uniform(0.0, 2.0),
        "gamma": uniform(0.0, 1.0),
    }

    sampler = ParameterSampler(param_distributions, n_iter=40, random_state=42)
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=43)
    results: list[dict[str, Any]] = []

    for sampled_params in sampler:
        params = {
            key: int(value) if key in {"max_depth", "n_estimators", "min_child_weight"} else float(value)
            for key, value in sampled_params.items()
        }
        train_scores: list[float] = []
        validation_scores: list[float] = []

        for fold_train_idx, fold_valid_idx in inner.split(X_train, y_train, groups_train):
            X_fold_train, X_fold_valid = X_train[fold_train_idx], X_train[fold_valid_idx]
            y_fold_train, y_fold_valid = y_train[fold_train_idx], y_train[fold_valid_idx]
            sample_weight = compute_sample_weight("balanced", y_fold_train)

            valid_pred, model = _fit_predict(params, X_fold_train, y_fold_train, X_fold_valid, sample_weight)
            train_pred = model.predict(X_fold_train)
            train_scores.append(f1_score(y_fold_train, train_pred, average="macro", zero_division=0))
            validation_scores.append(f1_score(y_fold_valid, valid_pred, average="macro", zero_division=0))

        train_macro_f1 = float(np.mean(train_scores))
        validation_macro_f1 = float(np.mean(validation_scores))
        results.append(
            {
                "params": params,
                "train_macro_f1": round(train_macro_f1, 6),
                "validation_macro_f1": round(validation_macro_f1, 6),
                "train_validation_gap": round(abs(train_macro_f1 - validation_macro_f1), 6),
            }
        )

    selected = _select_best(results)
    validation_train_idx, validation_idx = next(inner.split(X_train, y_train, groups_train))
    X_validation_train = X_train[validation_train_idx]
    y_validation_train = y_train[validation_train_idx]
    X_validation = X_train[validation_idx]
    y_validation = y_train[validation_idx]
    validation_weight = compute_sample_weight("balanced", y_validation_train)
    validation_pred, _validation_model = _fit_predict(
        selected["params"],
        X_validation_train,
        y_validation_train,
        X_validation,
        validation_weight,
    )

    sample_weight = compute_sample_weight("balanced", y_train)
    test_pred, final_model = _fit_predict(selected["params"], X_train, y_train, X_test, sample_weight)
    train_pred = final_model.predict(X_train)

    final_model.save_model(str(MODEL_PATH))

    train_distribution = _class_distribution(y_train)
    validation_distribution = _class_distribution(y_validation)
    test_distribution = _class_distribution(y_test)

    meta = {
        "window_size": 5,
        "dataset_size": int(len(X)),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "selected_params": selected["params"],
        "selection": {
            "train_macro_f1": selected["train_macro_f1"],
            "validation_macro_f1": selected["validation_macro_f1"],
            "train_validation_gap": selected["train_validation_gap"],
        },
        "metrics": {
            "train": _evaluate(y_train, train_pred),
            "validation": _evaluate(y_validation, validation_pred),
            "test": _evaluate(y_test, test_pred),
        },
        "class_distribution": {
            str(label): {
                "train": train_distribution[str(label)],
                "validation": validation_distribution[str(label)],
                "test": test_distribution[str(label)],
            }
            for label in sorted(CLASS_TO_LABEL.values())
        },
        "cv_results": sorted(results, key=lambda result: result["validation_macro_f1"], reverse=True),
    }

    META_PATH.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(meta)
    print(json.dumps({"selected_params": selected["params"], "test": meta["metrics"]["test"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

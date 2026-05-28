# XGBoost tuning report

## Шаги настройки

1. Собран датасет из `AI/AI_data/marks_data.txt` с окном последних `5` оценок.
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

- Train macro F1: `0.479207`, accuracy: `0.515588`
- Validation macro F1: `0.403179`, accuracy: `0.47619`
- Test macro F1: `0.35968`, accuracy: `0.419048`
- Inner CV validation macro F1: `0.385602`
- Inner CV train macro F1: `0.484796`
- Train-validation gap: `0.099194`

## Class distribution

- Оценка `2`: train `167`, validation `42`, test `43`
- Оценка `3`: train `134`, validation `34`, test `34`
- Оценка `4`: train `208`, validation `53`, test `51`
- Оценка `5`: train `325`, validation `81`, test `82`

## Selected params

- `colsample_bytree`: `0.7853573712051881`
- `gamma`: `0.9367299887367345`
- `learning_rate`: `0.04219011801824916`
- `max_depth`: `2`
- `min_child_weight`: `1`
- `n_estimators`: `99`
- `reg_alpha`: `1.8493872365571256`
- `reg_lambda`: `8.896054180428829`
- `subsample`: `0.7402795697003045`

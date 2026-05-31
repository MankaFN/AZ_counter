from catboost import CatBoostRegressor, CatBoostError

class AIPredictor:
    def __init__(self, ai_data):
        self.ai_data = ai_data
        try:
            self.block_1 = CatBoostRegressor()
            self.block_1.load_model("AI_models/block_1")

            self.block_2 = CatBoostRegressor()
            self.block_2.load_model("AI_models/block_2")

            self.block_3 = CatBoostRegressor()
            self.block_3.load_model("AI_models/block_3")
        except CatBoostError:
            self.ai_retraining()

    def ai_retraining(self):
        self._ai_retraining_block_1()

        self._ai_retraining_block_2()

        self._ai_retraining_block_3()

    def _ai_retraining_block_1(self):
        X_train, X_test, y_train, y_test = self.ai_data.ai_data_block_1()
        self.block_1 = CatBoostRegressor(
            iterations=420,
            depth=2,
            learning_rate=0.04,
            l2_leaf_reg=5.0,
            bootstrap_type='Bernoulli',
            subsample=0.7,
            verbose=False,
            allow_writing_files=False,
            random_seed=200
        )

        self.block_1.fit(
            X_train, y_train,
            eval_set=(X_test, y_test),
            use_best_model=True
        )

        self.block_1.save_model("AI_models/block_1")

    def _ai_retraining_block_2(self): # 2-3
        X_train, X_test, y_train, y_test = self.ai_data.ai_data_block_2()
        self.block_2 = CatBoostRegressor(
            iterations=100,
            depth=1,
            learning_rate=0.1,
            l2_leaf_reg=5.0,
            bootstrap_type='Bernoulli',
            subsample=0.9,
            verbose=False,
            allow_writing_files=False,
            random_seed=200
        )

        self.block_2.fit(
            X_train, y_train,
            eval_set=(X_test, y_test),
            use_best_model=True
        )

        self.block_2.save_model("AI_models/block_2")

    def _ai_retraining_block_3(self): #4-5
        X_train, X_test, y_train, y_test = self.ai_data.ai_data_block_3()

        self.block_3 = CatBoostRegressor(
            iterations=600,
            depth=2,
            learning_rate=0.03,
            l2_leaf_reg=5.0,
            bootstrap_type='Bernoulli',
            subsample=0.5,
            verbose=False,
            allow_writing_files=False,
            random_seed=42
        )
        self.block_3.fit(
            X_train, y_train,
            eval_set=(X_test, y_test),
            use_best_model=True
        )

        self.block_3.save_model("AI_models/block_3")

    def predict(self, marks: dict) -> int:
        X = self.ai_data.ai_data_predict(marks)
        if self.block_1.predict(X) == 0:
            return self.block_2.predict(X)
        else:
            return self.block_3.predict(X)
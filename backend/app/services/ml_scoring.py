from __future__ import annotations

import os
import threading

import numpy as np
import pandas as pd
from tabpfn import TabPFNRegressor

_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "supplier_dataset.xlsx")
)

_FEATURES = ["price", "reliability", "delivery_time", "quantity"]


class TabPFNScoringService:
    def __init__(self) -> None:
        self._model: TabPFNRegressor | None = None
        self._lock = threading.Lock()

    def _load(self) -> None:
        df = pd.read_excel(_DATA_PATH)
        X = df[_FEATURES].values
        y = df["y_score"].values
        model = TabPFNRegressor()
        model.fit(X, y)
        self._model = model

    def predict(
        self,
        price: float,
        reliability: float,
        delivery_time: float,
        quantity: int,
    ) -> float:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._load()
        X = np.array([[price, reliability, delivery_time, quantity]], dtype=float)
        return float(self._model.predict(X)[0])  # type: ignore[union-attr]


scoring_service = TabPFNScoringService()

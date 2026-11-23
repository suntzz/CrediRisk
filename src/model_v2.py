"""Modelo final v2: híbrido HGB + las 3 redes de cv_protocol.MLP_SPECS, con y sin score.

final = lam * (w * HGB + (1 - w) * redes) + (1 - lam) * (w2 * HGB_sin_score + (1 - w2) * redes_sin_score)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

V2 = C.ARTIFACTS / "v2"


class FinalModelV2:
    def __init__(self, choice: dict):
        self.choice = choice

    # Las redes se guardan en .keras aparte; aquí solo sus rutas.
    def _nets(self, key):
        from tensorflow import keras
        if not hasattr(self, "_cache"):
            self._cache = {}
        if key not in self._cache:
            self._cache[key] = [keras.models.load_model(V2 / f) for f in self.net_files[key]]
        return self._cache[key]

    def components(self, df: pd.DataFrame) -> dict:
        out = {}
        X = self.frame.transform(df)
        out["hgb"] = np.mean([m.predict_proba(X)[:, 1] for m in self.hgbs], axis=0)
        Xn = self.frame_ns.transform(df)
        out["hgb_sin_score"] = np.mean([m.predict_proba(Xn)[:, 1] for m in self.hgbs_ns], axis=0)
        for key, pre in self.net_pre.items():
            if pre is None:
                continue
            Z = pre.transform(df)
            out[key] = np.mean([m.predict(Z, verbose=0, batch_size=8192).ravel() for m in self._nets(key)], axis=0)
        return out

    def predict_proba(self, df: pd.DataFrame, comps: dict | None = None) -> np.ndarray:
        c = comps or self.components(df)
        ch = self.choice
        w, w2 = ch["peso_hgb_con_score"], ch["peso_hgb_sin_score"]
        con = w * c["hgb"] + (1 - w) * c["redes"]
        sin = w2 * c["hgb_sin_score"] + (1 - w2) * c["redes_sin_score"] if "redes_sin_score" in c else c["hgb_sin_score"]
        lam = np.full(len(df), ch["peso_con_score"])
        if ch.get("peso_con_score_revolving") is not None:
            lam[(df["linea_negocio"] == "Revolving loans").to_numpy()] = ch["peso_con_score_revolving"]
        return lam * con + (1 - lam) * sin

    def __getstate__(self):
        s = dict(self.__dict__)
        s.pop("_cache", None)
        return s


def load():
    return joblib.load(V2 / "final_model.joblib")

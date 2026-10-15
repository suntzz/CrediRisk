"""Pruebas de Entrega 2: particiones, fuga de informacion, codificadores, faltantes, metricas e inferencia.

Ejecutar: .venv/Scripts/python.exe -m pytest tests -q
Las pruebas marcadas `tf` cargan TensorFlow (~2 min en Windows): -m "not tf" para omitirlas.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import log_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import config as C  # noqa: E402
from phase4_common import Encoder, load_raw, metrics, paired_bootstrap  # noqa: E402


@pytest.fixture(scope="module")
def raw():
    return load_raw()


@pytest.fixture(scope="module")
def ple_enc(raw):
    df, y, tr, va, te = raw
    return Encoder("ple", 16).fit(df.iloc[tr])


# --- particiones ------------------------------------------------------------------------------
def test_split_sizes_disjoint_and_frozen(raw):
    df, y, tr, va, te = raw
    assert (len(tr), len(va), len(te)) == (34755, 7447, 7448)
    assert not (set(tr) & set(va)) and not (set(tr) & set(te)) and not (set(va) & set(te))
    d = np.load(C.ARTIFACTS / "splits.npz")
    assert (te == d["idx_test"]).all()
    assert (y[va] == d["y_val"]).all() and (y[tr] == d["y_train"]).all()


def test_split_stratified(raw):
    df, y, tr, va, te = raw
    for idx in (tr, va, te):
        assert abs(y[idx].mean() - y.mean()) < 0.002


# --- fuga de informacion ------------------------------------------------------------------------
def test_leaky_columns_excluded(ple_enc):
    names = ple_enc.pre.feature_names
    assert "INCUMPLIO_PAGO" not in names and "id_solicitud" not in names and C.TARGET not in names
    assert "INCUMPLIO_PAGO" in C.DROP_COLS


def test_transform_does_not_read_target_or_leaky_column(raw, ple_enc):
    df, y, tr, va, te = raw
    part = df.iloc[va[:500]].copy()
    X1 = ple_enc.transform(part)
    part[C.TARGET] = 1 - part[C.TARGET]
    part["INCUMPLIO_PAGO"] = 1 - part["INCUMPLIO_PAGO"]
    assert np.array_equal(X1, ple_enc.transform(part))
    assert np.array_equal(X1, ple_enc.transform(part.drop(columns=[C.TARGET, "INCUMPLIO_PAGO"])))


def test_encoder_fitted_only_on_train(raw):
    """Alterar filas de Val/Test no cambia ningun parametro aprendido (cuantiles, escalado, tramos)."""
    df, y, tr, va, te = raw
    e1 = Encoder("ple_tree", 16).fit(df.iloc[tr])
    df2 = df.copy()
    rest = np.r_[va, te]
    df2.loc[df2.index[rest], "score_crediticio"] = 9999.0
    df2.loc[df2.index[rest], C.TARGET] = 1 - df2.loc[df2.index[rest], C.TARGET]
    e2 = Encoder("ple_tree", 16).fit(df2.iloc[tr])
    assert all(np.array_equal(a, b) for a, b in zip(e1.edges, e2.edges))
    assert np.allclose(e1.pre.scaler.mean_, e2.pre.scaler.mean_)


# --- codificaciones y faltantes ---------------------------------------------------------------------
def test_ple_values_bounded_and_finite(raw, ple_enc):
    df, y, tr, va, te = raw
    X = ple_enc.transform(df.iloc[va])
    assert np.isfinite(X).all()
    ple = X[:, 44:]
    assert ple.min() >= 0.0 and ple.max() <= 1.0
    assert X.shape[1] == 44 + sum(b - a for a, b in ple_enc.slices)


def test_missing_values_are_handled(raw, ple_enc):
    df, y, tr, va, te = raw
    part = df.iloc[va[:50]].copy()
    for c in C.FLAG_COLS + ["score_crediticio", "dias_maximo_mora"]:
        part[c] = np.nan
    X = ple_enc.transform(part)
    assert np.isfinite(X).all()
    names = ple_enc.pre.feature_names
    for c in C.FLAG_COLS:  # el indicador de faltante debe quedar activo (estandarizado > 0)
        assert (X[:, names.index(c + "_nan")] > 0).all()


def test_nan_zero_zeroes_ple_block_only_for_missing(raw):
    df, y, tr, va, te = raw
    enc = Encoder("ple", 16, nan_zero=True).fit(df.iloc[tr])
    part = df.iloc[va[:100]].copy()
    part.loc[part.index[:10], "antiguedad_laboral_anios"] = np.nan
    X = enc.transform(part)
    j = enc.base.index("antiguedad_laboral_anios")
    a, b = enc.slices[[k for k, e in enumerate(enc.edges) if len(e) > 2].index(j)]
    assert (X[:10, a:b] == 0).all()
    assert (X[10:, a:b].sum(1) > 0).any()


def test_phase4_encoder_backward_compatible():
    """El codificador serializado en Fase 4 (sin atributo nan_zero) sigue transformando igual."""
    import joblib

    enc = joblib.load(C.ARTIFACTS / "phase4" / "encoder_phase4.joblib")
    assert not hasattr(enc, "nan_zero")
    df, y, tr, va, te = load_raw()
    X = enc.transform(df.iloc[va[:200]])
    assert X.shape == (200, 268) and np.isfinite(X).all()


# --- metricas y estadistica ---------------------------------------------------------------------
def test_metrics_logloss_matches_sklearn():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 1000)
    p = rng.uniform(0.01, 0.99, 1000)
    assert metrics(y, p)["LogLoss"] == pytest.approx(log_loss(y, p), abs=1e-10)


def test_metrics_clip_avoids_infinite_loss():
    y = np.array([0, 1, 1, 0])
    p = np.array([0.0, 1.0, 0.0, 1.0])
    ll = metrics(y, p)["LogLoss"]
    assert np.isfinite(ll) and ll == pytest.approx(-np.log(1e-7) / 2, rel=1e-3)


def test_paired_bootstrap_identical_and_better():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 2000).astype(float)
    p = np.full(2000, 0.5)
    d, lo, hi, _ = paired_bootstrap(y, p, p)
    assert d == lo == hi == 0
    better = np.where(y == 1, 0.7, 0.3)
    d, lo, hi, pge0 = paired_bootstrap(y, better, p)
    assert d < 0 and hi < 0 and pge0 == 0


# --- inferencia (TensorFlow) ----------------------------------------------------------------------
@pytest.mark.tf
@pytest.mark.parametrize("manifest", ["phase4", "entrega2"])
def test_predict_output_format(manifest):
    from predict import load_model_and_preprocessor, score

    p = C.ARTIFACTS / manifest / "final_manifest.json"
    if not p.exists():
        pytest.skip(f"sin modelo final en {p.parent.name}")
    enc, models = load_model_and_preprocessor(**{manifest: True})
    df = pd.DataFrame([json.loads((ROOT / "data" / "ejemplo_solicitante.json").read_text())])
    out = score(df, enc, models, use_ensemble=True)
    assert list(out.columns) == ["id_solicitud", "probabilidad_apto", "probabilidad_no_apto", "resultado"]
    pa = out.probabilidad_apto.iloc[0]
    assert 0 <= pa <= 1 and out.probabilidad_no_apto.iloc[0] == pytest.approx(1 - pa, abs=1e-3)
    assert out.resultado.iloc[0] in ("APTO", "NO APTO")

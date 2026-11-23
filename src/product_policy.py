"""Política de umbral por línea de negocio.

La probabilidad pertenece al modelo neuronal; el umbral es una regla de decisión
operativa. Mantenerlas separadas evita confundir calibración, entrenamiento y
política comercial.
"""
from __future__ import annotations

import json
from typing import Any

import config as C


POLICY_PATH = C.ARTIFACTS / "product_threshold_policy.json"


def default_policy() -> dict[str, Any]:
    return {
        "version": 1,
        "status": "fallback",
        "selection_split": "not_available",
        "objective": "balanced_accuracy",
        "default_threshold": float(C.THRESHOLD),
        "thresholds": {},
        "unsupported_products": {
            "Mortgage loans": "No hay registros etiquetados de crédito hipotecario en el dataset actual."
        },
    }


def load_policy() -> dict[str, Any]:
    if not POLICY_PATH.exists():
        return default_policy()
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_policy()
    merged = default_policy()
    merged.update(policy)
    return merged


def threshold_for_product(product: str, policy: dict[str, Any] | None = None) -> float:
    policy = policy or load_policy()
    item = policy.get("thresholds", {}).get(product, {})
    return float(item.get("threshold", policy["default_threshold"]))


def is_supported_product(product: str, policy: dict[str, Any] | None = None) -> bool:
    policy = policy or load_policy()
    return product not in policy.get("unsupported_products", {})

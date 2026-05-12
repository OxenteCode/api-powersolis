"""Runtime configuration for the HTTP API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ApiSettings:
    """Settings read from environment variables."""

    modelo_hotspot_path: Path
    modelo_clustering_path: Path | None
    tensao_ensaio_V: float
    vida_ref_anos: float
    temp_ref_C: float
    p_montsinger: float


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default.resolve()
    return Path(value).expanduser().resolve()


def _optional_path_from_env(name: str) -> Path | None:
    value = os.getenv(name)
    if not value:
        return None
    return Path(value).expanduser().resolve()


def _float_from_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float.") from exc


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    """Return cached API settings."""

    return ApiSettings(
        modelo_hotspot_path=_path_from_env(
            "POWER_SOLIS_MODEL_HOTSPOT",
            PROJECT_ROOT / "models" / "modelo_hotspot.pkl",
        ),
        modelo_clustering_path=_optional_path_from_env(
            "POWER_SOLIS_MODEL_CLUSTERING"
        ),
        tensao_ensaio_V=_float_from_env("POWER_SOLIS_TENSAO_ENSAIO_V", 10_000.0),
        vida_ref_anos=_float_from_env("POWER_SOLIS_VIDA_REF_ANOS", 25.0),
        temp_ref_C=_float_from_env("POWER_SOLIS_TEMP_REF_C", 85.0),
        p_montsinger=_float_from_env("POWER_SOLIS_P_MONTSINGER", 8.0),
    )

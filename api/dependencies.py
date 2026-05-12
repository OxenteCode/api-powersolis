"""FastAPI dependencies and service objects."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastapi import HTTPException, status

from api.config import ApiSettings, get_settings
from pipeline.data_models import DiagnosticResult, MedicaoBruta
from pipeline.diagnostic_pipeline import DiagnosticPipeline


@dataclass
class DiagnosticService:
    """Thin service wrapper around the diagnostic pipeline."""

    settings: ApiSettings
    pipeline: DiagnosticPipeline

    def executar(self, medicao: MedicaoBruta) -> DiagnosticResult:
        """Run one diagnostic."""

        return self.pipeline.executar(medicao)

    def readiness(self) -> dict[str, str | None]:
        """Return service readiness information."""

        return {
            "status": "ready",
            "modelo_hotspot": str(self.settings.modelo_hotspot_path),
            "modelo_clustering": (
                str(self.settings.modelo_clustering_path)
                if self.settings.modelo_clustering_path
                else None
            ),
        }


@lru_cache(maxsize=1)
def _build_diagnostic_service() -> DiagnosticService:
    settings = get_settings()
    pipeline = DiagnosticPipeline(
        caminho_modelo_hotspot=str(settings.modelo_hotspot_path),
        caminho_modelo_clustering=(
            str(settings.modelo_clustering_path)
            if settings.modelo_clustering_path
            else None
        ),
        tensao_ensaio_V=settings.tensao_ensaio_V,
        vida_ref_anos=settings.vida_ref_anos,
        temp_ref_C=settings.temp_ref_C,
        p_montsinger=settings.p_montsinger,
    )
    return DiagnosticService(settings=settings, pipeline=pipeline)


def get_diagnostic_service() -> DiagnosticService:
    """Return a cached diagnostic service or raise an API-friendly error."""

    try:
        return _build_diagnostic_service()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

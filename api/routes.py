"""HTTP routes for diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import DiagnosticService, get_diagnostic_service
from api.schemas import (
    DiagnosticResponse,
    LoteDiagnosticoRequest,
    LoteDiagnosticoResponse,
    MedicaoRequest,
    ReadyResponse,
)


router = APIRouter()


@router.get("/ready", response_model=ReadyResponse)
def ready(
    service: DiagnosticService = Depends(get_diagnostic_service),
) -> ReadyResponse:
    """Check whether the diagnostic service can load its models."""

    return ReadyResponse(**service.readiness())


@router.post("/diagnosticos", response_model=DiagnosticResponse)
def diagnosticar(
    payload: MedicaoRequest,
    service: DiagnosticService = Depends(get_diagnostic_service),
) -> DiagnosticResponse:
    """Run a diagnostic for one measurement."""

    try:
        result = service.executar(payload.to_domain())
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return DiagnosticResponse.from_domain(result)


@router.post("/diagnosticos/lote", response_model=LoteDiagnosticoResponse)
def diagnosticar_lote(
    payload: LoteDiagnosticoRequest,
    service: DiagnosticService = Depends(get_diagnostic_service),
) -> LoteDiagnosticoResponse:
    """Run diagnostics for multiple measurements."""

    resultados: list[DiagnosticResponse] = []
    for index, medicao in enumerate(payload.medicoes):
        try:
            result = service.executar(medicao.to_domain())
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"item_index": index, "message": str(exc)},
            ) from exc
        resultados.append(DiagnosticResponse.from_domain(result))

    return LoteDiagnosticoResponse(
        total=len(resultados),
        resultados=resultados,
    )

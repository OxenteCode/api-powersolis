"""Pydantic schemas used by the HTTP API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from pipeline.data_models import DiagnosticResult, MedicaoBruta


class MedicaoRequest(BaseModel):
    """Input payload for one TC measurement."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_equipamento": "TC-550kV-001",
                "tangente_perdas": 0.7,
                "corrente": 2000.0,
                "temperatura_ambiente": 30.0,
                "ponto_quente_externo": 45.0,
                "horas_operacao": 87600.0,
                "tensao_nominal": 550.0,
            }
        }
    )

    tangente_perdas: float = Field(..., ge=0.0, le=10.0)
    corrente: float = Field(..., ge=0.0)
    temperatura_ambiente: float = Field(..., ge=-50.0, le=80.0)
    ponto_quente_externo: float = Field(..., ge=-50.0, le=250.0)
    horas_operacao: float = Field(..., ge=0.0)
    tensao_nominal: float = Field(..., gt=0.0)
    id_equipamento: Optional[str] = None

    def to_domain(self) -> MedicaoBruta:
        """Convert request payload to the domain dataclass."""

        return MedicaoBruta(
            tangente_perdas=self.tangente_perdas,
            corrente=self.corrente,
            temperatura_ambiente=self.temperatura_ambiente,
            ponto_quente_externo=self.ponto_quente_externo,
            horas_operacao=self.horas_operacao,
            tensao_nominal=self.tensao_nominal,
            id_equipamento=self.id_equipamento,
        )


class DiagnosticResponse(BaseModel):
    """Output payload for one diagnostic result."""

    id_equipamento: Optional[str] = None
    temperatura_hotspot_inferida_C: float
    fator_aceleracao: float
    expectativa_vida_anos: float
    horas_equivalentes_ref: float
    percentual_vida_perdida: float
    estado_operacional: str
    score_fuzzy: float
    cluster_id: int

    @classmethod
    def from_domain(cls, result: DiagnosticResult) -> "DiagnosticResponse":
        """Convert the domain dataclass to an API response."""

        return cls(
            id_equipamento=result.id_equipamento,
            temperatura_hotspot_inferida_C=result.temperatura_hotspot_inferida_C,
            fator_aceleracao=result.fator_aceleracao,
            expectativa_vida_anos=result.expectativa_vida_anos,
            horas_equivalentes_ref=result.horas_equivalentes_ref,
            percentual_vida_perdida=result.percentual_vida_perdida,
            estado_operacional=result.estado_operacional,
            score_fuzzy=result.score_fuzzy,
            cluster_id=result.cluster_id,
        )


class LoteDiagnosticoRequest(BaseModel):
    """Input payload for batch diagnostics."""

    medicoes: List[MedicaoRequest] = Field(..., min_length=1, max_length=1000)


class LoteDiagnosticoResponse(BaseModel):
    """Output payload for batch diagnostics."""

    total: int
    resultados: List[DiagnosticResponse]


class ReadyResponse(BaseModel):
    """Readiness payload."""

    status: str
    modelo_hotspot: str
    modelo_clustering: Optional[str]

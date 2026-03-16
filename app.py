"""API mínima para expor funções de modelagem como endpoints HTTP.

Use `uvicorn app:app --reload` para rodar em desenvolvimento.

Endpoints principais:
- GET  /health
- POST /inferir-hotspot  -> retorna temperatura de hotspot estimada
- POST /perda-vida      -> retorna perda de vida útil estimada
"""

from fastapi import FastAPI
from pydantic import BaseModel

from modeling.model_hotspot import inferir_temperatura, treinar_e_salvar_modelo
from modeling.model_aging import calcular_perda_vida_util_base2

app = FastAPI(
    title="Power Solis API",
    description="API para inferência de hotspot e cálculo de perda de vida útil de transformadores.",
    version="0.1.0",
)


class HotspotRequest(BaseModel):
    tangente_perdas: float
    corrente_primario: float
    temperatura_ambiente: float


class VidaUtilRequest(BaseModel):
    temperatura_hotspot: float
    horas_operacao: float
    temp_ref: float = 85.0
    vida_ref_anos: float = 25.0
    p: float = 8.0


@app.get("/health")
def health() -> dict:
    """Endpoint de sanity check."""
    return {"status": "ok"}


@app.post("/inferir-hotspot")
def inferir_hotspot(data: HotspotRequest) -> dict:
    """Inferência da temperatura de hotspot com base nos parâmetros de entrada."""
    try:
        temperatura = inferir_temperatura(
            tangente_perdas=data.tangente_perdas,
            corrente_primario=data.corrente_primario,
            temperatura_ambiente=data.temperatura_ambiente,
        )
    except FileNotFoundError:
        # Treina e salva um modelo rápido se ainda não existir.
        treinar_e_salvar_modelo()
        temperatura = inferir_temperatura(
            tangente_perdas=data.tangente_perdas,
            corrente_primario=data.corrente_primario,
            temperatura_ambiente=data.temperatura_ambiente,
        )

    return {
        "temperatura_hotspot": float(temperatura),
        "entrada": data.dict(),
    }


@app.post("/perda-vida")
def perda_vida(data: VidaUtilRequest) -> dict:
    """Cálculo da perda de vida útil usando a regra de base 2."""
    resultado = calcular_perda_vida_util_base2(
        temperatura_hotspot=data.temperatura_hotspot,
        horas_operacao=data.horas_operacao,
        temp_ref=data.temp_ref,
        vida_ref_anos=data.vida_ref_anos,
        p=data.p,
    )

    return {
        "resultado": resultado,
        "entrada": data.dict(),
    }

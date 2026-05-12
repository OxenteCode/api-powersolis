from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_diagnostico_individual_returns_result():
    payload = {
        "id_equipamento": "TC-550kV-001",
        "tangente_perdas": 0.7,
        "corrente": 2000.0,
        "temperatura_ambiente": 30.0,
        "ponto_quente_externo": 45.0,
        "horas_operacao": 87600.0,
        "tensao_nominal": 550.0,
    }

    response = client.post("/api/v1/diagnosticos", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["id_equipamento"] == "TC-550kV-001"
    assert body["temperatura_hotspot_inferida_C"] > 0
    assert body["expectativa_vida_anos"] > 0
    assert body["estado_operacional"] in {"Novo", "Atencao", "Atenção", "Perigo"}

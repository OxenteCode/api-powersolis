#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/validar_pipeline.py
===========================
Script de validação end-to-end do pipeline de diagnóstico de TCs.
Execute a partir da raiz do projeto:

    python scripts/validar_pipeline.py

Não modifica dados, apenas lê e processa.
"""

import sys
import os

# Garante que o root do projeto está no path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

VERDE  = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
RESET  = "\033[0m"
NEGRITO = "\033[1m"

def ok(msg):   print(f"  {VERDE}✔{RESET}  {msg}")
def warn(msg): print(f"  {AMARELO}⚠{RESET}  {msg}")
def fail(msg): print(f"  {VERMELHO}✘{RESET}  {msg}")


# ============================================================
# ETAPA 0 — Imports
# ============================================================
print(f"\n{NEGRITO}{'='*55}{RESET}")
print(f"{NEGRITO}  VALIDAÇÃO DO PIPELINE DE DIAGNÓSTICO DE TCs{RESET}")
print(f"{NEGRITO}{'='*55}{RESET}\n")

print("[ 0 ] Verificando imports...")
try:
    from modeling import model_hotspot
    ok("modeling.model_hotspot")
except Exception as e:
    fail(f"modeling.model_hotspot — {e}"); sys.exit(1)

try:
    from modeling import model_aging
    ok("modeling.model_aging")
except Exception as e:
    fail(f"modeling.model_aging — {e}"); sys.exit(1)

try:
    from preprocessing.feature_extraction import extrair_features, validar_medicao
    ok("preprocessing.feature_extraction")
except Exception as e:
    fail(f"preprocessing.feature_extraction — {e}"); sys.exit(1)

try:
    from pipeline.data_models import MedicaoBruta, FeatureVector, DiagnosticResult
    ok("pipeline.data_models")
except Exception as e:
    fail(f"pipeline.data_models — {e}"); sys.exit(1)

try:
    from classification.clustering import TCClusteringModel
    ok("classification.clustering")
except Exception as e:
    fail(f"classification.clustering — {e}"); sys.exit(1)

try:
    from classification.fuzzy_classifier import FuzzyTCClassifier
    ok("classification.fuzzy_classifier")
except Exception as e:
    fail(f"classification.fuzzy_classifier — {e}"); sys.exit(1)

try:
    from pipeline.diagnostic_pipeline import DiagnosticPipeline
    ok("pipeline.diagnostic_pipeline")
except Exception as e:
    fail(f"pipeline.diagnostic_pipeline — {e}"); sys.exit(1)

# ============================================================
# ETAPA 1 — feature_extraction
# ============================================================
print(f"\n[ 1 ] Testando feature_extraction...")
try:
    m = MedicaoBruta(
        tangente_perdas=0.70, corrente=2000.0,
        temperatura_ambiente=30.0, ponto_quente_externo=45.0,
        horas_operacao=87_600.0, tensao_nominal=550.0,
        id_equipamento="TC-TEST-001"
    )
    fv = extrair_features(m)
    assert fv.capacitancia > 0,   "capacitância deve ser positiva"
    assert fv.perda_dieletrica > 0, "perda dielétrica deve ser positiva"
    ok(f"FeatureVector OK — C={fv.capacitancia:.3e} F, P={fv.perda_dieletrica:.3e} W")
except Exception as e:
    fail(f"feature_extraction — {e}"); sys.exit(1)

try:
    m_inv = MedicaoBruta(-1.0, 2000.0, 30.0, 45.0, 0.0, 550.0)
    validar_medicao(m_inv)
    fail("validar_medicao deveria ter levantado ValueError para tg negativa")
except ValueError:
    ok("validar_medicao rejeita tg negativa corretamente")

# ============================================================
# ETAPA 2 — model_hotspot (treino e inferência)
# ============================================================
print(f"\n[ 2 ] Testando model_hotspot (treino + inferência)...")
CAMINHO_ODS = os.path.join(ROOT, "modeling", "Dados_Lab_550.ods")
CAMINHO_PKL = os.path.join(ROOT, "models", "modelo_hotspot_validacao.pkl")
os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)

try:
    metricas = model_hotspot.treinar_e_salvar_modelo(
        caminho_dados=CAMINHO_ODS,
        caminho_arquivo=CAMINHO_PKL,
        grau=2,
    )
    ok(f"Modelo treinado — RMSE≈{metricas['rmse']:.2f}°C, R²adj≈{metricas['r2_adj']:.4f}")
except Exception as e:
    fail(f"model_hotspot.treinar — {e}"); sys.exit(1)

try:
    from inference.temperature_inference import HotspotInferenceModel
    modelo_inf = HotspotInferenceModel(CAMINHO_PKL)
    t = modelo_inf.inferir(fv)
    assert 30 < t < 200, f"Temperatura fora do range esperado: {t}"
    ok(f"Hotspot inferido = {t:.2f} °C")
except Exception as e:
    fail(f"HotspotInferenceModel — {e}"); sys.exit(1)

# ============================================================
# ETAPA 3 — model_aging
# ============================================================
print(f"\n[ 3 ] Testando model_aging...")
try:
    res = model_aging.calcular_perda_vida_util_base2(
        temperatura_hotspot=t,
        horas_operacao=87_600.0,
    )
    vida = res["expectativa_vida_atual_anos"]
    faa  = res["fator_aceleracao"]
    assert vida > 0, "Vida útil deve ser positiva"
    ok(f"Vida útil = {vida:.2f} anos | FAA = {faa:.2f}x")
except Exception as e:
    fail(f"model_aging — {e}"); sys.exit(1)

# ============================================================
# ETAPA 4a — clustering
# ============================================================
print(f"\n[ 4a ] Testando clustering (fallback sem treino)...")
try:
    clust = TCClusteringModel()
    cluster_id = DiagnosticPipeline._cluster_fallback(0.70, t, vida)
    ok(f"Cluster fallback = {cluster_id} (0=Novo, 1=Atenção, 2=Perigo)")
except Exception as e:
    fail(f"clustering fallback — {e}"); sys.exit(1)

# ============================================================
# ETAPA 4b — fuzzy classifier
# ============================================================
print(f"\n[ 4b ] Testando FuzzyTCClassifier...")
try:
    clf = FuzzyTCClassifier()
    estado, score = clf.classificar(
        tangente_perdas=fv.tangente_perdas,
        temperatura_hotspot_C=t,
        expectativa_vida_anos=vida,
        fator_aceleracao=faa,
    )
    ok(f"Estado = '{estado}' | Score fuzzy = {score:.1f}/100")
except Exception as e:
    fail(f"FuzzyTCClassifier — {e}"); sys.exit(1)

# ============================================================
# ETAPA 5 — Pipeline completo (3 cenários)
# ============================================================
print(f"\n[ 5 ] Testando DiagnosticPipeline end-to-end (3 cenários)...")

cenarios = [
    ("Equipamento Novo",   MedicaoBruta(0.25, 1500.0, 22.0, 25.0, 8_760.0,   550.0, "TC-NOVO")),
    ("Atenção",            MedicaoBruta(0.70, 2000.0, 30.0, 45.0, 87_600.0,  550.0, "TC-ATENCAO")),
    ("Perigo",             MedicaoBruta(1.10, 2000.0, 38.0, 70.0, 175_200.0, 550.0, "TC-PERIGO")),
]

try:
    pipeline = DiagnosticPipeline(caminho_modelo_hotspot=CAMINHO_PKL)
    for nome, med in cenarios:
        r = pipeline.executar(med)
        cor = VERDE if r.estado_operacional == "Novo" else (
              AMARELO if r.estado_operacional == "Atenção" else VERMELHO)
        print(f"  {cor}●{RESET} [{nome:18s}]  Hotspot={r.temperatura_hotspot_inferida_C:.1f}°C  "
              f"Vida={r.expectativa_vida_anos:.1f}a  "
              f"Estado={cor}{r.estado_operacional}{RESET}  Score={r.score_fuzzy:.1f}")
except Exception as e:
    fail(f"DiagnosticPipeline — {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# ============================================================
# RESULTADO FINAL
# ============================================================
print(f"\n{NEGRITO}{VERDE}{'='*55}{RESET}")
print(f"{NEGRITO}{VERDE}  TODAS AS ETAPAS VALIDADAS COM SUCESSO ✔{RESET}")
print(f"{NEGRITO}{VERDE}{'='*55}{RESET}\n")

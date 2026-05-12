# -*- coding: utf-8 -*-
"""
main.py — Ponto de entrada do sistema de diagnóstico de TCs.

Demonstra o fluxo completo:
  1. Treino do modelo de hotspot (regressão polinomial)
  2. Execução do pipeline sobre uma medição de exemplo
  3. Impressão do resultado de diagnóstico
"""

import os
import sys

# Garante que a raiz do projeto está no PYTHONPATH ao rodar diretamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modeling import model_hotspot
from pipeline.diagnostic_pipeline import DiagnosticPipeline
from pipeline.data_models import MedicaoBruta

# ---------------------------------------------------------------------------
# CONFIGURAÇÕES — ajuste os caminhos conforme o dataset disponível
# ---------------------------------------------------------------------------

# Caminho para o arquivo .ods com dados de laboratório
CAMINHO_DADOS_ODS = os.path.join(
    os.path.dirname(__file__), "modeling", "Dados_Lab_550.ods"
)

# Caminho onde o modelo de hotspot treinado será salvo/carregado
CAMINHO_MODELO_PKL = os.path.join(
    os.path.dirname(__file__), "models", "modelo_hotspot.pkl"
)


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def garantir_modelo_treinado(caminho_dados: str, caminho_modelo: str) -> None:
    """
    Treina e salva o modelo de hotspot se ainda não existir.
    Seleciona automaticamente o melhor grau polinomial (1–4).
    """
    if os.path.isfile(caminho_modelo):
        print(f"[✔] Modelo de hotspot encontrado em: '{caminho_modelo}'")
        return

    print("[→] Modelo não encontrado. Iniciando treinamento...")
    os.makedirs(os.path.dirname(caminho_modelo), exist_ok=True)

    resultado = model_hotspot.selecionar_melhor_grau(
        caminho_dados=caminho_dados,
        graus=[1, 2, 3, 4],
        metrica_principal="rmse",
        verbose=True,
    )
    melhor_grau = resultado["melhor_grau"]

    model_hotspot.treinar_e_salvar_modelo(
        caminho_dados=caminho_dados,
        caminho_arquivo=caminho_modelo,
        grau=melhor_grau,
    )
    print(f"[✔] Modelo grau {melhor_grau} salvo em: '{caminho_modelo}'")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Executa o pipeline de diagnóstico sobre uma medição de exemplo.

    Fluxo
    -----
    1. Garante que o modelo de hotspot está treinado e salvo.
    2. Instancia o DiagnosticPipeline.
    3. Cria uma MedicaoBruta de exemplo.
    4. Executa o pipeline e imprime o DiagnosticResult.
    """
    print("=" * 60)
    print("  SISTEMA DE DIAGNÓSTICO DE TCs — PeD Power Solis")
    print("=" * 60)

    # 1. Garantir modelo treinado
    garantir_modelo_treinado(CAMINHO_DADOS_ODS, CAMINHO_MODELO_PKL)

    # 2. Instanciar pipeline
    pipeline = DiagnosticPipeline(
        caminho_modelo_hotspot=CAMINHO_MODELO_PKL,
        vida_ref_anos=25.0,   # Vida de referência: 25 anos
        temp_ref_C=85.0,      # Temperatura de referência: 85 °C (IEC)
        p_montsinger=8.0,     # Duplicação a cada 8 °C
    )

    # 3. Medição de exemplo — TC 550 kV em condição de Atenção
    medicao = MedicaoBruta(
        tangente_perdas=0.70,        # Tg(δ) = 0,70 %  → zona de Atenção
        corrente=2000.0,             # Corrente primária em A
        temperatura_ambiente=30.0,   # °C
        ponto_quente_externo=45.0,   # °C (medido por câmera IR)
        horas_operacao=87_600.0,     # ≈ 10 anos de operação contínua
        tensao_nominal=550.0,        # kV
        id_equipamento="TC-550kV-001",
    )

    print("\n[→] Executando pipeline de diagnóstico...")
    resultado = pipeline.executar(medicao)

    # 4. Exibir resultado
    print("\n" + "=" * 60)
    print("  RESULTADO DO DIAGNÓSTICO")
    print("=" * 60)
    print(resultado)
    print("=" * 60)

    # Exemplo adicional: cenário crítico (Perigo)
    print("\n[→] Testando cenário crítico (Tg=1,1%, Hotspot elevado)...")
    medicao_perigo = MedicaoBruta(
        tangente_perdas=1.10,
        corrente=2000.0,
        temperatura_ambiente=38.0,
        ponto_quente_externo=70.0,
        horas_operacao=175_200.0,    # ≈ 20 anos
        tensao_nominal=550.0,
        id_equipamento="TC-550kV-002",
    )
    resultado_perigo = pipeline.executar(medicao_perigo)
    print("\n" + "=" * 60)
    print("  RESULTADO DO DIAGNÓSTICO — CENÁRIO CRÍTICO")
    print("=" * 60)
    print(resultado_perigo)
    print("=" * 60)

    # Exemplo: cenário novo
    print("\n[→] Testando cenário de equipamento novo...")
    medicao_novo = MedicaoBruta(
        tangente_perdas=0.25,
        corrente=1500.0,
        temperatura_ambiente=22.0,
        ponto_quente_externo=25.0,
        horas_operacao=8_760.0,      # ≈ 1 ano
        tensao_nominal=550.0,
        id_equipamento="TC-550kV-003",
    )
    resultado_novo = pipeline.executar(medicao_novo)
    print("\n" + "=" * 60)
    print("  RESULTADO DO DIAGNÓSTICO — EQUIPAMENTO NOVO")
    print("=" * 60)
    print(resultado_novo)
    print("=" * 60)


if __name__ == "__main__":
    main()

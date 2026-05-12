# -*- coding: utf-8 -*-
"""
preprocessing/feature_extraction.py — Etapa ① do pipeline.
Extração e engenharia de atributos a partir de medições brutas de TCs.
"""

from __future__ import annotations

import numpy as np
from pipeline.data_models import MedicaoBruta, FeatureVector

FREQUENCIA_REDE_HZ: float = 60.0


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------------------------

def calcular_capacitancia(
    tg: float,
    rms_corrente: float,
    rms_tensao: float,
) -> float:
    """
    Calcula a capacitância do isolamento: C = I / (2π·f·V·√(1 + tg²)).

    Parâmetros
    ----------
    tg : float
        Tangente de perdas em percentual (%). Convertida internamente para decimal.
    rms_corrente : float
        Corrente de fuga RMS em Ampères (A).
    rms_tensao : float
        Tensão de ensaio RMS em Volts (V).

    Retorna
    -------
    float
        Capacitância em Farads (F).

    Levanta
    -------
    ValueError
        Se ``rms_tensao`` for zero.
    """
    if rms_tensao == 0.0:
        raise ValueError("rms_tensao não pode ser zero.")
    tg_dec = tg / 100.0
    return rms_corrente / (2 * np.pi * FREQUENCIA_REDE_HZ * rms_tensao * np.sqrt(1 + tg_dec ** 2))


def calcular_perda_dieletrica(
    tg: float,
    rms_corrente: float,
    rms_tensao: float,
) -> float:
    """
    Calcula a perda dielétrica: P = 2π·f·C·V²·tg.

    Parâmetros
    ----------
    tg : float
        Tangente de perdas em percentual (%).
    rms_corrente : float
        Corrente de fuga RMS em Ampères (A).
    rms_tensao : float
        Tensão de ensaio RMS em Volts (V).

    Retorna
    -------
    float
        Perda dielétrica em Watts (W).
    """
    tg_dec = tg / 100.0
    C = calcular_capacitancia(tg, rms_corrente, rms_tensao)
    return 2 * np.pi * FREQUENCIA_REDE_HZ * C * (rms_tensao ** 2) * tg_dec


def validar_medicao(medicao: MedicaoBruta) -> None:
    """
    Valida os campos de uma MedicaoBruta contra intervalos fisicamente plausíveis.

    Parâmetros
    ----------
    medicao : MedicaoBruta
        Objeto com os dados brutos a validar.

    Levanta
    -------
    TypeError
        Se algum campo não for numérico.
    ValueError
        Se algum campo estiver fora do intervalo esperado.
    """
    campos = {
        "tangente_perdas": medicao.tangente_perdas,
        "corrente": medicao.corrente,
        "temperatura_ambiente": medicao.temperatura_ambiente,
        "ponto_quente_externo": medicao.ponto_quente_externo,
        "horas_operacao": medicao.horas_operacao,
        "tensao_nominal": medicao.tensao_nominal,
    }
    for nome, valor in campos.items():
        if not isinstance(valor, (int, float)):
            raise TypeError(f"Campo '{nome}' deve ser numérico, recebido: {type(valor)}")

    if not (0.0 <= medicao.tangente_perdas <= 10.0):
        raise ValueError(f"tangente_perdas fora de [0, 10]: {medicao.tangente_perdas}")
    if medicao.corrente < 0:
        raise ValueError(f"corrente não pode ser negativa: {medicao.corrente}")
    if not (-50.0 <= medicao.temperatura_ambiente <= 80.0):
        raise ValueError(f"temperatura_ambiente fora de [-50, 80]: {medicao.temperatura_ambiente}")
    if not (-50.0 <= medicao.ponto_quente_externo <= 250.0):
        raise ValueError(f"ponto_quente_externo fora de [-50, 250]: {medicao.ponto_quente_externo}")
    if medicao.horas_operacao < 0:
        raise ValueError(f"horas_operacao não pode ser negativa: {medicao.horas_operacao}")
    if medicao.tensao_nominal <= 0:
        raise ValueError(f"tensao_nominal deve ser positiva: {medicao.tensao_nominal}")


# ---------------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

def extrair_features(
    medicao: MedicaoBruta,
    tensao_ensaio_V: float = 10_000.0,
) -> FeatureVector:
    """
    Converte uma MedicaoBruta em um FeatureVector enriquecido.

    Fluxo: valida → calcula capacitância → calcula perda dielétrica → monta FeatureVector.

    Parâmetros
    ----------
    medicao : MedicaoBruta
        Dados brutos do banco de dados.
    tensao_ensaio_V : float, opcional
        Tensão de ensaio em Volts usada para calcular C e P. Padrão: 10 000 V.

    Retorna
    -------
    FeatureVector
        Vetor de atributos pronto para as etapas seguintes do pipeline.

    Levanta
    -------
    ValueError
        Se a medição contiver dados inválidos.

    Exemplo
    -------
    >>> from pipeline.data_models import MedicaoBruta
    >>> m = MedicaoBruta(0.7, 2000.0, 30.0, 45.0, 87_600.0, 550.0)
    >>> fv = extrair_features(m)
    >>> print(fv.capacitancia)
    """
    validar_medicao(medicao)

    capacitancia = calcular_capacitancia(
        tg=medicao.tangente_perdas,
        rms_corrente=medicao.corrente,
        rms_tensao=tensao_ensaio_V,
    )
    perda_dieletrica = calcular_perda_dieletrica(
        tg=medicao.tangente_perdas,
        rms_corrente=medicao.corrente,
        rms_tensao=tensao_ensaio_V,
    )

    return FeatureVector(
        tangente_perdas=medicao.tangente_perdas,
        corrente=medicao.corrente,
        temperatura_ambiente=medicao.temperatura_ambiente,
        ponto_quente_externo=medicao.ponto_quente_externo,
        horas_operacao=medicao.horas_operacao,
        capacitancia=capacitancia,
        perda_dieletrica=perda_dieletrica,
    )

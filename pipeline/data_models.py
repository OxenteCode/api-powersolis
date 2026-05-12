# -*- coding: utf-8 -*-
"""
pipeline/data_models.py
=======================
Definição das estruturas de dados (dataclasses) que circulam por todo o
pipeline de diagnóstico de Transformadores de Corrente (TCs).

Todas as outras camadas importam daqui — garante um contrato único de interface.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# ENTRADA DO PIPELINE
# ---------------------------------------------------------------------------

@dataclass
class MedicaoBruta:
    """
    Representa **uma linha de medição** proveniente do banco de dados.

    Parâmetros
    ----------
    tangente_perdas : float
        Tangente de perdas dielétrica Tg(δ), em percentual (%).
        Ex.: 0.7 significa 0,7 %.
    corrente : float
        Corrente primária aplicada ao TC, em Ampères (A).
    temperatura_ambiente : float
        Temperatura ambiente no momento da medição, em graus Celsius (°C).
    ponto_quente_externo : float
        Temperatura do ponto quente medido externamente (câmera IR ou
        sensor de superfície), em graus Celsius (°C).
    horas_operacao : float
        Total de horas de operação acumuladas pelo equipamento até o
        momento da medição.
    tensao_nominal : float
        Tensão nominal do TC em kV (ex.: 245.0 ou 550.0).
        Usada para selecionar o modelo de inferência correto.
    id_equipamento : str, opcional
        Identificador único do TC no banco de dados (para rastreabilidade).
    """

    tangente_perdas: float
    corrente: float
    temperatura_ambiente: float
    ponto_quente_externo: float
    horas_operacao: float
    tensao_nominal: float
    id_equipamento: Optional[str] = field(default=None)


# ---------------------------------------------------------------------------
# DADOS INTERMEDIÁRIOS (entre etapas do pipeline)
# ---------------------------------------------------------------------------

@dataclass
class FeatureVector:
    """
    Vetor de atributos extraídos e calculados a partir de uma
    :class:`MedicaoBruta`.

    Inclui as quatro medições brutas originais **mais** os atributos
    derivados calculados por ``preprocessing/feature_extraction.py``.

    Parâmetros
    ----------
    tangente_perdas : float
        Tg(δ) em percentual (%) — repassada sem modificação.
    corrente : float
        Corrente primária em A — repassada sem modificação.
    temperatura_ambiente : float
        Temperatura ambiente em °C — repassada sem modificação.
    ponto_quente_externo : float
        Ponto quente externo em °C — repassado sem modificação.
    horas_operacao : float
        Horas de operação acumuladas.
    capacitancia : float
        Capacitância calculada a partir de Tg(δ), corrente e tensão, em Farads (F).
    perda_dieletrica : float
        Perda dielétrica calculada a partir de Tg(δ) e capacitância, em Watts (W).
    """

    tangente_perdas: float
    corrente: float
    temperatura_ambiente: float
    ponto_quente_externo: float
    horas_operacao: float
    capacitancia: float
    perda_dieletrica: float


# ---------------------------------------------------------------------------
# SAÍDA DO PIPELINE
# ---------------------------------------------------------------------------

@dataclass
class DiagnosticResult:
    """
    Resultado completo do pipeline de diagnóstico para um único TC.

    É a saída final de :class:`pipeline.diagnostic_pipeline.DiagnosticPipeline`.

    Parâmetros
    ----------
    id_equipamento : str, opcional
        Identificador do TC (repassado de :class:`MedicaoBruta`).
    temperatura_hotspot_inferida_C : float
        Temperatura interna do ponto quente (hotspot) inferida pelo modelo
        de regressão, em graus Celsius (°C).
    fator_aceleracao : float
        Fator de Aceleração de Envelhecimento (FAA) calculado pelo
        ``model_aging``; indica quantas vezes mais rápido o TC envelhece
        em relação à temperatura de referência.
    expectativa_vida_anos : float
        Expectativa de vida útil total do TC na temperatura de hotspot
        atual, em **anos** (saída direta de ``model_aging``).
    horas_equivalentes_ref : float
        Horas equivalentes de operação na temperatura de referência,
        considerando a aceleração de envelhecimento.
    percentual_vida_perdida : float
        Percentual da vida útil já consumida até o momento da medição (%).
    estado_operacional : str
        Categoria qualitativa do estado do equipamento.
        Valores possíveis: ``"Novo"``, ``"Atenção"`` ou ``"Perigo"``.
    score_fuzzy : float
        Score numérico contínuo gerado pelo sistema de lógica nebulosa,
        no intervalo [0, 100]. Quanto maior, pior o estado.
        (0–33 → Novo; 33–66 → Atenção; 66–100 → Perigo)
    cluster_id : int
        Rótulo do cluster (0, 1 ou 2) atribuído pelo KMeans ao TC.
        Serve como âncora histórica para a classificação fuzzy.
    """

    temperatura_hotspot_inferida_C: float
    fator_aceleracao: float
    expectativa_vida_anos: float
    horas_equivalentes_ref: float
    percentual_vida_perdida: float
    estado_operacional: str
    score_fuzzy: float
    cluster_id: int
    id_equipamento: Optional[str] = field(default=None)

    def __str__(self) -> str:  # noqa: D105
        return (
            f"[TC: {self.id_equipamento or 'N/A'}]\n"
            f"  Hotspot inferido     : {self.temperatura_hotspot_inferida_C:.2f} °C\n"
            f"  FAA                  : {self.fator_aceleracao:.2f}x\n"
            f"  Expectativa de vida  : {self.expectativa_vida_anos:.2f} anos\n"
            f"  Vida perdida         : {self.percentual_vida_perdida:.4f} %\n"
            f"  Estado operacional   : {self.estado_operacional}\n"
            f"  Score fuzzy          : {self.score_fuzzy:.1f} / 100\n"
            f"  Cluster              : {self.cluster_id}"
        )

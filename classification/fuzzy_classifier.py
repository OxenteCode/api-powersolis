# -*- coding: utf-8 -*-
"""
classification/fuzzy_classifier.py — Sub-etapa de classificação nebulosa (Etapa ④).
Sistema Mamdani com 4 entradas e 10 regras para classificação de TCs.
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ---------------------------------------------------------------------------
# UNIVERSOS DE DISCURSO
# ---------------------------------------------------------------------------

UNIVERSO_TG      = np.arange(0.0,   2.01,  0.01)   # Tg(δ) em %
UNIVERSO_HOTSPOT = np.arange(40.0, 141.0,  1.0)    # Hotspot em °C
UNIVERSO_VIDA    = np.arange(0.0,   25.1,  0.1)    # Vida útil em anos
UNIVERSO_FAA     = np.arange(0.25,  8.01,  0.01)   # FAA adimensional
UNIVERSO_ESTADO  = np.arange(0.0,  101.0,  1.0)    # Score de saída [0–100]


# ---------------------------------------------------------------------------
# CLASSIFICADOR
# ---------------------------------------------------------------------------

class FuzzyTCClassifier:
    """
    Classificador nebuloso Mamdani para estado operacional de TCs.

    Variáveis de entrada
    --------------------
    tg       : Tangente de perdas em %   → baixa / media / alta
    hotspot  : Hotspot interno em °C     → normal / elevada / critica
    vida     : Expectativa de vida (anos)→ alta / media / baixa
    faa      : Fator de aceleração       → baixo / moderado / alto

    Variável de saída
    -----------------
    estado   : Score [0–100]  → novo [0–33] / atenção [33–66] / perigo [66–100]

    Defuzzificação: centróide (CoG).

    Exemplo
    -------
    >>> clf = FuzzyTCClassifier()
    >>> estado, score = clf.classificar(0.7, 82.0, 10.5, 2.1)
    >>> print(estado, score)
    Atenção 55.3
    """

    def __init__(self) -> None:
        self._criar_variaveis_linguisticas()
        self._definir_funcoes_pertinencia()
        self._definir_regras()
        self._sistema = ctrl.ControlSystem(self._regras)

    # ------------------------------------------------------------------
    def _criar_variaveis_linguisticas(self) -> None:
        """Cria os Antecedentes e o Consequente do sistema fuzzy."""
        self.tg      = ctrl.Antecedent(UNIVERSO_TG,      "tg")
        self.hotspot = ctrl.Antecedent(UNIVERSO_HOTSPOT,  "hotspot")
        self.vida    = ctrl.Antecedent(UNIVERSO_VIDA,     "vida")
        self.faa     = ctrl.Antecedent(UNIVERSO_FAA,      "faa")
        self.estado  = ctrl.Consequent(UNIVERSO_ESTADO,   "estado",
                                       defuzzify_method="centroid")

    # ------------------------------------------------------------------
    def _definir_funcoes_pertinencia(self) -> None:
        """
        Define funções de pertinência trapezoidais e triangulares baseadas
        nos limiares normativos para TCs de alta tensão.

        Limiares chave
        --------------
        - Tg(δ): Baixa < 0,5% | Média 0,5–0,8% | Alta > 0,8%
        - Hotspot: Normal < 70°C | Elevada 70–90°C | Crítica > 90°C
        - Vida: Alta > 17,5a | Média 7,5–17,5a | Baixa < 7,5a
        """
        # --- Tangente de Perdas ---
        self.tg["baixa"] = fuzz.trapmf(UNIVERSO_TG,  [0.0,  0.0,  0.35, 0.50])
        self.tg["media"] = fuzz.trimf(UNIVERSO_TG,   [0.50, 0.65, 0.80])
        self.tg["alta"]  = fuzz.trapmf(UNIVERSO_TG,  [0.70, 0.80, 2.0,  2.0])

        # --- Temperatura Hotspot ---
        self.hotspot["normal"]  = fuzz.trapmf(UNIVERSO_HOTSPOT, [40.0, 40.0, 60.0, 72.0])
        self.hotspot["elevada"] = fuzz.trimf(UNIVERSO_HOTSPOT,  [62.0, 80.0, 95.0])
        self.hotspot["critica"] = fuzz.trapmf(UNIVERSO_HOTSPOT, [85.0, 95.0, 140.0, 140.0])

        # --- Expectativa de Vida (anos) ---
        self.vida["alta"]  = fuzz.trapmf(UNIVERSO_VIDA, [15.0, 20.0, 25.0, 25.0])
        self.vida["media"] = fuzz.trimf(UNIVERSO_VIDA,  [5.0,  12.5, 20.0])
        self.vida["baixa"] = fuzz.trapmf(UNIVERSO_VIDA, [0.0,  0.0,  5.0,  10.0])

        # --- Fator de Aceleração de Envelhecimento ---
        self.faa["baixo"]    = fuzz.trapmf(UNIVERSO_FAA, [0.25, 0.25, 0.9,  1.5])
        self.faa["moderado"] = fuzz.trimf(UNIVERSO_FAA,  [1.2,  2.25, 3.2])
        self.faa["alto"]     = fuzz.trapmf(UNIVERSO_FAA, [2.8,  3.5,  8.0,  8.0])

        # --- Estado Operacional (saída) ---
        self.estado["novo"]    = fuzz.trapmf(UNIVERSO_ESTADO, [0.0,  0.0,  20.0, 38.0])
        self.estado["atencao"] = fuzz.trimf(UNIVERSO_ESTADO,  [28.0, 50.0, 72.0])
        self.estado["perigo"]  = fuzz.trapmf(UNIVERSO_ESTADO, [58.0, 76.0, 100.0, 100.0])

    # ------------------------------------------------------------------
    def _definir_regras(self) -> None:
        """
        Define a base de 10 regras Mamdani.

        R1:  tg=baixa  ∧ hotspot=normal  ∧ vida=alta   → novo
        R2:  tg=media  ∧ hotspot=elevada              → atenção
        R3:  tg=alta                                  → perigo
        R4:  hotspot=critica                          → perigo
        R5:  vida=baixa                               → perigo
        R6:  tg=baixa  ∧ hotspot=elevada              → atenção
        R7:  tg=media  ∧ vida=media                   → atenção
        R8:  faa=alto  ∧ vida=media                   → atenção
        R9:  faa=alto  ∧ tg=alta                      → perigo
        R10: tg=baixa  ∧ vida=alta  ∧ hotspot=normal  → novo
        """
        self._regras = [
            ctrl.Rule(self.tg["baixa"] & self.hotspot["normal"] & self.vida["alta"],
                      self.estado["novo"]),
            ctrl.Rule(self.tg["media"] & self.hotspot["elevada"],
                      self.estado["atencao"]),
            ctrl.Rule(self.tg["alta"],
                      self.estado["perigo"]),
            ctrl.Rule(self.hotspot["critica"],
                      self.estado["perigo"]),
            ctrl.Rule(self.vida["baixa"],
                      self.estado["perigo"]),
            ctrl.Rule(self.tg["baixa"] & self.hotspot["elevada"],
                      self.estado["atencao"]),
            ctrl.Rule(self.tg["media"] & self.vida["media"],
                      self.estado["atencao"]),
            ctrl.Rule(self.faa["alto"] & self.vida["media"],
                      self.estado["atencao"]),
            ctrl.Rule(self.faa["alto"] & self.tg["alta"],
                      self.estado["perigo"]),
            ctrl.Rule(self.tg["baixa"] & self.vida["alta"] & self.hotspot["normal"],
                      self.estado["novo"]),
        ]

    # ------------------------------------------------------------------
    def classificar(
        self,
        tangente_perdas: float,
        temperatura_hotspot_C: float,
        expectativa_vida_anos: float,
        fator_aceleracao: float,
    ) -> Tuple[str, float]:
        """
        Executa a inferência fuzzy e retorna o estado e o score numérico.

        Parâmetros
        ----------
        tangente_perdas : float
            Tg(δ) em % (ex.: 0.7 para 0,7%).
        temperatura_hotspot_C : float
            Temperatura interna do hotspot em °C.
        expectativa_vida_anos : float
            Expectativa de vida em **anos** (chave ``expectativa_vida_atual_anos``
            de ``model_aging``).
        fator_aceleracao : float
            FAA adimensional (chave ``fator_aceleracao`` de ``model_aging``).

        Retorna
        -------
        Tuple[str, float]
            ``("Novo" | "Atenção" | "Perigo", score_0_a_100)``
        """
        # Clamp para os universos de discurso
        tg_val  = float(np.clip(tangente_perdas,       UNIVERSO_TG[0],      UNIVERSO_TG[-1]))
        hs_val  = float(np.clip(temperatura_hotspot_C, UNIVERSO_HOTSPOT[0], UNIVERSO_HOTSPOT[-1]))
        vd_val  = float(np.clip(expectativa_vida_anos, UNIVERSO_VIDA[0],    UNIVERSO_VIDA[-1]))
        faa_val = float(np.clip(fator_aceleracao,      UNIVERSO_FAA[0],     UNIVERSO_FAA[-1]))

        simulador = ctrl.ControlSystemSimulation(self._sistema)
        simulador.input["tg"]      = tg_val
        simulador.input["hotspot"] = hs_val
        simulador.input["vida"]    = vd_val
        simulador.input["faa"]     = faa_val

        try:
            simulador.compute()
            score = float(simulador.output["estado"])
        except Exception:
            # Fallback determinístico caso nenhuma regra dispare
            score = self._score_fallback(tg_val, hs_val, vd_val)

        estado = self.score_para_estado(score)
        return estado, round(score, 2)

    # ------------------------------------------------------------------
    @staticmethod
    def score_para_estado(score: float) -> str:
        """
        Converte um score [0–100] para o rótulo de estado.

        0 ≤ score < 33  → "Novo"
        33 ≤ score < 66 → "Atenção"
        66 ≤ score ≤ 100 → "Perigo"
        """
        if score < 33.0:
            return "Novo"
        elif score < 66.0:
            return "Atenção"
        else:
            return "Perigo"

    # ------------------------------------------------------------------
    @staticmethod
    def _score_fallback(tg: float, hotspot: float, vida: float) -> float:
        """
        Score determinístico baseado em regras rígidas — usado quando
        a inferência fuzzy não produz resultado (ex.: entrada fora dos limites).
        """
        if tg > 0.8 or hotspot > 90.0 or vida < 7.5:
            return 80.0   # Perigo
        elif tg > 0.5 or hotspot > 70.0 or vida < 17.5:
            return 50.0   # Atenção
        else:
            return 16.0   # Novo

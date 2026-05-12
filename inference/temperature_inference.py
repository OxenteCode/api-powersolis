# -*- coding: utf-8 -*-
"""
inference/temperature_inference.py — Etapa ② do pipeline.
Wrapper sobre modeling.model_hotspot para inferência do hotspot interno.
"""

from __future__ import annotations

import os
import joblib
import pandas as pd

from pipeline.data_models import FeatureVector


class HotspotInferenceModel:
    """
    Wrapper de alto nível sobre o modelo de regressão polinomial de hotspot.

    Carrega um arquivo ``.pkl`` gerado por
    ``modeling.model_hotspot.treinar_e_salvar_modelo`` e expõe uma interface
    simples via :meth:`inferir`.

    Parâmetros
    ----------
    caminho_modelo_pkl : str
        Caminho para o arquivo ``.pkl`` do modelo treinado.

    Levanta
    -------
    FileNotFoundError
        Se o arquivo ``.pkl`` não for encontrado.
    """

    def __init__(self, caminho_modelo_pkl: str) -> None:
        if not os.path.isfile(caminho_modelo_pkl):
            raise FileNotFoundError(
                f"Modelo de hotspot não encontrado em: '{caminho_modelo_pkl}'\n"
                f"Execute modeling.model_hotspot.treinar_e_salvar_modelo() primeiro."
            )
        self._caminho = os.path.abspath(caminho_modelo_pkl)
        self._modelo = joblib.load(self._caminho)

    def inferir(self, features: FeatureVector) -> float:
        """
        Infere a temperatura do hotspot interno a partir do FeatureVector.

        Monta um DataFrame com as 4 colunas esperadas pelo pipeline do
        scikit-learn e chama ``predict``.

        Parâmetros
        ----------
        features : FeatureVector
            Vetor de atributos da etapa ①. Usados:
            ``tangente_perdas``, ``corrente``, ``temperatura_ambiente``,
            ``ponto_quente_externo``.

        Retorna
        -------
        float
            Temperatura do hotspot interno inferida em °C.
        """
        X = pd.DataFrame({
            "tangente_perdas":      [features.tangente_perdas],
            "corrente_primario":    [features.corrente],
            "temperatura_ambiente": [features.temperatura_ambiente],
            "ponto_quente_externo": [features.ponto_quente_externo],
        })
        return float(self._modelo.predict(X)[0])

    @property
    def caminho_modelo(self) -> str:
        """Caminho absoluto do arquivo ``.pkl`` carregado."""
        return self._caminho


# ---------------------------------------------------------------------------
# FUNÇÃO DE CONVENIÊNCIA
# ---------------------------------------------------------------------------

def inferir_hotspot(
    features: FeatureVector,
    caminho_modelo_pkl: str,
) -> float:
    """
    Infere o hotspot sem instanciar HotspotInferenceModel explicitamente.

    Parâmetros
    ----------
    features : FeatureVector
        Vetor de atributos da etapa ①.
    caminho_modelo_pkl : str
        Caminho para o ``.pkl`` do modelo treinado.

    Retorna
    -------
    float
        Temperatura do hotspot interno em °C.
    """
    return HotspotInferenceModel(caminho_modelo_pkl).inferir(features)

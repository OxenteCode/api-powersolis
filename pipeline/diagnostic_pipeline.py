# -*- coding: utf-8 -*-
"""
pipeline/diagnostic_pipeline.py — Orquestrador central do sistema de diagnóstico de TCs.
Une as 4 etapas do pipeline em uma única interface DiagnosticPipeline.
"""

from __future__ import annotations

import pandas as pd
from typing import Optional

from pipeline.data_models import MedicaoBruta, DiagnosticResult
from preprocessing.feature_extraction import extrair_features
from inference.temperature_inference import HotspotInferenceModel
from classification.clustering import TCClusteringModel, MAPA_CLUSTER_ESTADO
from classification.fuzzy_classifier import FuzzyTCClassifier
import modeling.model_aging as aging


class DiagnosticPipeline:
    """
    Pipeline completo de diagnóstico de Transformadores de Corrente (TCs).

    Sequência de execução
    ---------------------
    ①  feature_extraction  — valida e enriquece atributos
    ②  temperature_inference — infere T_hotspot interno
    ③  model_aging           — calcula vida útil (Montsinger)
    ④a clustering            — atribui cluster histórico
    ④b fuzzy_classifier      — classifica estado (Novo/Atenção/Perigo)

    Parâmetros
    ----------
    caminho_modelo_hotspot : str
        Caminho para o ``.pkl`` do modelo de regressão de hotspot.
    caminho_modelo_clustering : str, opcional
        Caminho para o ``.pkl`` do modelo KMeans pré-treinado.
        Se None, usa fallback por regras rígidas até treinar.
    tensao_ensaio_V : float
        Tensão de ensaio para cálculo de capacitância. Padrão: 10 000 V.
    vida_ref_anos : float
        Vida útil de referência em anos para Montsinger. Padrão: 25.
    temp_ref_C : float
        Temperatura de referência para Montsinger em °C. Padrão: 85.
    p_montsinger : float
        Fator p de Montsinger em °C. Padrão: 8.
    """

    def __init__(
        self,
        caminho_modelo_hotspot: str,
        caminho_modelo_clustering: Optional[str] = None,
        tensao_ensaio_V: float = 10_000.0,
        vida_ref_anos: float = 25.0,
        temp_ref_C: float = 85.0,
        p_montsinger: float = 8.0,
    ) -> None:
        self._tensao_ensaio_V = tensao_ensaio_V
        self._vida_ref_anos   = vida_ref_anos
        self._temp_ref_C      = temp_ref_C
        self._p_montsinger    = p_montsinger

        # Modelos
        self.modelo_hotspot   = HotspotInferenceModel(caminho_modelo_hotspot)
        self.modelo_clustering = (
            TCClusteringModel.carregar(caminho_modelo_clustering)
            if caminho_modelo_clustering
            else TCClusteringModel()
        )
        self.classificador_fuzzy = FuzzyTCClassifier()

    # ------------------------------------------------------------------
    def executar(self, medicao: MedicaoBruta) -> DiagnosticResult:
        """
        Executa o pipeline completo sobre uma única medição.

        Parâmetros
        ----------
        medicao : MedicaoBruta
            Dados brutos de uma medição do banco de dados.

        Retorna
        -------
        DiagnosticResult
            Resultado completo com hotspot, vida útil, estado e score fuzzy.

        Levanta
        -------
        ValueError
            Se os dados de entrada forem inválidos.
        """
        # ① Extração de atributos
        features = extrair_features(medicao, tensao_ensaio_V=self._tensao_ensaio_V)

        # ② Inferência de temperatura
        t_hotspot = self.modelo_hotspot.inferir(features)

        # ③ Previsão de vida útil (Montsinger Base-2)
        res_aging = aging.calcular_perda_vida_util_base2(
            temperatura_hotspot=t_hotspot,
            horas_operacao=medicao.horas_operacao,
            temp_ref=self._temp_ref_C,
            vida_ref_anos=self._vida_ref_anos,
            p=self._p_montsinger,
        )
        expectativa_vida_anos   = res_aging["expectativa_vida_atual_anos"]
        fator_aceleracao        = res_aging["fator_aceleracao"]
        horas_equivalentes_ref  = res_aging["horas_equivalentes_a_95C"]
        percentual_vida_perdida = res_aging["percentual_vida_perdida"]

        # ④a Clustering
        if self.modelo_clustering.esta_treinado:
            cluster_id = self.modelo_clustering.prever_cluster(
                temperatura_hotspot_C=t_hotspot,
                expectativa_vida_anos=expectativa_vida_anos,
                tangente_perdas=features.tangente_perdas,
            )
        else:
            cluster_id = self._cluster_fallback(
                features.tangente_perdas, t_hotspot, expectativa_vida_anos
            )

        # ④b Classificação fuzzy
        estado, score_fuzzy = self.classificador_fuzzy.classificar(
            tangente_perdas=features.tangente_perdas,
            temperatura_hotspot_C=t_hotspot,
            expectativa_vida_anos=expectativa_vida_anos,
            fator_aceleracao=fator_aceleracao,
        )

        return DiagnosticResult(
            temperatura_hotspot_inferida_C=round(t_hotspot, 2),
            fator_aceleracao=fator_aceleracao,
            expectativa_vida_anos=expectativa_vida_anos,
            horas_equivalentes_ref=horas_equivalentes_ref,
            percentual_vida_perdida=percentual_vida_perdida,
            estado_operacional=estado,
            score_fuzzy=round(score_fuzzy, 2),
            cluster_id=cluster_id,
            id_equipamento=medicao.id_equipamento,
        )

    # ------------------------------------------------------------------
    def executar_lote(self, df_medicoes: pd.DataFrame) -> pd.DataFrame:
        """
        Executa o pipeline sobre um lote de medições (DataFrame).

        Parâmetros
        ----------
        df_medicoes : pd.DataFrame
            Colunas obrigatórias: ``tangente_perdas``, ``corrente``,
            ``temperatura_ambiente``, ``ponto_quente_externo``,
            ``horas_operacao``, ``tensao_nominal``.
            Coluna opcional: ``id_equipamento``.

        Retorna
        -------
        pd.DataFrame
            DataFrame original com colunas de resultado adicionadas.

        Levanta
        -------
        KeyError
            Se alguma coluna obrigatória estiver ausente.
        """
        colunas_obrigatorias = [
            "tangente_perdas", "corrente", "temperatura_ambiente",
            "ponto_quente_externo", "horas_operacao", "tensao_nominal",
        ]
        faltando = [c for c in colunas_obrigatorias if c not in df_medicoes.columns]
        if faltando:
            raise KeyError(f"Colunas obrigatórias ausentes no DataFrame: {faltando}")

        registros = []
        for _, row in df_medicoes.iterrows():
            medicao = MedicaoBruta(
                tangente_perdas=float(row["tangente_perdas"]),
                corrente=float(row["corrente"]),
                temperatura_ambiente=float(row["temperatura_ambiente"]),
                ponto_quente_externo=float(row["ponto_quente_externo"]),
                horas_operacao=float(row["horas_operacao"]),
                tensao_nominal=float(row["tensao_nominal"]),
                id_equipamento=str(row["id_equipamento"])
                if "id_equipamento" in row else None,
            )
            r = self.executar(medicao)
            registros.append({
                "temperatura_hotspot_inferida_C": r.temperatura_hotspot_inferida_C,
                "fator_aceleracao":               r.fator_aceleracao,
                "expectativa_vida_anos":          r.expectativa_vida_anos,
                "horas_equivalentes_ref":         r.horas_equivalentes_ref,
                "percentual_vida_perdida":        r.percentual_vida_perdida,
                "estado_operacional":             r.estado_operacional,
                "score_fuzzy":                    r.score_fuzzy,
                "cluster_id":                     r.cluster_id,
            })

        df_resultado = pd.DataFrame(registros)
        return pd.concat(
            [df_medicoes.reset_index(drop=True), df_resultado],
            axis=1,
        )

    # ------------------------------------------------------------------
    def treinar_clustering(
        self,
        df_historico: pd.DataFrame,
        salvar_em: Optional[str] = None,
    ) -> None:
        """
        Treina (ou re-treina) o modelo de clustering com dados históricos.

        O DataFrame deve conter as colunas que o :class:`TCClusteringModel`
        espera: ``tangente_perdas``, ``temperatura_hotspot_C``,
        ``expectativa_vida_anos``.

        Parâmetros
        ----------
        df_historico : pd.DataFrame
            Histórico de medições rotuladas/processadas.
        salvar_em : str, opcional
            Se informado, persiste o modelo treinado neste caminho.
        """
        self.modelo_clustering.treinar(df_historico)
        if salvar_em:
            self.modelo_clustering.salvar(salvar_em)

    # ------------------------------------------------------------------
    @staticmethod
    def _cluster_fallback(tg: float, hotspot: float, vida_anos: float) -> int:
        """Atribuição de cluster por regras rígidas (sem modelo treinado)."""
        if tg > 0.8 or hotspot > 90.0 or vida_anos < 7.5:
            return 2  # Perigo
        elif tg > 0.5 or hotspot > 70.0 or vida_anos < 17.5:
            return 1  # Atenção
        return 0      # Novo

# -*- coding: utf-8 -*-
"""
classification/clustering.py — Sub-etapa de agrupamento da Etapa ④.
KMeans semi-supervisionado com centróides normativos para TCs.
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# CONSTANTES NORMATIVAS
# ---------------------------------------------------------------------------

COLUNAS_CLUSTERING: list[str] = [
    "tangente_perdas",
    "temperatura_hotspot_C",
    "expectativa_vida_anos",
]

# Centróides iniciais em escala original (não normalizada):
# [tangente_perdas (%), hotspot (°C), vida_util (anos)]
CENTROIDES_INICIAIS_RAW: np.ndarray = np.array([
    [0.30,  60.0, 22.0],   # Cluster → Novo
    [0.65,  80.0, 12.0],   # Cluster → Atenção
    [1.20, 100.0,  4.0],   # Cluster → Perigo
])

MAPA_CLUSTER_ESTADO: dict[int, str] = {
    0: "Novo",
    1: "Atenção",
    2: "Perigo",
}


# ---------------------------------------------------------------------------
# CLASSE PRINCIPAL
# ---------------------------------------------------------------------------

class TCClusteringModel:
    """
    Modelo de agrupamento KMeans semi-supervisionado para TCs.

    Os centróides são inicializados com os valores normativos em
    ``CENTROIDES_INICIAIS_RAW``, garantindo convergência para clusters
    com significado físico mesmo em datasets pequenos.

    Após o ajuste, os clusters são remapeados por ordem crescente de
    tangente de perdas: cluster 0 = Novo, 1 = Atenção, 2 = Perigo.

    Parâmetros
    ----------
    n_clusters : int
        Número de clusters. Padrão: 3.
    random_state : int
        Semente para reprodutibilidade. Padrão: 42.
    """

    def __init__(self, n_clusters: int = 3, random_state: int = 42) -> None:
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.modelo_kmeans: KMeans | None = None
        self.scaler: StandardScaler | None = None
        self._label_map: dict[int, int] = {}
        self.esta_treinado: bool = False

    # ------------------------------------------------------------------
    def treinar(self, df_historico: pd.DataFrame) -> "TCClusteringModel":
        """
        Treina o KMeans sobre um histórico de medições.

        Parâmetros
        ----------
        df_historico : pd.DataFrame
            Deve conter as colunas: ``tangente_perdas``,
            ``temperatura_hotspot_C``, ``expectativa_vida_anos``.

        Retorna
        -------
        TCClusteringModel
            A própria instância (encadeamento de métodos).

        Levanta
        -------
        ValueError
            Se colunas obrigatórias estiverem ausentes ou o DataFrame
            tiver menos amostras que ``n_clusters``.
        """
        faltando = [c for c in COLUNAS_CLUSTERING if c not in df_historico.columns]
        if faltando:
            raise ValueError(f"Colunas ausentes no DataFrame: {faltando}")
        if len(df_historico) < self.n_clusters:
            raise ValueError(
                f"O DataFrame precisa de pelo menos {self.n_clusters} amostras, "
                f"mas tem {len(df_historico)}."
            )

        X = df_historico[COLUNAS_CLUSTERING].values.astype(float)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Transforma os centróides normativos para o espaço normalizado
        centroides_scaled = self.scaler.transform(CENTROIDES_INICIAIS_RAW)

        self.modelo_kmeans = KMeans(
            n_clusters=self.n_clusters,
            init=centroides_scaled,
            n_init=1,
            random_state=self.random_state,
            max_iter=500,
        )
        self.modelo_kmeans.fit(X_scaled)

        # Remapeia labels: ordena centróides por tangente_perdas (asc)
        # → índice 0 = Novo, 1 = Atenção, 2 = Perigo
        centros_orig = self.scaler.inverse_transform(self.modelo_kmeans.cluster_centers_)
        ordem = np.argsort(centros_orig[:, 0])   # coluna 0 = tangente_perdas
        self._label_map = {int(kmeans_id): int(estado_id)
                           for estado_id, kmeans_id in enumerate(ordem)}

        self.esta_treinado = True
        return self

    # ------------------------------------------------------------------
    def prever_cluster(
        self,
        temperatura_hotspot_C: float,
        expectativa_vida_anos: float,
        tangente_perdas: float,
    ) -> int:
        """
        Atribui um rótulo de cluster a uma nova observação.

        Parâmetros
        ----------
        temperatura_hotspot_C : float
            Temperatura do hotspot interno inferida em °C.
        expectativa_vida_anos : float
            Expectativa de vida útil em **anos**.
        tangente_perdas : float
            Tg(δ) em percentual (%).

        Retorna
        -------
        int
            0 = Novo, 1 = Atenção, 2 = Perigo.

        Levanta
        -------
        RuntimeError
            Se o modelo não foi treinado.
        """
        if not self.esta_treinado:
            raise RuntimeError("Chame .treinar() antes de usar .prever_cluster().")

        X = np.array([[tangente_perdas, temperatura_hotspot_C, expectativa_vida_anos]])
        X_scaled = self.scaler.transform(X)
        label_kmeans = int(self.modelo_kmeans.predict(X_scaled)[0])
        return self._label_map[label_kmeans]

    # ------------------------------------------------------------------
    def salvar(self, caminho_pkl: str) -> None:
        """
        Serializa o modelo e o scaler em ``caminho_pkl``.

        Parâmetros
        ----------
        caminho_pkl : str
            Caminho de destino para o arquivo ``.pkl``.

        Levanta
        -------
        RuntimeError
            Se o modelo não foi treinado.
        """
        if not self.esta_treinado:
            raise RuntimeError("Chame .treinar() antes de .salvar().")
        os.makedirs(os.path.dirname(caminho_pkl) or ".", exist_ok=True)
        joblib.dump(
            {"kmeans": self.modelo_kmeans,
             "scaler": self.scaler,
             "label_map": self._label_map},
            caminho_pkl,
        )

    # ------------------------------------------------------------------
    @classmethod
    def carregar(cls, caminho_pkl: str) -> "TCClusteringModel":
        """
        Carrega um modelo previamente salvo com :meth:`salvar`.

        Parâmetros
        ----------
        caminho_pkl : str
            Caminho para o ``.pkl`` salvo.

        Retorna
        -------
        TCClusteringModel
            Instância pronta para uso.

        Levanta
        -------
        FileNotFoundError
            Se o arquivo não existir.
        """
        if not os.path.isfile(caminho_pkl):
            raise FileNotFoundError(f"Arquivo de clustering não encontrado: '{caminho_pkl}'")
        data = joblib.load(caminho_pkl)
        inst = cls()
        inst.modelo_kmeans = data["kmeans"]
        inst.scaler = data["scaler"]
        inst._label_map = data["label_map"]
        inst.esta_treinado = True
        return inst

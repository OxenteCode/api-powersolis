# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 20:35:40 2026

@author: engjo
"""

import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
import joblib

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

def treinar_e_salvar_modelo(caminho_arquivo='modelo_hotspot.pkl', grau=2):
    """
    Treina um modelo de regressão polinomial com os dados da tabela
    e o salva em um arquivo .pkl.
    """
    dados = {
        'tangente_perdas': [0.22, 0.22, 0.5, 0.5, 0.5, 0.22, 0.5, 0.7, 1.0],
        'corrente_primario': [200, 400, 400, 400, 400, 400, 400, 400, 400],
        'temperatura_ambiente': [20, 20, 20, 30, 40, 20, 20, 20, 20],
        'temperatura_hotspot': [52.3, 58.9, 72.0, 80.9, 89.8, 52.3, 72.0, 81.5, 95.7]
    }
    
    df = pd.DataFrame(dados)
    
    # Separando as variáveis de entrada (X) e a variável alvo (y)
    X = df[['tangente_perdas', 'corrente_primario', 'temperatura_ambiente']]
    y = df['temperatura_hotspot']
    
    # Criando um pipeline: transforma as features em polinomiais e aplica Regressão Linear
    # O grau 2 cria interações e termos ao quadrado (ex: x1*x2, x1^2)
    modelo = Pipeline([
        ('poly', PolynomialFeatures(degree=grau, include_bias=False)),
        ('linear', LinearRegression())
    ])
    
    # Treinando o modelo
    modelo.fit(X, y)
    
    # Salvando o modelo treinado
    joblib.dump(modelo, caminho_arquivo)
    print(f"Modelo treinado com sucesso e salvo em: '{caminho_arquivo}'")

def inferir_temperatura(tangente_perdas, corrente_primario, temperatura_ambiente, caminho_arquivo='modelo_hotspot.pkl'):
    """
    Carrega o modelo salvo e realiza a inferência da temperatura do hotspot.
    """
    # Carregando o modelo
    modelo_carregado = joblib.load(caminho_arquivo)
    
    # Preparando os novos dados no mesmo formato do treinamento
    X_novo = pd.DataFrame({
        'tangente_perdas': [tangente_perdas],
        'corrente_primario': [corrente_primario],
        'temperatura_ambiente': [temperatura_ambiente]
    })
    
    # Realizando a predição
    previsao = modelo_carregado.predict(X_novo)
    
    return previsao[0]

# --- Exemplo de Uso ---
if __name__ == "__main__":
    # 1. Treinar e salvar
    treinar_e_salvar_modelo(grau=2)
    
    # 2. Testar uma inferência
    tg_perdas = 0.6
    corrente = 350
    temp_amb = 25
    
    temp_estimada = inferir_temperatura(tg_perdas, corrente, temp_amb)
    print(f"\nPara Tg(δ)={tg_perdas}%, I={corrente}A, Temp. Amb.={temp_amb}°C:")
    print(f"Temperatura Hotspot inferida: {temp_estimada:.2f} °C")
    

def plotar_superficie_hotspot(variavel_fixa, valor_fixo, 
                              min_tg=0.2, max_tg=1.0, 
                              min_corr=200, max_corr=400, 
                              min_temp=20, max_temp=40, 
                              passos=30, caminho_modelo='modelo_hotspot_3.pkl'):
    """
    Gera uma superfície 3D fixando uma variável e variando as outras duas.
    Variáveis aceitas em 'variavel_fixa': 
    'tangente_perdas', 'corrente_primario' ou 'temperatura_ambiente'.
    """
    # Carregamento do modelo preditivo
    try:
        modelo = joblib.load(caminho_modelo)
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_modelo} não foi encontrado.")
        return

    # Dicionário de limites e mapeamento de nomenclatura
    limites = {
        'tangente_perdas': (min_tg, max_tg),
        'corrente_primario': (min_corr, max_corr),
        'temperatura_ambiente': (min_temp, max_temp)
    }
    
    nomes_exibicao = {
        'tangente_perdas': 'Tangente de Perdas (%)',
        'corrente_primario': 'Corrente Primário (A)',
        'temperatura_ambiente': 'Temp. Ambiente (°C)'
    }

    if variavel_fixa not in limites:
        raise ValueError(f"Variável inválida. Escolha entre: {list(limites.keys())}")

    # Segregação entre variáveis livres (eixos X e Y) e a variável fixa
    vars_livres = {k: v for k, v in limites.items() if k != variavel_fixa}
    chaves_livres = list(vars_livres.keys())
    
    eixo_x_nome = chaves_livres[0]
    eixo_y_nome = chaves_livres[1]

    # Geração da malha estruturada (meshgrid) para as variáveis livres
    # O aumento do número de passos (padrão 30) garante uma superfície suavizada
    x_vals = np.linspace(limites[eixo_x_nome][0], limites[eixo_x_nome][1], passos)
    y_vals = np.linspace(limites[eixo_y_nome][0], limites[eixo_y_nome][1], passos)
    X_mesh, Y_mesh = np.meshgrid(x_vals, y_vals)

    # Estruturação dos dados para inferência vetorializada
    df_pred = pd.DataFrame({
        eixo_x_nome: X_mesh.ravel(),
        eixo_y_nome: Y_mesh.ravel(),
        variavel_fixa: valor_fixo
    })

    # Ordenação estrita das colunas conforme o treinamento do modelo
    df_pred = df_pred[['tangente_perdas', 'corrente_primario', 'temperatura_ambiente']]

    # Inferência e redimensionamento topológico (eixo Z)
    Z_flat = modelo.predict(df_pred)
    Z_mesh = Z_flat.reshape(X_mesh.shape)

    # Configuração gráfica da superfície
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(X_mesh, Y_mesh, Z_mesh, cmap=cm.coolwarm, 
                           linewidth=0, antialiased=True, alpha=0.85)

    # Parametrização dos eixos e legendas
    ax.set_xlabel('\n' + nomes_exibicao[eixo_x_nome])
    ax.set_ylabel('\n' + nomes_exibicao[eixo_y_nome])
    ax.set_zlabel('\nTemperatura Hotspot Inferida (°C)')

    fig.colorbar(surf, shrink=0.6, aspect=12, pad=0.1, label='Temperatura Hotspot (°C)')
    plt.title(f'Análise de Superfície Térmica\n(Condição Fixa: {nomes_exibicao[variavel_fixa]} = {valor_fixo})')
    
    plt.tight_layout()
    # plt.savefig('superficie_hotspot.png', dpi=300)
    # plt.close()
    plt.show()
    
    print("Superfície gerada com sucesso e salva como 'superficie_hotspot.png'.")

# --- Exemplo de Execução ---
if __name__ == "__main__":
    # Exemplo: Avaliando o impacto da corrente e da tangente de perdas
    # em um ensaio com temperatura ambiente controlada a 30°C.
    plotar_superficie_hotspot(
        variavel_fixa='temperatura_ambiente', 
        valor_fixo=30,
        passos=40 # Malha mais densa para melhor resolução gráfica
    )
    
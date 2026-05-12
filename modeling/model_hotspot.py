# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 20:35:40 2026

@author: engjo
"""

import pandas as pd
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, KFold
import joblib
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_PADRAO_MODELO = os.path.join(DIRETORIO_ATUAL, 'modelo_hotspot.pkl')

def _carregar_e_preparar_dados(caminho_dados):
    """
    Carrega e prepara o DataFrame a partir do arquivo ODS.
    Retorna (X, y) prontos para treinamento, ou (None, None) em caso de erro.
    """
    try:
        df = pd.read_excel(caminho_dados, engine='odf')
    except Exception as e:
        print(f"Erro ao ler o arquivo de dados: {e}")
        return None, None

    # Limpando espaços nos nomes das colunas e renomeando
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={
        'Tangente de Perdas (%)': 'tangente_perdas',
        'Corrente Aplicada (A)': 'corrente_primario',
        'Temperatura Ambiente (ºC)': 'temperatura_ambiente',
        'Ponto Quente Externo (ºC)': 'ponto_quente_externo',
        'Hot spot': 'temperatura_hotspot'
    })

    # Limpeza caso os números usem vírgula como separador decimal
    for col in ['tangente_perdas', 'corrente_primario', 'temperatura_ambiente', 'temperatura_hotspot']:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

    X = df[['tangente_perdas', 'corrente_primario', 'temperatura_ambiente', 'ponto_quente_externo']]
    y = df['temperatura_hotspot']
    return X, y


def treinar_e_salvar_modelo(caminho_dados, caminho_arquivo=CAMINHO_PADRAO_MODELO, grau=2):
    """
    Treina um modelo de regressão polinomial com os dados da planilha
    e o salva em um arquivo .pkl.

    Retorna
    -------
    dict com métricas de cross-validation (R² ajustado, RMSE e MAE médios)
    ou None em caso de falha na leitura dos dados.
    """
    X, y = _carregar_e_preparar_dados(caminho_dados)
    if X is None:
        return None

    n_amostras = len(y)
    n_folds = min(5, n_amostras)   # leave-one-out se dataset pequeno

    # Criando um pipeline: padroniza, transforma as features em polinomiais e aplica Regressão Linear
    modelo = Pipeline([
        ('scaler', MinMaxScaler()),
        ('poly', PolynomialFeatures(degree=grau, include_bias=False)),
        ('linear', LinearRegression())
    ])

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    # Predições out-of-fold via cross-validation para conjuntos pequenos
    from sklearn.model_selection import cross_val_predict
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    y_pred_cv = cross_val_predict(modelo, X, y, cv=kf)
    
    r2_cv = r2_score(y, y_pred_cv)
    rmse_cv = np.sqrt(mean_squared_error(y, y_pred_cv))
    mae_cv = mean_absolute_error(y, y_pred_cv)

    # R² ajustado geral (penaliza complexidade)
    n_features_poly = PolynomialFeatures(degree=grau, include_bias=False).fit(X).n_output_features_
    denominador = n_amostras - n_features_poly - 1
    
    if denominador > 0:
        r2_adj_cv = 1 - (1 - r2_cv) * (n_amostras - 1) / denominador
    else:
        # Quando há mais features que amostras, o R² ajustado não é definido
        r2_adj_cv = float('nan')

    metricas = {
        'grau'    : grau,
        'r2_adj'  : float(r2_adj_cv),
        'rmse'    : float(rmse_cv),
        'mae'     : float(mae_cv),
        'n_folds' : n_folds,
    }

    # Treina com dados completos e salva
    modelo.fit(X, y)
    joblib.dump(modelo, caminho_arquivo)
    print(f"Modelo grau {grau} treinado e salvo em: '{caminho_arquivo}'")

    return metricas


def selecionar_melhor_grau(caminho_dados, graus=None, diretorio_saida=None,
                           metrica_principal='r2_adj', verbose=True):
    """
    Avalia modelos de regressão polinomial com graus de 1 a 5 (ou personalizados)
    e identifica o melhor grau com base em métricas de cross-validation.

    Parâmetros
    ----------
    caminho_dados : str
        Caminho para o arquivo ODS com os dados de laboratório.
    graus : list[int], opcional
        Graus a avaliar. Padrão: [1, 2, 3, 4, 5].
    diretorio_saida : str, opcional
        Pasta onde os modelos intermediários serão salvos temporariamente.
        Se None, usa um subdiretório ``avaliacao_graus/`` ao lado dos dados.
    metrica_principal : str
        Métrica usada para determinar o melhor grau.
        Opções: ``'r2_adj'`` (↑ melhor), ``'rmse'`` (↓ melhor), ``'mae'`` (↓ melhor).
        Padrão: ``'r2_adj'``.
    verbose : bool
        Se True, imprime a tabela comparativa no console.

    Retorna
    -------
    dict
        {
          'melhor_grau'  : int,
          'melhor_metrica': float,
          'resultados'   : list[dict],   # uma entrada por grau
        }
    """
    if graus is None:
        graus = [1, 2, 3, 4, 5]

    # Validação da métrica
    metricas_validas = ('r2_adj', 'rmse', 'mae')
    if metrica_principal not in metricas_validas:
        raise ValueError(f"metrica_principal deve ser uma de: {metricas_validas}")

    # Diretório de saída para os modelos temporários
    if diretorio_saida is None:
        diretorio_saida = os.path.join(os.path.dirname(caminho_dados), 'avaliacao_graus')
    os.makedirs(diretorio_saida, exist_ok=True)

    resultados = []

    if verbose:
        print("\n" + "="*60)
        print(" AVALIAÇÃO DE MODELOS | Regressão Polinomial - Hotspot")
        print("="*60)
        print(f" Métrica principal : {metrica_principal.upper()}")
        print(f" Cross-validation  : KFold estratificado")
        print("="*60)
        print(f" {'Grau':^6} | {'R² Adj':^10} | {'RMSE (°C)':^11} | {'MAE (°C)':^10}")
        print("-"*60)

    for grau in graus:
        caminho_modelo_temp = os.path.join(diretorio_saida, f'modelo_grau_{grau}.pkl')
        metricas = treinar_e_salvar_modelo(
            caminho_dados=caminho_dados,
            caminho_arquivo=caminho_modelo_temp,
            grau=grau
        )
        if metricas is None:
            print(f"  Grau {grau}: falha ao treinar — dados não carregados.")
            continue

        resultados.append(metricas)

        if verbose:
            print(f" {grau:^6} | {metricas['r2_adj']:^10.4f} | "
                  f"{metricas['rmse']:^11.4f} | {metricas['mae']:^10.4f}")

    if not resultados:
        print("Nenhum modelo pôde ser avaliado.")
        return None

    # Determina o melhor grau (ignorando NaNs se existirem)
    if metrica_principal == 'r2_adj':
        validos = [r for r in resultados if not np.isnan(r['r2_adj'])]
        melhor = max(validos, key=lambda d: d['r2_adj']) if validos else resultados[0]
    else:
        validos = [r for r in resultados if not np.isnan(r[metrica_principal])]
        melhor = min(validos, key=lambda d: d[metrica_principal]) if validos else resultados[0]

    melhor_grau   = melhor['grau']
    melhor_metrica = melhor[metrica_principal]

    if verbose:
        print("="*60)
        print(f"\n✔ MELHOR GRAU : {melhor_grau}")
        print(f"  {metrica_principal.upper()} = {melhor_metrica:.4f}")
        print(f"\n  Modelo salvo em: {os.path.join(diretorio_saida, f'modelo_grau_{melhor_grau}.pkl')}")
        print("="*60 + "\n")

    return {
        'melhor_grau'   : melhor_grau,
        'melhor_metrica': melhor_metrica,
        'resultados'    : resultados,
    }

def inferir_temperatura(tangente_perdas, corrente_primario, temperatura_ambiente, ponto_externo, caminho_arquivo=CAMINHO_PADRAO_MODELO):
    """
    Carrega o modelo salvo e realiza a inferência da temperatura do hotspot.
    """
    # Carregando o modelo
    modelo_carregado = joblib.load(caminho_arquivo)
    
    # Preparando os novos dados no mesmo formato do treinamento
    X_novo = pd.DataFrame({
        'tangente_perdas': [tangente_perdas],
        'corrente_primario': [corrente_primario],
        'temperatura_ambiente': [temperatura_ambiente],
        'ponto_quente_externo': [ponto_externo]
    })
    
    # Realizando a predição
    previsao = modelo_carregado.predict(X_novo)
    
    return previsao[0]



def plotar_superficie_hotspot(variaveis_fixas, valores_fixos, 
                              min_tg=0.2, max_tg=1.0, 
                              min_corr=200, max_corr=2000, 
                              min_temp=20, max_temp=40,
                              min_temp_ext=20, max_temp_ext=40,
                              passos=30, caminho_modelo=CAMINHO_PADRAO_MODELO):
    """
    Gera uma superfície 3D fixando uma variável e variando as outras duas.
    Salva a figura na mesma pasta do modelo .pkl.
    """
    # 1. Carregamento do modelo preditivo
    try:
        modelo = joblib.load(caminho_modelo)
    except FileNotFoundError:
        print(f"Erro: O arquivo {caminho_modelo} não foi encontrado.")
        return

    # --- Lógica de diretório para salvamento ---
    # Extrai a pasta onde o modelo está (ex: 'modelos/meu_modelo.pkl' -> 'modelos')
    diretorio_destino = os.path.dirname(caminho_modelo)
    # Define um nome de arquivo dinâmico baseado nas variáveis fixas
    nome_img = f"superficie_{variaveis_fixas[0]}_{variaveis_fixas[1]}.png"
    caminho_salvamento = os.path.join(diretorio_destino, nome_img)
    # -------------------------------------------

    limites = {
        'tangente_perdas': (min_tg, max_tg),
        'corrente_primario': (min_corr, max_corr),
        'temperatura_ambiente': (min_temp, max_temp),
        'ponto_quente_externo': (min_temp_ext, max_temp_ext)
    }
    
    nomes_exibicao = {
        'tangente_perdas': 'Tangente de Perdas (%)',
        'corrente_primario': 'Corrente Primário (A)',
        'temperatura_ambiente': 'Temp. Ambiente (°C)',
        'ponto_quente_externo': 'Ponto Quente Ext. (°C)'
    }
    
    chaves_livres = [k for k in limites.keys() if k not in variaveis_fixas]
    
    if len(chaves_livres) != 2:
        raise ValueError("Você deve passar exatamente 2 variáveis fixas para um gráfico 3D.")
        
    eixo_x_nome = chaves_livres[0]
    eixo_y_nome = chaves_livres[1]

    x_vals = np.linspace(limites[eixo_x_nome][0], limites[eixo_x_nome][1], passos)
    y_vals = np.linspace(limites[eixo_y_nome][0], limites[eixo_y_nome][1], passos)
    X_mesh, Y_mesh = np.meshgrid(x_vals, y_vals)

    dados_input = {
        eixo_x_nome: X_mesh.ravel(),
        eixo_y_nome: Y_mesh.ravel(),
        variaveis_fixas[0]: np.full(X_mesh.size, valores_fixos[0]),
        variaveis_fixas[1]: np.full(X_mesh.size, valores_fixos[1])
    }
    df_pred = pd.DataFrame(dados_input)

    colunas_treino = ['tangente_perdas', 'corrente_primario', 'temperatura_ambiente', 'ponto_quente_externo']
    df_pred = df_pred[colunas_treino]

    Z_flat = modelo.predict(df_pred)
    Z_mesh = Z_flat.reshape(X_mesh.shape)

    # --- Lógica de Destaque para > 80°C ---
    limite_critico = 80
    
    # Criamos um colormap que combina uma paleta suave com uma cor de alerta
    # 'coolwarm' para a base, mas os valores acima do limite serão destacados
    cmap_base = cm.coolwarm
    
    # Definimos a normalização: valores abaixo de 80 usam a escala normal, 
    # valores acima ficam no topo da escala (ou podemos usar um TwoSlopeNorm)
    norm = colors.TwoSlopeNorm(vmin=Z_mesh.min() if Z_mesh.min() < limite_critico else limite_critico - 10, 
                               vcenter=limite_critico, 
                               vmax=Z_mesh.max() if Z_mesh.max() > limite_critico else limite_critico + 10)
    # -------------------------------------

    # Plotagem
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Aplicamos a 'norm' e o 'cmap'
    surf = ax.plot_surface(X_mesh, Y_mesh, Z_mesh, 
                           cmap=cmap_base,
                           norm=norm, # A mágica acontece aqui
                           linewidth=0.1, 
                           edgecolors='gray', # Adiciona uma malha fina para melhor percepção
                           antialiased=True, 
                           alpha=0.9)

    # Adicionar uma linha de contorno (Isolinha) exatamente em 80°C para marcar o limite no plano
    ax.contour(X_mesh, Y_mesh, Z_mesh, levels=[limite_critico], colors=['black'], 
               linewidths=3, linestyles='dashed', offset=Z_mesh.min())

    ax.set_xlabel(nomes_exibicao[eixo_x_nome])
    ax.set_ylabel(nomes_exibicao[eixo_y_nome])
    ax.set_zlabel('Hotspot Inferido (°C)')

    txt_fixo = f"{nomes_exibicao[variaveis_fixas[0]]}={valores_fixos[0]} | {nomes_exibicao[variaveis_fixas[1]]}={valores_fixos[1]}"
    plt.title(f'Análise de Superfície Térmica\nCondições Fixas: {txt_fixo}')

    fig.colorbar(surf, shrink=0.5, aspect=10, label='Temp. Hotspot (°C)')
    plt.tight_layout()

    # SALVAR A FIGURA
    # O dpi=300 garante boa qualidade; bbox_inches='tight' evita cortes nas bordas
    plt.savefig(caminho_salvamento, dpi=300, bbox_inches='tight')
    print(f"Sucesso: Gráfico salvo em '{caminho_salvamento}'")

    plt.show()

# --- Exemplo de Uso e Execução ---
if __name__ == "__main__":
    caminho_dados_ods = '/home/joao/Documents/GitHub/PeD-Power-Solis/modeling/Dados_Lab_550.ods'

    # 1. Selecionar o melhor grau polinomial (graus 1–5)
    resultado = selecionar_melhor_grau(
        caminho_dados=caminho_dados_ods,
        metrica_principal='r2_adj',   # pode ser 'rmse' ou 'mae'
        verbose=True
    )
    melhor_grau = resultado['melhor_grau']

    # 2. Treinar e salvar o modelo definitivo com o melhor grau encontrado
    treinar_e_salvar_modelo(
        caminho_dados=caminho_dados_ods,
        caminho_arquivo=CAMINHO_PADRAO_MODELO,
        grau=melhor_grau
    )

    # 3. Testar uma inferência
    tg_perdas = 0.3
    corrente = 1500
    temp_amb = 30
    ponto_externo = 30

    temp_estimada = inferir_temperatura(tg_perdas, corrente, temp_amb, ponto_externo)
    print(f"\nPara Tg(δ)={tg_perdas}%, I={corrente}A, Temp. Amb.={temp_amb}°C, Ext.={ponto_externo}°C:")
    print(f"Temperatura Hotspot inferida: {temp_estimada:.2f} °C")

    # 4. Exemplo de plotagem
    plotar_superficie_hotspot(
        variaveis_fixas=['temperatura_ambiente', 'ponto_quente_externo'],
        valores_fixos=[35, 35],
        passos=40
    )
    
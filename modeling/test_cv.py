import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

df = pd.read_excel('/home/joao/Documents/GitHub/PeD-Power-Solis/modeling/Dados_Lab_245.ods', engine='odf')
df.columns = [str(c).strip() for c in df.columns]
df = df.rename(columns={
    'Tangente de Perdas (%)': 'tangente_perdas',
    'Corrente Aplicada (A)': 'corrente_primario',
    'Temperatura Ambiente (ºC)': 'temperatura_ambiente',
    'Ponto Quente Externo (ºC)': 'ponto_quente_externo',
    'Hot spot': 'temperatura_hotspot'
})

for col in ['tangente_perdas', 'corrente_primario', 'temperatura_ambiente', 'temperatura_hotspot']:
    if col in df.columns and df[col].dtype == object:
        df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

X = df[['tangente_perdas', 'corrente_primario', 'temperatura_ambiente', 'ponto_quente_externo']]
y = df['temperatura_hotspot']

n_amostras = len(y)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

for grau in range(1, 6):
    modelo = Pipeline([
        ('scaler', MinMaxScaler()),
        ('poly', PolynomialFeatures(degree=grau, include_bias=False)),
        ('linear', LinearRegression())
    ])
    y_pred = cross_val_predict(modelo, X, y, cv=kf)
    r2 = r2_score(y, y_pred)
    n_features = PolynomialFeatures(degree=grau, include_bias=False).fit(X).n_output_features_
    denom = (n_amostras - n_features - 1)
    r2_adj = 1 - (1 - r2) * (n_amostras - 1) / denom if denom != 0 else float('nan')
    print(f"Grau {grau}: R2={r2:.4f}, R2_adj={r2_adj:.4f}")

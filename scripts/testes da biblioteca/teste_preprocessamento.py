# import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# import preprocessing.feature_extration as feature_extration
import modeling.model_aging as aging
import modeling.model_hotspot as hotspot

# --- Exemplo de Uso ---
# Simulando o mesmo cenário: operação a 105 °C durante 8736 horas (1 ano)
# Usando as premissas de Montsinger: Temp. Ref = 85 °C, Vida Ref = 25 anos, p = 8 °C

#%%
resultado = aging.calcular_perda_vida_util_base2(temperatura_hotspot=105, horas_operacao=8736)

print(f"Temperatura do Hotspot: {resultado['temperatura_hotspot_C']} °C")
print(f"Fator de Aceleração (FAA): {resultado['fator_aceleracao']}x (envelhece {resultado['fator_aceleracao']} vezes mais rápido)")
print(f"Expectativa de vida total nesta temperatura: {resultado['expectativa_vida_atual_anos']} anos")
print(f"Horas reais operadas: {resultado['horas_reais_operadas']} h")
print(f"Desgaste equivalente a {resultado['temperatura_hotspot_C']}°C corresponde a operar {resultado['horas_equivalentes_a_95C']} h a 95°C")
print(f"Perda de vida útil: {resultado['percentual_vida_perdida']} %")

#%%

resultado = hotspot.selecionar_melhor_grau(
    caminho_dados='/home/joao/Documents/GitHub/PeD-Power-Solis/modeling/Dados_Lab_550.ods',
    graus=[2, 3, 4],          # padrão
    metrica_principal='mae',      # ou 'rmse' ou 'mae'
    verbose=True
)

temp = hotspot.inferir_temperatura(tangente_perdas = 0.7, corrente_primario = 2000, 
                                  temperatura_ambiente = 20, ponto_externo = 20, caminho_arquivo='/home/joao/Documents/GitHub/PeD-Power-Solis/modeling/avaliacao_graus/modelo_grau_2.pkl')
print(f"Temperatura do Hotspot inferida: {temp}°C")

hotspot.plotar_superficie_hotspot(variaveis_fixas=['temperatura_ambiente', 'ponto_quente_externo'], 
                                  valores_fixos=[40.0, 100.0], 
                                  min_tg=0.2, max_tg=1.0, 
                                  min_corr=200, max_corr=2000, 
                                  min_temp=20, max_temp=40, 
                                  min_temp_ext=20, max_temp_ext=40, 
                                  passos=30, 
                                  caminho_modelo='/home/joao/Documents/GitHub/PeD-Power-Solis/modeling/avaliacao_graus/modelo_grau_2.pkl')

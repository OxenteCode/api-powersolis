# import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..', '..')))
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

hotspot.treinar_e_salvar_modelo(caminho_arquivo='modelo_hotspot_2.pkl', grau=2)
hotspot.treinar_e_salvar_modelo(caminho_arquivo='modelo_hotspot_3.pkl', grau=3)

temp = hotspot.inferir_temperatura(tangente_perdas = 0.7, corrente_primario = 200, 
                                   temperatura_ambiente = 30, caminho_arquivo='modelo_hotspot_3.pkl')

print(f"Temperatura do Hotspot inferida: {temp}°C")

hotspot.plotar_superficie_hotspot('temperatura_ambiente', 40, 
                              min_tg=0.2, max_tg=1.0, 
                              min_corr=200, max_corr=400, 
                              min_temp=20, max_temp=40, 
                              passos=30, caminho_modelo='modelo_hotspot_3.pkl')

# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 20:16:59 2026

@author: engjo
"""


def calcular_perda_vida_util_base2(temperatura_hotspot, horas_operacao, temp_ref=85, vida_ref_anos=25, p=8):
    """
    Estima a perda de vida útil de um equipamento usando a regra 
    de duplicação da taxa de envelhecimento a cada 'p' graus (Base 2).
    
    Parâmetros:
    temperatura_hotspot (float): Temperatura atual do ponto mais quente em °C (θp).
    horas_operacao (float): Tempo de operação nessa temperatura (em horas).
    temp_ref (float): Temperatura de referência em °C (θref). Padrão = 95 °C.
    vida_ref_anos (float): Vida útil esperada na temperatura de referência (Lref). Padrão = 16 anos.
    p (float): Incremento de temperatura que reduz a vida pela metade. Padrão = 8 °C.
    
    Retorna:
    dict: Dicionário com os resultados do cálculo.
    """
    
    # 1. Cálculo da Vida Útil Esperada na temperatura atual (expoente negativo)
    # L(θ) = Lref * 2^(- (θp - θref) / p)
    vida_util_anos = vida_ref_anos * (2 ** (-(temperatura_hotspot - temp_ref) / p))
    vida_util_horas = vida_util_anos * 8760  # Convertendo para horas (1 ano = 8760h)
    
    # 2. Cálculo do Fator de Aceleração de Envelhecimento (expoente positivo)
    # FAA = 2^( (θp - θref) / p )
    fator_aceleracao = 2 ** ((temperatura_hotspot - temp_ref) / p)
    
    # Horas equivalentes de operação na temperatura de referência
    horas_equivalentes_ref = horas_operacao * fator_aceleracao
    
    # 3. Cálculo da porcentagem de vida perdida
    percentual_perda = (horas_operacao / vida_util_horas) * 100
    
    return {
        "temperatura_hotspot_C": temperatura_hotspot,
        "fator_aceleracao": round(fator_aceleracao, 2),
        "expectativa_vida_atual_anos": round(vida_util_anos, 2),
        "horas_reais_operadas": horas_operacao,
        "horas_equivalentes_a_95C": round(horas_equivalentes_ref, 2),
        "percentual_vida_perdida": round(percentual_perda, 4)
    }

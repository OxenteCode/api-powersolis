import pandas as pd
import numpy as np

# %% DEFINIÇÃO DE FUNÇÕES DE PRE-PROCESSAMENTO
 
def perda_dieletrica (tg, rms_corrente, rms_tensao):
    # as variáveis de entrada são floats
 
    C = capacitancia(tg, rms_corrente, rms_tensao)
    perda = 2*np.pi*60*C*(rms_tensao**2)*tg
    
    return perda

def capacitancia (tg, rms_corrente, rms_tensao):
    # as variáveis de entrada são floats
 
    cap = rms_corrente/(2*np.pi*60*rms_tensao*np.sqrt(1+tg**2))
 
    return cap

def variacao_tan_perdas (tg, anos, janela):
    # tg é um vetor com vários valores de tg;
    # anos é o rótulo do ano em que cada valor de tangente foi medido

    tg = np.asarray(tg, dtype=float)
    anos = np.asarray(anos,dtype=float)

    #Variação geral
    x0 = tg[0]
    xn = tg[-1]
    delta = anos[-1] - anos[0]
    tendencia = (xn/x0)**(1/delta) -1

    #Variação curto prazo
    ano_final = anos[-1]
    ano_limite = ano_final - janela
    pontos_curto = anos >= ano_limite
    anos_curto = anos[pontos_curto]
    tg_curto = tg[pontos_curto]

    x0_curto = tg_curto[0]
    xn_curto = tg_curto[-1]
    dt_curto = anos_curto[-1] - anos_curto[0]
    tendencia_curto = (xn_curto/x0_curto)**(1 / dt_curto)- 1
    return tendencia, tendencia_curto

def variacao_capacitancia (cap, anos, janela):
    # cap é um vetor com vários valores de cap;
    # anos é o rótulo do ano em que cada valor de capacitância foi medido
    
    cap = np.asarray(cap, dtype=float)
    anos = np.asarray(anos,dtype=float)

    #Variação geral
    x0 = cap[0]
    xn = cap[-1]
    delta = anos[-1] - anos[0]
    tendencia = (xn / x0)**(1/delta) - 1

    #Variação curto prazo
    ano_final = anos[-1]
    ano_limite = ano_final - janela
    pontos_curto = anos >= ano_limite
    anos_curto = anos[pontos_curto]
    cap_curto = cap[pontos_curto]

    x0_curto = cap_curto[0]
    xn_curto = cap_curto[-1]
    dt_curto = anos_curto[-1] - anos_curto[0]
    tendencia_curto = (xn_curto/x0_curto)**(1 / dt_curto) - 1
    return tendencia, tendencia_curto

def variacao_isolamento (resistencia, anos, janela):
    # resistencia é uma matriz com vários valores de resistência do isolamento. Pode possuir várias 
    #linhas (anos de medição) e colunas (resitencias medidas em diferentes pontos. 
    #Ex.: alta para terra e alta para baixa);
    # anos é o rótulo do ano em que cada medição foi feita (cada linha)
    # deve ser calculada uma variação para cada coluna

    resistencia = np.asarray(resistencia, dtype=float)
    anos = np.asarray(anos,dtype=float)

    #Variação geral
    delta = anos[-1] - anos[0]
    n_colunas = resistencia.shape[1]
    tendencias = []

    for j in range(n_colunas):
        x0 = resistencia[0, j]
        xn = resistencia[-1, j]
        tendencia = (xn/x0)**(1/delta) - 1
        tendencias.append(tendencia)

    # Variação curto prazo
    ano_final = anos[-1]
    ano_limite = ano_final - janela
    pontos_curto = anos >= ano_limite
    anos_curto = anos[pontos_curto]
    resistencia_curto = resistencia[pontos_curto, :]

    dt_curto = anos_curto[-1] - anos_curto[0]
    tendencias_curto = []

    for j in range(n_colunas):
        x0_curto = resistencia_curto[0, j]
        xn_curto = resistencia_curto[-1, j]
        tendencia_curto = (xn_curto/x0_curto)**(1/dt_curto) -1
        tendencias_curto.append(tendencia_curto)
     
    return tendencias, tendencias_curto

def variacao_enrolamento (resistencia, anos, janela):
    # resistencia é uma matriz com vários valores de resistência do enrolamento. Pode possuir várias 
    #linhas (anos de medição) e colunas (resitencias medidas em diferentes enrolamentos. 
    # deve ser calculada uma variação para cada coluna
    
    resistencia = np.asarray(resistencia, dtype=float)
    anos = np.asarray(anos, dtype=float)

    delta = anos[-1] -anos[0]
    n_colunas = resistencia.shape[1]
    tendencias = []

    for j in range(n_colunas):
        x0 = resistencia[0, j]
        xn = resistencia[-1, j]
        tendencia = (xn/ x0)**(1/delta) -1
        tendencias.append(tendencia)
     
    #variação curto prazo
    ano_final = anos[-1]
    ano_limite = ano_final - janela
    pontos_curto = anos >= ano_limite
    anos_curto = anos[pontos_curto]
    resistencia_curto = resistencia[pontos_curto, :]

    dt_curto = anos_curto[-1] -anos_curto[0]
    tendencias_curto = []

    for j in range(n_colunas):
        x0_curto = resistencia_curto[0, j]
        xn_curto = resistencia_curto[-1, j]
        tendencia_curto = (xn_curto /x0_curto)**(1/dt_curto) -1
        tendencias_curto.append(tendencia_curto)

    return tendencias, tendencias_curto
 

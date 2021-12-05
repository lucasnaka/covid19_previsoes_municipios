# Importa bibliotecas

import os
import pandas as pd
import time

# Define funções para corrigir a coluna de óbitos acumulados e de óbitos diários
def fix_number_accumulated_deaths(obitos_novos, obitos_acumulado, index, chave, nivel, df):
    if obitos_novos >= 0:
        if (index + 1) < df.shape[0] and (
                (df[f'{nivel}'].iloc[index - 1] and df[f'{nivel}'].iloc[index + 1]) == chave):
            obitos_acumulado_corrigido = (df['obitosAcumulado'].iloc[index - 1] + df['obitosAcumulado'].iloc[
                index + 1]) / 2
            if obitos_novos > 10 * obitos_acumulado_corrigido:
                return int(obitos_acumulado_corrigido + 0.5)
            else:
                return int(obitos_acumulado + 0.5)
        else:
            return int(obitos_acumulado + 0.5)
    else:
        if (index + 1) < df.shape[0] and (
                (df[f'{nivel}'].iloc[index - 1] and df[f'{nivel}'].iloc[index + 1]) == chave):
            obitos_acumulado_corrigido = (df['obitosAcumulado'].iloc[index - 1] + df['obitosAcumulado'].iloc[
                index + 1]) / 2
            return int(obitos_acumulado_corrigido + 0.5)
        elif (index + 1) < df.shape[0] and (df[f'{nivel}'].iloc[index - 1] == chave) and (
                df[f'{nivel}'].iloc[index + 1] != chave):
            return int(df['obitosAcumulado'].iloc[index - 1] + 0.5)
        elif (index + 1) < df.shape[0] and (df[f'{nivel}'].iloc[index - 1] != chave) and (
                df[f'{nivel}'].iloc[index + 1] == chave):
            return int(df['obitosAcumulado'].iloc[index + 1] + 0.5)
        else:
            return int(obitos_acumulado + 0.5)


def fix_number_of_daily_deaths(obitos_acumulado, index, chave, nivel, df):
    if df[f'{nivel}'].iloc[index - 1] == chave:
        obitos_novos = (obitos_acumulado - df['obitosAcumulado'].iloc[index - 1])
        return int(obitos_novos)
    else:
        return obitos_acumulado

# Concatena as partes do dataframe
tempo_inicial = time.time()
path = 'data/'
files = os.listdir(path)
list_dfs = [pd.read_csv(path + file, sep=';') for file in files]
df = pd.concat(list_dfs)
df = df.drop(columns=['Recuperadosnovos', 'emAcompanhamentoNovos'])

# Salva o csv de município corrigido
df_mun = df[~df['municipio'].isna() & (df['data'].notna())]
df_mun = df_mun.sort_values(by=['codmun', 'data'], ascending=[True, True]).reset_index(drop=True)
df_mun = df_mun.reset_index()

df_mun['obitosAcumulado'] = df_mun.apply(
    lambda x: fix_number_accumulated_deaths(x['obitosNovos'], x['obitosAcumulado'], x['index'], x['codmun'], 'codmun',
                                            df_mun),
    axis=1)
df_mun['obitosNovos'] = df_mun.apply(
    lambda x: fix_number_of_daily_deaths(x['obitosAcumulado'], x['index'], x['codmun'], 'codmun', df_mun),
    axis=1)

df_mun.to_csv('data/df_mun.csv', index=False)

# Salva o csv de estado corrigido
df_uf = df[(df['codmun'].isna()) & (df['estado'].notna()) & (df['data'].notna())]
df_uf = df_uf.sort_values(by=['estado', 'data'], ascending=[True, True]).reset_index(drop=True)
df_uf = df_uf.reset_index()

df_uf['obitosAcumulado'] = df_uf.apply(
    lambda x: fix_number_accumulated_deaths(x['obitosNovos'], x['obitosAcumulado'], x['index'], x['estado'], 'estado',
                                            df_uf),
    axis=1)
df_uf['obitosNovos'] = df_uf.apply(
    lambda x: fix_number_of_daily_deaths(x['obitosAcumulado'], x['index'], x['estado'], 'estado', df_uf),
    axis=1)

df_uf.to_csv('data/df_uf.csv', index=False)

# Salva o csv de regional de saúde corrigido
df_regional_saude = df[(df['municipio'].notna()) & (df['codRegiaoSaude'].notna()) & (df['data'].notna())]
df_regional_saude = df_regional_saude.groupby(['codRegiaoSaude', 'data'], as_index=False).agg(
    {'codRegiaoSaude': 'first', 'data': 'first', 'casosNovos': 'sum', 'casosAcumulado': 'sum',
     'obitosNovos': 'sum', 'obitosAcumulado': 'sum'})
df_regional_saude = df_regional_saude.sort_values(by=['codRegiaoSaude', 'data'], ascending=[True, True]).reset_index(
    drop=True)
df_regional_saude = df_regional_saude.reset_index()

df_regional_saude['obitosAcumulado'] = df_regional_saude.apply(
    lambda x: fix_number_accumulated_deaths(x['obitosNovos'], x['obitosAcumulado'], x['index'], x['codRegiaoSaude'],
                                            'codRegiaoSaude',
                                            df_regional_saude),
    axis=1)
df_regional_saude['obitosNovos'] = df_regional_saude.apply(
    lambda x: fix_number_of_daily_deaths(x['obitosAcumulado'], x['index'], x['codRegiaoSaude'],
                                         'codRegiaoSaude',
                                         df_regional_saude), axis=1)

df_regional_saude.to_csv('data/df_regional_saude.csv', index=False)

# Salva o csv de regional corrigido
df_regional = df[(df['codmun'].isna()) & (df['estado'].notna()) & (df['data'].notna())]
df_regional = df_regional.groupby(['regiao', 'data'], as_index=False).agg({'regiao': 'first', 'data': 'first',
                                                                           'casosNovos': 'sum', 'casosAcumulado': 'sum',
                                                                           'obitosNovos': 'sum',
                                                                           'obitosAcumulado': 'sum'})
df_regional = df_regional.sort_values(by=['regiao', 'data'], ascending=[True, True]).reset_index(drop=True)
df_regional = df_regional.reset_index()

df_regional['obitosAcumulado'] = df_regional.apply(
    lambda x: fix_number_accumulated_deaths(x['obitosNovos'], x['obitosAcumulado'], x['index'], x['regiao'], 'regiao',
                                            df_regional), axis=1)
df_regional['obitosNovos'] = df_regional.apply(
    lambda x: fix_number_of_daily_deaths(x['obitosAcumulado'], x['index'], x['regiao'], 'regiao',
                                         df_regional), axis=1)

df_regional.to_csv('data/df_regional.csv', index=False)

# Salva o csv de Brasil corrigido
df_brasil = df[(df['estado'].isna()) & (df['data'].notna())]
df_brasil = df_brasil.sort_values(by=['data'], ascending=True).reset_index(drop=True)
df_brasil = df_brasil.reset_index()

df_brasil.to_csv('data/df_brasil.csv', index=False)

tempo_final = time.time()
print(tempo_final)
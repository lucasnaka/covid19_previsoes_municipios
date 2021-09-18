import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns


# Cria função para plotar gráficos de valores e medidas móveis
def plotar_serie_temporal(titulo, rotulo_y, variavel, media_movel_variavel, df):
    fig, ax = plt.subplots(figsize=(15, 7))
    sns.lineplot(ax=ax, x='data', y=variavel, data=df, label='Casos').set_title(titulo)
    sns.lineplot(ax=ax, x='data', y=media_movel_variavel, data=df, label='Média móvel')
    plt.xlabel('Data')
    plt.ylabel(rotulo_y)
    plt.show()


# Carrega os dados da covid saude concatenados e dropa as colunas nulas
path = 'covid_saude/'
files = os.listdir(path)
lista_dfs = [pd.read_csv(path + file, sep=';') for file in files]
df_final = pd.concat(lista_dfs)
df_final = df_final.drop(columns=['Recuperadosnovos', 'emAcompanhamentoNovos'])

# Dropa os casos em que o municio é vazio, cria a coluna com a taxa de letalidade e preenche os campos nulos com zero
df_final = df_final[~df_final['municipio'].isna()]
df_final['taxa_de_letalidade'] = df_final['obitosAcumulado'] / df_final['casosAcumulado']
df_final['taxa_de_letalidade'] = df_final['taxa_de_letalidade'].fillna(0)

# Printa total de casos, de óbitos, de óbitos nas últimas 24hrs e taxa de letalidade em percentual
print(f'Total de casos: {df_final.casosNovos.sum()}')
print(f'Total de óbitos: {df_final.obitosNovos.sum()}')
print(f"Total de óbitos nas últimas 24hrs: {df_final[df_final['data'] == df_final['data'].max()].casosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df_final.obitosNovos.sum() / df_final.casosNovos.sum() * 100, 2)}%")

# Cria as colunas com as médias móveis de casos, óbitos e letalidade
df_final['media_movel_casos'] = df_final.groupby('codmun')['casosNovos'].transform(lambda x: x.rolling(7, 1).mean())
df_final['media_movel_obitos'] = df_final.groupby('codmun')['obitosNovos'].transform(lambda x: x.rolling(7, 1).mean())
df_final['media_movel_letalidade'] = df_final.groupby('codmun')['taxa_de_letalidade'].transform(
    lambda x: x.rolling(7, 1).mean())

# Define UF para plotar os gráficos diários de casos, óbitos e letalidade
uf = 'SP'
df_final_uf = df_final[df_final['estado'] == uf]
df_final_uf['data'] = pd.to_datetime(df_final_uf['data'], format='%Y-%m-%d')
df_final_plot = df_final_uf.groupby(['data'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'casosAcumulado', 'obitosAcumulado',
     'media_movel_casos', 'media_movel_obitos']].sum()
df_final_plot['taxa_de_letalidade'] = df_final_plot['obitosAcumulado'] / df_final_plot['casosAcumulado']
df_final_plot['taxa_de_letalidade'] = df_final_plot['taxa_de_letalidade'].fillna(0)
df_final_plot['media_movel_letalidade'] = df_final_plot['taxa_de_letalidade'].transform(
    lambda x: x.rolling(7, 1).mean())

plotar_serie_temporal(f'Número de casos de covid confirmados em {uf}', 'Número de casos', 'casosNovos',
                      'media_movel_casos', df_final_plot)
plotar_serie_temporal(f'Número de óbitos de covid em {uf}', 'Número de óbitos', 'obitosNovos', 'media_movel_obitos',
                      df_final_plot)
plotar_serie_temporal(f'Taxa de letalidade por covid em {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'media_movel_letalidade', df_final_plot)

# Define municipio para plotar os gráficos diários de casos, óbitos e letalidade
municipio = 'São Carlos'
df_final_sc = df_final_uf[df_final_uf['municipio'] == municipio]
plotar_serie_temporal(f'Número de casos de covid confirmados em {municipio} - {uf}', 'Número de casos', 'casosNovos',
                      'media_movel_casos',
                      df_final_sc)
plotar_serie_temporal(f'Número de óbitos de covid em {municipio} - {uf}', 'Número de óbitos', 'obitosNovos',
                      'media_movel_obitos', df_final_sc)
plotar_serie_temporal(f'Taxa de letalidade por covid em {municipio} - {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'media_movel_letalidade', df_final_plot)
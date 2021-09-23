import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns


def adiciona_zero_a_esquerda(string):
    if len(string) == 1:
        return '0' + string
    else:
        return string


# Cria função para plotar gráficos de valores e medidas móveis
def plotar_serie_temporal(titulo, rotulo_y, variavel, media_movel_variavel, df):
    fig, ax = plt.subplots(figsize=(15, 7))
    sns.lineplot(ax=ax, x='data', y=variavel, data=df, label='Casos').set_title(titulo)
    sns.lineplot(ax=ax, x='data', y=media_movel_variavel, data=df, label='Média móvel')
    plt.xlabel('Data')
    plt.ylabel(rotulo_y)
    plt.show()


def plotar_grafico_barras(titulo, rotulo_x, rotulo_y, variavel_x, variavel_y, variavel_linha, df):
    sns.set_theme(style="whitegrid", rc=None)
    fig, ax1 = plt.subplots(figsize=(15, 7))
    sns.barplot(x=variavel_x, y=variavel_y, data=df, palette="Blues_d", ax=ax1).set_title(titulo)
    ax2 = ax1.twinx()
    sns.lineplot(x=variavel_x, y=variavel_linha, data=df, sort=False, color='black',ax=ax2)
    plt.xlabel(rotulo_x)
    plt.ylabel(rotulo_y)
    plt.show()


# Carrega os dados da covid saude concatenados e dropa as colunas nulas
path = 'covid_saude/'
files = os.listdir(path)
lista_dfs = [pd.read_csv(path + file, sep=';') for file in files]
df = pd.concat(lista_dfs)
df = df.drop(columns=['Recuperadosnovos', 'emAcompanhamentoNovos'])

# Dropa os casos em que o municio é vazio, cria a coluna com a taxa de letalidade e preenche os campos nulos com zero
df = df[~df['municipio'].isna()]
df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d')
df['ano'] = pd.DatetimeIndex(df['data']).year
df['ano'] = df['ano'].astype('str')
df['semanaEpi'] = df['semanaEpi'].astype('str')
df['semanaEpi'] = df.apply(lambda x: adiciona_zero_a_esquerda(x['semanaEpi']), axis=1)
df['semana_ano'] = df['ano'] + df['semanaEpi']
df['taxa_de_letalidade'] = df['obitosAcumulado'] / df['casosAcumulado']
df['taxa_de_letalidade'] = df['taxa_de_letalidade'].fillna(0)

# Printa total de casos, de óbitos, de óbitos nas últimas 24hrs e taxa de letalidade em percentual
print(f'Total de casos: {df.casosNovos.sum()}')
print(f'Total de óbitos: {df.obitosNovos.sum()}')
print(f"Total de óbitos nas últimas 24hrs: {df[df['data'] == df['data'].max()].casosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df.obitosNovos.sum() / df.casosNovos.sum() * 100, 2)}%")

# Cria as colunas com as médias móveis de casos, óbitos e letalidade
df['media_movel_casos'] = df.groupby('codmun')['casosNovos'].transform(lambda x: x.rolling(7, 1).mean())
df['media_movel_obitos'] = df.groupby('codmun')['obitosNovos'].transform(lambda x: x.rolling(7, 1).mean())
df['media_movel_letalidade'] = df.groupby('codmun')['taxa_de_letalidade'].transform(
    lambda x: x.rolling(7, 1).mean())

# Define UF para plotar os gráficos diários de casos, óbitos e letalidade
uf = 'SP'
df_uf = df[df['estado'] == uf]
print(f'Total de casos: {df_uf.casosNovos.sum()}')
print(f'Total de óbitos: {df_uf.obitosNovos.sum()}')
print(f"Total de casos nas últimas 24hrs: {df_uf[df_uf['data'] == df_uf['data'].max()].casosNovos.sum()}")
print(f"Total de óbitos nas últimas 24hrs: {df_uf[df_uf['data'] == df_uf['data'].max()].obitosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df_uf.obitosNovos.sum() / df_uf.casosNovos.sum() * 100, 2)}%")
df_plot = df_uf.groupby(['data'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'casosAcumulado', 'obitosAcumulado',
     'media_movel_casos', 'media_movel_obitos']].sum()
df_plot['taxa_de_letalidade'] = df_plot['obitosAcumulado'] / df_plot['casosAcumulado']
df_plot['taxa_de_letalidade'] = df_plot['taxa_de_letalidade'].fillna(0)
df_plot['media_movel_letalidade'] = df_plot['taxa_de_letalidade'].transform(
    lambda x: x.rolling(7, 1).mean())

plotar_serie_temporal(f'Número de casos de covid confirmados em {uf}', 'Número de casos', 'casosNovos',
                      'media_movel_casos', df_plot)
plotar_serie_temporal(f'Número de óbitos de covid em {uf}', 'Número de óbitos', 'obitosNovos', 'media_movel_obitos',
                      df_plot)
plotar_serie_temporal(f'Taxa de letalidade por covid em {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'media_movel_letalidade', df_plot)

# Define municipio para plotar os gráficos diários de casos, óbitos e letalidade
municipio = 'São Carlos'
df_mun = df_uf[df_uf['municipio'] == municipio]
print(f'Total de casos: {df_mun.casosNovos.sum()}')
print(f'Total de óbitos: {df_mun.obitosNovos.sum()}')
print(f"Total de óbitos nas últimas 24hrs: {df_mun[df_mun['data'] == df_mun['data'].max()].casosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df_mun.obitosNovos.sum() / df_mun.casosNovos.sum() * 100, 2)}%")
plotar_serie_temporal(f'Número de casos de covid confirmados em {municipio} - {uf}', 'Número de casos', 'casosNovos',
                      'media_movel_casos',
                      df_mun)
plotar_serie_temporal(f'Número de óbitos de covid em {municipio} - {uf}', 'Número de óbitos', 'obitosNovos',
                      'media_movel_obitos', df_mun)
plotar_serie_temporal(f'Taxa de letalidade por covid em {municipio} - {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'media_movel_letalidade', df_mun)

df_mun_semanal = df_mun.groupby(['semana_ano'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'casosAcumulado', 'obitosAcumulado',
     'media_movel_casos', 'media_movel_obitos']].sum()

df_mun_semanal['index'] = range(1, len(df_mun_semanal) + 1)

plotar_grafico_barras(f'Número de casos e óbitos por covid em {municipio} - {uf} por semana', 'Semana',
                      'Número de óbitos',
                      'index', 'casosNovos','obitosNovos', df_mun_semanal)

#Create combo chart
fig, ax1 = plt.subplots(figsize=(10,6))
color = 'tab:green'
#bar plot creation
ax1.set_title('Average Percipitation Percentage by Month', fontsize=16)
ax1.set_xlabel('Month', fontsize=16)
ax1.set_ylabel('Avg Temp', fontsize=16)
ax1 = sns.barplot(x='index', y='casosNovos', data = df_mun_semanal, palette='summer')
ax1.tick_params(axis='y')
#specify we want to share the same x-axis
ax2 = ax1.twinx()
color = 'tab:red'
#line plot creation
ax2.set_ylabel('Avg Percipitation %', fontsize=16)
ax2 = sns.lineplot(x='index', y='obitosNovos', data = df_mun_semanal, sort=False, color=color)
ax2.tick_params(axis='y', color=color)
#show plot
plt.show()

sns.set_theme(style="whitegrid", rc=None)
sns.barplot(x=df_mun_semanal.index.tolist(),
            y=df_mun_semanal.obitosNovos.tolist())  # .set_title(f'Número de óbitos de covid em {municipio} - {uf} por semana')
# plt.xlabel('Semana')
# plt.ylabel('Número de óbitos')
plt.show()

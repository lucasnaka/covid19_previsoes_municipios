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
def plotar_serie_temporal(titulo, rotulo_y, variavel, label, df, media_movel_variavel=None, media_movel=True,
                          label_flag=True):
    fig, ax = plt.subplots(figsize=(15, 7))
    if label_flag:
        sns.lineplot(ax=ax, x='data', y=variavel, data=df, label=label).set_title(titulo)
    else:
        sns.lineplot(ax=ax, x='data', y=variavel, data=df).set_title(titulo)
    if media_movel:
        sns.lineplot(ax=ax, x='data', y=media_movel_variavel, data=df, label='Média móvel')
    plt.xlabel('Data')
    plt.ylabel(rotulo_y)
    plt.show()


def plotar_grafico_barras(titulo, rotulo_x, rotulo_y, variavel_x, variavel_y, df, media_movel_variavel=None,
                          media_movel=True):
    sns.set_theme(style="whitegrid", rc=None)
    fig, ax1 = plt.subplots(figsize=(15, 7))
    sns.barplot(x=variavel_x, y=variavel_y, data=df, palette="Blues_d", ax=ax1).set_title(titulo)
    if media_movel:
        sns.lineplot(ax=ax1, x=variavel_x, y=media_movel_variavel, data=df, label='Média móvel')
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
df['mes'] = pd.DatetimeIndex(df['data']).month
df['mes'] = df['mes'].astype('str')
df['ano'] = pd.DatetimeIndex(df['data']).year
df['ano'] = df['ano'].astype('str')
df['semanaEpi'] = df['semanaEpi'].astype('str')
df['semanaEpi'] = df.apply(lambda x: adiciona_zero_a_esquerda(x['semanaEpi']), axis=1)
df['mes'] = df.apply(lambda x: adiciona_zero_a_esquerda(x['mes']), axis=1)
df['semana_ano'] = df['ano'] + df['semanaEpi']
df['mes_ano'] = df['ano'] + df['mes']
df['taxa_de_letalidade'] = df['obitosAcumulado'] / df['casosAcumulado']
df['taxa_de_letalidade'] = df['taxa_de_letalidade'].fillna(0)
data_referencia = df.data.iloc[-1].strftime("%d/%m/%Y")

# Printa total de casos, de óbitos, de óbitos nas últimas 24hrs e taxa de letalidade em percentual
print(f'Data de referência: {data_referencia}')
print(f'Total de casos: {df.casosNovos.sum()}')
print(f'Total de óbitos: {df.obitosNovos.sum()}')
print(f"Total de óbitos nas últimas 24hrs: {df[df['data'] == df['data'].max()].casosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df.obitosNovos.sum() / df.casosNovos.sum() * 100, 2)}%")

# Cria as colunas com as médias móveis de casos, óbitos e letalidade
dias_media_movel = 7
df['media_movel_casos'] = df.groupby('codmun')['casosNovos'].transform(lambda x: x.rolling(dias_media_movel, 1).mean())
df['media_movel_obitos'] = df.groupby('codmun')['obitosNovos'].transform(
    lambda x: x.rolling(dias_media_movel, 1).mean())
df['media_movel_letalidade'] = df.groupby('codmun')['taxa_de_letalidade'].transform(
    lambda x: x.rolling(dias_media_movel, 1).mean())

df_casos_obitos = df.groupby(['estado'], as_index=False).agg({'casosNovos': 'sum', 'obitosNovos': 'sum'})

df_diario = df.groupby(['data'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'casosAcumulado', 'obitosAcumulado',
     'media_movel_casos', 'media_movel_obitos']].sum()
populacao_brasil = df.drop_duplicates(subset=['estado', 'municipio']).populacaoTCU2019.sum()

# Define UF para plotar os gráficos diários de casos, óbitos e letalidade
uf = 'SP'
df_uf = df[df['estado'] == uf]
populacao_uf = df_uf.drop_duplicates(subset=['municipio']).populacaoTCU2019.sum()

df_uf_diario = df_uf.groupby(['data'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'casosAcumulado', 'obitosAcumulado',
     'media_movel_casos', 'media_movel_obitos']].sum()
df_uf_diario['taxa_de_letalidade'] = df_uf_diario['obitosAcumulado'] / df_uf_diario['casosAcumulado']
df_uf_diario['taxa_de_letalidade'] = df_uf_diario['taxa_de_letalidade'].fillna(0)
df_uf_diario['media_movel_letalidade'] = df_uf_diario['taxa_de_letalidade'].transform(
    lambda x: x.rolling(dias_media_movel, 1).mean())

print(f'Data de referência: {data_referencia}')
print(f'Total de casos: {df_uf.casosNovos.sum()}')
print(f'Total de óbitos: {df_uf.obitosNovos.sum()}')
print(f"Total de casos nas últimas 24hrs: {df_uf[df_uf['data'] == df_uf['data'].max()].casosNovos.sum()}")
print(f"Total de óbitos nas últimas 24hrs: {df_uf[df_uf['data'] == df_uf['data'].max()].obitosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df_uf.obitosNovos.sum() / df_uf.casosNovos.sum() * 100, 2)}%")

print(
    f'Média de casos nos últimos {dias_media_movel} dias por 100 mil habitantes - {uf}: '
    f'{round(df_uf_diario.media_movel_casos.iloc[-1] / (populacao_uf / 100000), 2)}')
print(
    f'Média de óbitos nos últimos {dias_media_movel} dias por 100 mil habitantes - {uf}: '
    f'{round(df_uf_diario.media_movel_obitos.iloc[-1] / (populacao_uf / 100000), 2)}')

print(
    f'Média de casos nos últimos {dias_media_movel} dias por 100 mil habitantes no Brasil: '
    f'{round(df_diario.media_movel_casos.iloc[-1] / (populacao_brasil / 100000), 2)}')
print(
    f'Média de óbitos nos últimos {dias_media_movel} dias por 100 mil habitantes no Brasil: '
    f'{round(df_diario.media_movel_obitos.iloc[-1] / (populacao_brasil / 100000), 2)}')

plotar_serie_temporal(f'Número de casos de covid confirmados - {uf}', 'Número de casos', 'casosNovos',
                      'Casos', df_uf_diario, 'media_movel_casos')
plotar_serie_temporal(f'Número de óbitos de covid - {uf}', 'Número de óbitos', 'obitosNovos', 'Óbitos', df_uf_diario,
                      'media_movel_obitos')
plotar_serie_temporal(f'Taxa de letalidade por covid - {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'Taxa de letalidade', df_uf_diario, 'media_movel_letalidade')

# Análise acumulada por UF de casos e óbitos

plotar_serie_temporal(f'Número de casos acumulados de covid - {uf}', 'Número de casos acumulados', 'casosAcumulado',
                      'Casos', df_uf_diario, media_movel=False)
plotar_serie_temporal(f'Número de óbitos acumulados de covid - {uf}', 'Número de óbitos acumulados',
                      'obitosAcumulado', 'Óbitos', df_uf_diario, media_movel=False)

# Análise semanal por UF de casos, óbitos e letalidade
df_uf_semanal = df_uf.groupby(['semana_ano'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'media_movel_casos', 'media_movel_obitos']].sum()

df_uf_semanal['casosAcumulado'] = df_uf_semanal['casosNovos'].cumsum(axis=0)
df_uf_semanal['obitosAcumulado'] = df_uf_semanal['obitosNovos'].cumsum(axis=0)

df_uf_semanal['taxa_de_letalidade'] = df_uf_semanal['obitosAcumulado'] / df_uf_semanal['casosAcumulado']
df_uf_semanal['taxa_de_letalidade'] = df_uf_semanal['taxa_de_letalidade'].fillna(0)
df_uf_semanal['media_movel_letalidade'] = df_uf_semanal['taxa_de_letalidade'].transform(
    lambda x: x.rolling(2, 1).mean())

df_uf_semanal['index'] = range(1, len(df_uf_semanal) + 1)

plotar_grafico_barras(f'Número de casos de covid confirmados - {uf} por semana', 'Semana da pandemia',
                      'Número de casos', 'index', 'casosNovos', df_uf_semanal, 'media_movel_casos')

plotar_grafico_barras(f'Número de óbitos por covid - {uf} por semana', 'Semana da pandemia',
                      'Número de óbitos', 'index', 'obitosNovos', df_uf_semanal, 'media_movel_obitos')

plotar_grafico_barras(f'Taxa de letalidade por covid - {uf} por semana', 'Semana da pandemia',
                      'Taxa de letalidade', 'index', 'taxa_de_letalidade', df_uf_semanal, 'media_movel_letalidade')

# Análise mensal por UF de casos, óbitos e letalidade

df_uf_mensal = df_uf.groupby(['mes_ano'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'media_movel_casos', 'media_movel_obitos']].sum()

df_uf_mensal['casosAcumulado'] = df_uf_mensal['casosNovos'].cumsum(axis=0)
df_uf_mensal['obitosAcumulado'] = df_uf_mensal['obitosNovos'].cumsum(axis=0)

df_uf_mensal['taxa_de_letalidade'] = df_uf_mensal['obitosAcumulado'] / df_uf_mensal['casosAcumulado']
df_uf_mensal['taxa_de_letalidade'] = df_uf_mensal['taxa_de_letalidade'].fillna(0)

df_uf_mensal['index'] = range(1, len(df_uf_mensal) + 1)

plotar_grafico_barras(f'Número de casos de covid confirmados - {uf} por mês', 'Mês da pandemia',
                      'Número de casos', 'index', 'casosNovos', df_uf_mensal, media_movel=False)

plotar_grafico_barras(f'Número de óbitos por covid - {uf} por mês', 'Mês da pandemia',
                      'Número de óbitos', 'index', 'obitosNovos', df_uf_mensal, media_movel=False)

plotar_grafico_barras(f'Taxa de letalidade por covid - {uf} por mês', 'Mês da pandemia',
                      'Taxa de letalidade', 'index', 'taxa_de_letalidade', df_uf_mensal, media_movel=False)

# Define municipio para plotar os gráficos diários de casos, óbitos e letalidade
municipio = 'São Carlos'
df_mun = df_uf[df_uf['municipio'] == municipio]

print(f'Data de referência: {data_referencia}')
print(f'Total de casos: {df_mun.casosNovos.sum()}')
print(f'Total de óbitos: {df_mun.obitosNovos.sum()}')
print(f"Total de óbitos nas últimas 24hrs: {df_mun[df_mun['data'] == df_mun['data'].max()].casosNovos.sum()}")
print(f"Taxa de letalidade em percentual: {round(df_mun.obitosNovos.sum() / df_mun.casosNovos.sum() * 100, 2)}%")

print(
    f'Média de casos nos últimos {dias_media_movel} dias por 100 mil habitantes em {municipio} - {uf}: '
    f'{round(df_mun.media_movel_casos.iloc[-1] / (df_mun.populacaoTCU2019.unique()[0] / 100000), 2)}')
print(
    f'Média de óbitos nos últimos {dias_media_movel} dias por 100 mil habitantes em {municipio} - {uf}: '
    f'{round(df_mun.media_movel_obitos.iloc[-1] / (df_mun.populacaoTCU2019.unique()[0] / 100000), 2)}')

print(
    f'Média de casos nos últimos {dias_media_movel} dias por 100 mil habitantes - {uf}: '
    f'{round(df_uf_diario.media_movel_casos.iloc[-1] / (populacao_uf / 100000), 2)}')
print(
    f'Média de óbitos nos últimos {dias_media_movel} dias por 100 mil habitantes - {uf}: '
    f'{round(df_uf_diario.media_movel_obitos.iloc[-1] / (populacao_uf / 100000), 2)}')

print(
    f'Média de casos nos últimos {dias_media_movel} dias por 100 mil habitantes no Brasil: '
    f'{round(df_diario.media_movel_casos.iloc[-1] / (populacao_brasil / 100000), 2)}')
print(
    f'Média de óbitos nos últimos {dias_media_movel} dias por 100 mil habitantes no Brasil: '
    f'{round(df_diario.media_movel_obitos.iloc[-1] / (populacao_brasil / 100000), 2)}')

plotar_serie_temporal(f'Número de casos de covid confirmados em {municipio} - {uf}', 'Número de casos', 'casosNovos',
                      'media_movel_casos', df_mun)
plotar_serie_temporal(f'Número de óbitos de covid em {municipio} - {uf}', 'Número de óbitos', 'obitosNovos',
                      'media_movel_obitos', df_mun)
plotar_serie_temporal(f'Taxa de letalidade por covid em {municipio} - {uf}', 'Taxa de letalidade', 'taxa_de_letalidade',
                      'media_movel_letalidade', df_mun)

# Análise acumulada por município de casos e óbitos

plotar_serie_temporal(f'Número de casos acumulados de covid em {municipio} - {uf}', 'Número de casos acumulados',
                      'casosAcumulado',
                      'Casos', df_mun, media_movel=False)
plotar_serie_temporal(f'Número de óbitos acumulados de covid em {municipio} - {uf}', 'Número de óbitos acumulados',
                      'obitosAcumulado', 'Óbitos', df_mun, media_movel=False)

# Análise semanal de município para casos, óbitos e letalidade
df_mun_semanal = df_mun.groupby(['semana_ano'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'media_movel_casos', 'media_movel_obitos']].sum()

df_mun_semanal['casosAcumulado'] = df_mun_semanal['casosNovos'].cumsum(axis=0)
df_mun_semanal['obitosAcumulado'] = df_mun_semanal['obitosNovos'].cumsum(axis=0)

df_mun_semanal['taxa_de_letalidade'] = df_mun_semanal['obitosAcumulado'] / df_mun_semanal['casosAcumulado']
df_mun_semanal['taxa_de_letalidade'] = df_mun_semanal['taxa_de_letalidade'].fillna(0)
df_mun_semanal['media_movel_letalidade'] = df_mun_semanal['taxa_de_letalidade'].transform(
    lambda x: x.rolling(2, 1).mean())

df_mun_semanal['index'] = range(1, len(df_mun_semanal) + 1)

plotar_grafico_barras(f'Número de casos de covid confirmados em {municipio} - {uf} por semana', 'Semana da pandemia',
                      'Número de casos', 'index', 'casosNovos', df_mun_semanal, 'media_movel_casos')

plotar_grafico_barras(f'Número de óbitos por covid em {municipio} - {uf} por semana', 'Semana da pandemia',
                      'Número de óbitos', 'index', 'obitosNovos', df_mun_semanal, 'media_movel_obitos')

plotar_grafico_barras(f'Taxa de letalidade por covid em {municipio} - {uf} por semana', 'Semana da pandemia',
                      'Taxa de letalidade', 'index', 'taxa_de_letalidade', df_mun_semanal, 'media_movel_letalidade')

# Análise mensal de município para casos, óbitos e letalidade

df_mun_mensal = df_mun.groupby(['mes_ano'], as_index=False)[
    ['casosNovos', 'obitosNovos', 'media_movel_casos', 'media_movel_obitos']].sum()

df_mun_mensal['casosAcumulado'] = df_mun_mensal['casosNovos'].cumsum(axis=0)
df_mun_mensal['obitosAcumulado'] = df_mun_mensal['obitosNovos'].cumsum(axis=0)

df_mun_mensal['taxa_de_letalidade'] = df_mun_mensal['obitosAcumulado'] / df_mun_mensal['casosAcumulado']
df_mun_mensal['taxa_de_letalidade'] = df_mun_mensal['taxa_de_letalidade'].fillna(0)

df_mun_mensal['index'] = range(1, len(df_mun_mensal) + 1)

plotar_grafico_barras(f'Número de casos de covid confirmados em em {municipio} - {uf} por mês', 'Mês da pandemia',
                      'Número de casos', 'index', 'casosNovos', df_mun_mensal, media_movel=False)

plotar_grafico_barras(f'Número de óbitos por covid em em {municipio} - {uf} por mês', 'Mês da pandemia',
                      'Número de óbitos', 'index', 'obitosNovos', df_mun_mensal, media_movel=False)

plotar_grafico_barras(f'Taxa de letalidade por covid em em {municipio} - {uf} por mês', 'Mês da pandemia',
                      'Taxa de letalidade', 'index', 'taxa_de_letalidade', df_mun_mensal, media_movel=False)

# import pandas as pd
# import folium
#
# df_map = pd.read_csv("uteis/olist_geolocation_dataset.csv")
# df_map = df_map.drop_duplicates(subset=['geolocation_state'])
# df_map = df_map.rename(columns={'geolocation_state': 'estado'})
# df_map = df_map.merge(df_casos_obitos, how='left', on='estado')
#
# coordenadas = []
# for index, row in df_map.iterrows():
#     lat = row.geolocation_lat
#     lng = row.geolocation_lng
#     casos = row.casosNovos
#     for idx in range(0, casos):
#         coordenadas.extend([lat, lng])
#
# mapa = folium.Map(location=[-15.788497, -47.879873], zoom_start=5, tiles='Stamen Toner')
# mapa.add_child(folium.plugins.HeatMap(coordenadas))
# mapa.save('mapa_casos.html')
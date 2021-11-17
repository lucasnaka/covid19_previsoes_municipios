#!/usr/bin/env python
# coding: utf-8

import streamlit as st
from PIL import Image

import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import pandas as pd
import numpy as np
import datetime as dt
from urllib.request import urlopen
import json

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="Previsão Covid-19 ICMC/USP", page_icon="🖖"
)

matplotlib.use("Agg")

st.title("Previsão de Obitos COVID-19 - ICMC/MECAI - USP")

st.sidebar.title('Menu')
pages = ('Início', 'Modelos preditivos', 'Modelos descritivos', 'Sobre')
selected_page = st.sidebar.radio('Paginas', pages)


# suppress_st_warning=True para usar depois e "desaparecer" as mensagens de carregamento

@st.cache(allow_output_mutation=True)
def load_data():
    df_city_deaths = pd.read_parquet('../data/app/covid_saude_obito_municipio.parquet')
    df_region_deaths = pd.read_parquet('../data/app/covid_saude_obito_regiao.parquet')
    df_city_states = pd.read_parquet('../data/app/est_cidade.parquet')
    df_vaccine = pd.read_parquet('../data/app/opendatasus_vacinacao.parquet')
    df_regional_clusters = pd.read_parquet('../data/app/clusters.parquet')
    json_file = open('../data/app/cities_shape.json')

    df_city_deaths['data'] = pd.to_datetime(df_city_deaths['data'])
    df_region_deaths['data'] = pd.to_datetime(df_region_deaths['data'])
    df_vaccine['data'] = pd.to_datetime(df_vaccine['data'])
    list_states = list(df_city_states['estado'].drop_duplicates().sort_values())
    json_cities_shape = json.load(json_file)
    return df_city_deaths, df_region_deaths, list_states, df_city_states, df_vaccine, df_regional_clusters, \
           json_cities_shape


df_casos, df_casos_reg, states, df_city_states, df_vacina, df_clusters, cities_shape = load_data()


@st.cache(allow_output_mutation=True)
def load_metadata(url):
    with urlopen(url) as response:
        json_brazil_shape = json.load(response)
    dict_state_id_map = {}

    for feature_loop in json_brazil_shape["features"]:
        feature_loop["id"] = feature_loop["properties"]["name"]
        dict_state_id_map[feature_loop["properties"]["sigla"]] = feature_loop["id"]  # definindo a informação do gráfico
    return json_brazil_shape, feature_loop, dict_state_id_map


Brasil, feature, state_id_map = load_metadata(
    'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson')


def SetNewsSize(x):
    if not pd.isnull(x):
        return 7.5
    else:
        return 0


def find_cities(selected_states):
    return list(df_city_states[df_city_states['estado'] == selected_states]['municipio'].sort_values())


def filter_state_city():
    choose_state = st.sidebar.checkbox('Filtrar por estado')
    choose_city = None
    selected_state = None
    selected_city = 'São Paulo'

    if choose_state:
        selected_state = st.sidebar.selectbox('Estado', states)
        choose_city = st.sidebar.checkbox('Filtrar por cidade')
    if choose_city:
        selected_city = st.sidebar.selectbox('Cidade', find_cities(selected_state))

    return selected_state, selected_city


def filter_date(df):
    choose_date = st.sidebar.checkbox('Filtrar por data')
    min_date = df['data'].min()
    max_date = df['data'].max()
    date_range = (
        dt.date(min_date.year, min_date.month, min_date.day), dt.date(max_date.year, max_date.month, max_date.day))
    selected_date = None

    if choose_date:
        selected_date = st.sidebar.slider('Data', value=date_range, format="DD/MM/YYYY")

    return selected_date


def common_filters_pred(df_casos, df_casos_reg, df_clusters, cities_shape):
    selected_filters = dict()
    selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
    selected_state, selected_city = filter_state_city()

    selected_filters['state'] = selected_state
    selected_filters['city'] = selected_city
    selected_filters['cod_city_2'] = df_casos.loc[df_casos['municipio'] == selected_city, 'codmun'].iloc[0]
    selected_filters['cluster'] = df_clusters.loc[df_clusters['codigo_ibge_2'] == selected_filters['cod_city_2'],
                                                  'cluster'].iloc[0]

    if selected_filters['city']:
        df_filtered = df_casos.loc[(df_casos['codmun'] == selected_filters['cod_city_2'])]
    else:
        df_filtered = df_casos.loc[(df_casos['municipio'] == 'São Paulo')]

    selected_date_range = filter_date(df_filtered)

    selected_filters['database'] = selected_data
    selected_filters['date'] = selected_date_range

    if selected_filters['date']:
        df_filtered = df_filtered.loc[(df_filtered['data'].dt.date >= selected_filters['date'][0])
                                      & (df_filtered['data'].dt.date <= selected_filters['date'][1])]
        df_casos_reg = df_casos_reg.loc[(df_casos_reg['data'].dt.date >= selected_filters['date'][0])
                                        & (df_casos_reg['data'].dt.date <= selected_filters['date'][1])]

    cities_filtered_list = [x for x in cities_shape['features'] if
                            x['properties']['cluster'] == selected_filters['cluster']]
    cities_shape_filtered = {'type': 'FeatureCollection', 'features': cities_filtered_list}

    return selected_filters, df_filtered, df_casos_reg, cities_shape_filtered


def common_filters_desc(df_casos, df_casos_reg, df_clusters, df_vacina, cities_shape):
    selected_filters = dict()
    selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
    selected_state, selected_city = filter_state_city()

    selected_filters['state'] = selected_state
    selected_filters['city'] = selected_city
    selected_filters['cod_city_2'] = df_casos.loc[df_casos['municipio'] == selected_city, 'codmun'].iloc[0]
    selected_filters['cluster'] = df_clusters.loc[df_clusters['codigo_ibge_2'] == selected_filters['cod_city_2'],
                                                  'cluster'].iloc[0]

    if selected_filters['city']:
        df_filtered = df_casos.loc[(df_casos['codmun'] == selected_filters['cod_city_2'])]
    else:
        df_filtered = df_casos.loc[(df_casos['municipio'] == 'São Paulo')]

    selected_date_range = filter_date(df_filtered)

    selected_filters['database'] = selected_data
    selected_filters['date'] = selected_date_range

    if selected_filters['date']:
        df_filtered = df_filtered.loc[(df_filtered['data'].dt.date >= selected_filters['date'][0])
                                      & (df_filtered['data'].dt.date <= selected_filters['date'][1])]
        df_casos_reg = df_casos_reg.loc[(df_casos_reg['data'].dt.date >= selected_filters['date'][0])
                                        & (df_casos_reg['data'].dt.date <= selected_filters['date'][1])]
        df_vacina = df_vacina.loc[(df_vacina['data'].dt.date >= selected_filters['date'][0])
                                  & (df_vacina['data'].dt.date <= selected_filters['date'][1])]

    cities_filtered_list = [x for x in cities_shape['features'] if
                            x['properties']['cluster'] == selected_filters['cluster']]
    cities_shape_filtered = {'type': 'FeatureCollection', 'features': cities_filtered_list}

    return selected_filters, df_filtered, df_casos_reg, cities_shape_filtered, df_vacina


def home():
    st.title('Início')


def predictive_models():
    st.title('Modelos preditivos')

    selected_filters, df_filtered, df_filtered_reg, cities_shape_filtered = common_filters_pred(df_casos, df_casos_reg,
                                                                                                df_clusters,
                                                                                                cities_shape)

    with st.beta_container():
        col1, col2 = st.beta_columns([20, 10])

        with col1:
            html_card_header2 = """
            <div class="card">
            <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #eef9ea; padding-top: 5px; width: 100%; height: 100%;">
                <h3 class="card-title" style="background-color:#eef9ea; color:#008080; font-family:Georgia; text-align: center; padding: 0px 0;">Média Obitos BR:</h3>
            </div>
            </div>
            """
            st.markdown(html_card_header2, unsafe_allow_html=True)
            mean_ob = np.mean(df_filtered["obitosNovos"])
            figin = go.Figure().add_trace(go.Indicator(
                mode="number",
                value=mean_ob,
                domain={'row': 1, 'column': 0}))

            st.plotly_chart(figin.update_layout(autosize=False,
                                                width=150, height=90, margin=dict(l=20, r=20, b=20, t=30),
                                                paper_bgcolor="#fbfff0", font={'size': 20}), use_container_width=True)
            fig = px.choropleth_mapbox(
                df_clusters,  # banco de dados da soja
                locations="codarea",  # definindo os limites no mapa
                featureidkey="properties.codarea",
                geojson=cities_shape_filtered,  # definindo as delimitações geográficas
                #     color="cluster", # definindo a cor através da base de dados
                hover_name="Município",  # pontos que você quer mostrar na caixinha de informação
                hover_data=['Município', 'cluster'],
                title='Indice de Letalitade por Região',
                mapbox_style="carto-positron",  # Definindo novo estilo de mapa, o de satélite
                zoom=3,  # o tamanho do gráfico
                opacity=0.5,  # opacidade da cor do map
                center={"lat": -14, "lon": -55},
                width=1000, height=900, )
            fig.update_layout(title="Cidades similares",
                              title_font_color="black",
                              font=dict(
                                  family="arial",
                                  size=14),
                              template="plotly_white", plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(b=0))
            st.plotly_chart(fig, use_container_width=True)


def descriptive_models():
    st.header('Modelos descritivos')

    with st.beta_container():
        col1, col2 = st.beta_columns([20, 10])

        selected_filters, df_filtered, df_filtered_reg, df_filtered_vacina, cities_shape_filtered = common_filters_desc(
            df_casos, df_casos_reg, df_clusters, df_vacina, cities_shape)
        # if selected_filters:
        #     st.info(f"{selected_filters}")

        #     st.title('Número de óbitos por dia')
        with col1:
            html_card_header1 = """
            <div class="card">
            <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #eef9ea; padding-top: 5px; width: 100%; height: 100%;">
                <h3 class="card-title" style="background-color:#eef9ea; color:#008080; font-family:Georgia; text-align: center; padding: 0px 0;">Média Obitos BR:</h3>
            </div>
            </div>
            """
            st.markdown(html_card_header1, unsafe_allow_html=True)
            mean_ob = np.mean(df_filtered["obitosNovos"])
            figin = go.Figure().add_trace(go.Indicator(
                mode="number",
                value=mean_ob,
                domain={'row': 1, 'column': 0}))

            st.plotly_chart(figin.update_layout(autosize=False,
                                                width=150, height=90, margin=dict(l=20, r=20, b=20, t=30),
                                                paper_bgcolor="#fbfff0", font={'size': 20}), use_container_width=True)

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=df_filtered["data"],
                                     y=df_filtered["obitosNovos"],
                                     text=df_filtered['texto'],
                                     hoverinfo='text',
                                     mode='lines+markers',
                                     marker=dict(size=list(map(SetNewsSize, df_filtered['texto'])),
                                                 color=['orange'] * df_filtered.shape[0]),
                                     )
                          )

            fig.update_layout(title="Óbitos diários",
                              title_font_color="black",
                              yaxis_title="Número de óbitos",
                              font=dict(
                                  family="arial",
                                  size=14),
                              template="plotly_white", plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=20, r=20, b=20, t=30), width=1050, height=590)

            st.plotly_chart(fig, use_container_width=True)

            fig = go.Figure()
            fig = px.bar(df_filtered_reg,
                         x=df_filtered_reg['data'],
                         y=df_filtered_reg['percentage_deaths'],
                         color='regiao',
                         labels={
                             "regiao": "Região",
                         }, )
            # text=df_filtered_reg['percentage_deaths'].apply(lambda x: '{0:1.2f}%'.format(x)))
            fig.update_layout(yaxis_title="% Óbitos semanais por região",
                              font=dict(
                                  family="arial",
                                  size=14),
                              template="plotly_white", plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=20, r=20, b=20, t=30), width=1050, height=550)

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            html_card_header2 = """
            <div class="card">
            <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #eef9ea; padding-top: 5px; width: 100%; height: 100%;">
                <h3 class="card-title" style="background-color:#eef9ea; color:#008080; font-family:Georgia; text-align: center; padding: 0px 0;">Média Obitos BR:</h3>
            </div>
            </div>
            """
            st.markdown(html_card_header2, unsafe_allow_html=True)
            mean_ob = np.mean(df_filtered["obitosNovos"])
            figin = go.Figure().add_trace(go.Indicator(
                mode="number",
                value=mean_ob,
                domain={'row': 1, 'column': 0}))

            st.plotly_chart(figin.update_layout(autosize=False,
                                                width=150, height=90, margin=dict(l=20, r=20, b=20, t=30),
                                                paper_bgcolor="#fbfff0", font={'size': 20}), use_container_width=True)
            fig2 = px.choropleth_mapbox(
                df_vacina,  # banco de dados da soja
                locations="Estado",  # definindo os limites no mapa
                geojson=Brasil,  # definindo as delimitações geográficas
                color="ind",  # definindo a cor através da base de dados
                hover_name="Estado",  # pontos que você quer mostrar na caixinha de informação
                hover_data=['Estado', 'ind', 'Latitude', 'Longitude'],
                mapbox_style="carto-positron",  # Definindo novo estilo de mapa, o de satélite
                zoom=2.5,  # o tamanho do gráfico
                opacity=0.5,  # opacidade da cor do map
                center={"lat": -14, "lon": -55}, width=900, height=1100, )
            fig2.update_layout(title="Indice de Vacinação",
                               title_font_color="black",
                               font=dict(
                                   family="arial",
                                   size=14),
                               template="plotly_white", plot_bgcolor='rgba(0,0,0,0)',
                               margin=dict(b=0))
            st.plotly_chart(fig2, use_container_width=True)


def about():
    st.title('Sobre')

    st.markdown("""

    ### O Projeto
    Plataforma Web para disponibilizar publicamente a previsão de casos 
    de óbito e vacinação relacionados à Covid-19 em nível municipal.

    ### A Gerência
    | Membro | Função |
    | ------ | ------ |
    | Francisco Louzada Neto | CEO |
    | Loriz Sallum | Diretora |
    | Oilson Gonzatto | Diretor |

    ### Os membros da equipe
    | Aluno | Função |
    | ------ | ------ |
    | Bernardo | Estatístico |
    | Bruno Braziel | Programador |
    | Francisco Pigato | Coordenador |
    | Lucas Nakadaira | Programador |
    | Mariana Spanol | Estatística |
    

    #### PROBABILIDADE E ESTATÍSTICA 
    #### MECAI - 2021
    """)


if selected_page == 'Início':
    home()
elif selected_page == 'Modelos preditivos':
    predictive_models()
elif selected_page == 'Modelos descritivos':
    descriptive_models()
elif selected_page == 'Sobre':
    about()

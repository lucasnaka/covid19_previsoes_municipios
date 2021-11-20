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




# specify the primary menu definition

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
    df_weekly_deaths = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/covid_saude_obito_grouped.parquet')
    df_depara_levels = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/depara_levels.parquet')
    df_vaccine = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/opendatasus_vacinacao.parquet')
    df_regional_clusters = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/clusters.parquet')
    json_file = open('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/cities_shape.json')

    df_vaccine['data'] = pd.to_datetime(df_vaccine['data'])
    list_regions = list(df_depara_levels['regiao'].drop_duplicates().sort_values())
    list_states = list(df_depara_levels['estado'].drop_duplicates().sort_values())
    json_cities_shape = json.load(json_file)
    return list_regions, list_states, df_depara_levels, df_vaccine, df_regional_clusters, \
           json_cities_shape, df_weekly_deaths


list_regions, list_states, df_depara_levels, df_vacina, df_clusters, cities_shape, df_weekly_deaths = load_data()


@st.cache(allow_output_mutation=True)
def load_metadata(url):
    with urlopen(url) as response:
        json_brazil_shape = json.load(response)
    dict_state_id_map = {}

    for feature_loop in json_brazil_shape["features"]:
        feature_loop["id"] = feature_loop["properties"]["name"]
        dict_state_id_map[feature_loop["properties"]["sigla"]] = feature_loop["id"]  # definindo a informação do gráfico
    return json_brazil_shape, dict_state_id_map


# Brasil, state_id_map = load_metadata(
#     'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson')


def SetNewsSize(x):
    if not pd.isnull(x):
        return 7.5
    else:
        return 0


def find_level_divisions(level, selected_division):
    if level == 'region':
        return list(
            df_depara_levels[df_depara_levels['regiao'] == selected_division]['estado'].drop_duplicates().sort_values())
    elif level == 'state':
        return list(df_depara_levels[df_depara_levels['estado'] == selected_division][
                        'nomeRegiaoSaude'].drop_duplicates().sort_values())
    return list(df_depara_levels[df_depara_levels['nomeRegiaoSaude'] == selected_division][
                    'municipio'].drop_duplicates().sort_values())


def filter_aggregation_level():
    choose_region = st.sidebar.checkbox('Filtrar por região', key="1")
    choose_state = None
    choose_rs = None
    choose_city = None
    selected_reg = None
    selected_state = None
    selected_regsaude = None
    selected_city = None

    if choose_region:
        selected_reg = st.sidebar.selectbox('Região', list_regions, key="2")
        choose_state = st.sidebar.checkbox('Filtrar por estado', key="3")
    if choose_state:
        selected_state = st.sidebar.selectbox('Estado', find_level_divisions('region', selected_reg), key="4")
        choose_rs = st.sidebar.checkbox('Filtrar por regional de saúde', key="5")
    if choose_rs:
        selected_regsaude = st.sidebar.selectbox('Regional de saúde', find_level_divisions('state', selected_state),
                                                 key="6")
        choose_city = st.sidebar.checkbox('Filtrar por cidade', key="7")
    if choose_city:
        selected_city = st.sidebar.selectbox('Cidade', find_level_divisions('regsaude', selected_regsaude), key="8")

    return selected_reg, selected_state, selected_regsaude, selected_city


def filter_state_city():
    selected_state = st.sidebar.selectbox('Estado', list_states, key="selectbox_state")
    list_cities = list(df_depara_levels[df_depara_levels['estado'] == selected_state][
                           'municipio'].drop_duplicates().sort_values())
    selected_city = st.sidebar.selectbox('Cidade', list_cities, key="selectbox_city")

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


def common_filters_pred(df_clusters, cities_shape, df_weekly_cases):
    selected_filters = dict()
    selected_state, selected_city = filter_state_city()

    selected_filters['cod_city_2'] = df_weekly_cases.loc[df_weekly_cases['municipio'] == selected_city, 'codmun'].iloc[
        0]
    selected_filters['cluster'] = \
    df_clusters.loc[df_clusters['codigo_ibge_2'] == selected_filters['cod_city_2'], 'cluster'].iloc[0]

    cities_filtered_list = [x for x in cities_shape['features'] if
                            x['properties']['cluster'] == selected_filters['cluster']]
    cities_shape_filtered = {'type': 'FeatureCollection', 'features': cities_filtered_list}

    return selected_filters, cities_shape_filtered


def common_filters_desc(df_vacina, df_weekly_cases):
    selected_filters = dict()
    selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
    selected_reg, selected_state, selected_regsaude, selected_city = filter_aggregation_level()

    if selected_reg:
        if selected_state:
            if selected_regsaude:
                if selected_city:
                    df_weekly_cases_level_up_up = df_weekly_cases.loc[df_weekly_cases['nomeRegiaoSaude'] == selected_regsaude]
                    df_weekly_cases_level_up = df_weekly_cases.loc[(df_weekly_cases['municipio'] == selected_city)]
                    df_weekly_cases_level_down = df_weekly_cases_level_up.copy()
                    level = 'municipio'
                else:
                    df_weekly_cases_level_up_up = df_weekly_cases.loc[df_weekly_cases['estado'] == selected_state]
                    df_weekly_cases_level_up = df_weekly_cases.loc[df_weekly_cases['nomeRegiaoSaude'] == selected_regsaude]
                    df_weekly_cases_level_down = df_weekly_cases.loc[(df_weekly_cases['municipio'].notna())]
                    level = 'municipio'
            else:
                df_weekly_cases_level_up_up = df_weekly_cases.loc[df_weekly_cases['regiao'] == selected_reg]
                df_weekly_cases_level_up = df_weekly_cases.loc[(df_weekly_cases['estado'] == selected_state)]
                df_weekly_cases_level_down = df_weekly_cases.loc[(df_weekly_cases['nomeRegiaoSaude'].notna())]
                level = 'nomeRegiaoSaude'
        else:
            df_weekly_cases_level_up_up = df_weekly_cases.loc[
                (df_weekly_cases['regiao'].isna()) & (df_weekly_cases['estado'].isna()) & (
                    df_weekly_cases['codmun'].isna()) & (df_weekly_cases['codRegiaoSaude'].isna())]
            df_weekly_cases_level_up = df_weekly_cases.loc[(df_weekly_cases['regiao'] == selected_reg)]
            df_weekly_cases_level_down = df_weekly_cases.loc[(df_weekly_cases['estado'].notna())]
            level = 'estado'
    else:
        df_weekly_cases_level_up_up = df_weekly_cases.loc[
            (df_weekly_cases['regiao'].isna()) & (df_weekly_cases['estado'].isna()) & (
                df_weekly_cases['codmun'].isna()) & (df_weekly_cases['codRegiaoSaude'].isna())]
        df_weekly_cases_level_up = df_weekly_cases.loc[
            (df_weekly_cases['regiao'].isna()) & (df_weekly_cases['estado'].isna()) & (
                df_weekly_cases['codmun'].isna()) & (df_weekly_cases['codRegiaoSaude'].isna())]
        df_weekly_cases_level_down = df_weekly_cases.loc[(df_weekly_cases['regiao'].notna())]
        level = 'regiao'

    selected_date_range = filter_date(df_weekly_cases_level_up)

    selected_filters['database'] = selected_data
    selected_filters['date'] = selected_date_range

    if selected_filters['date']:
        df_vacina = df_vacina.loc[(df_vacina['data'].dt.date >= selected_filters['date'][0])
                                  & (df_vacina['data'].dt.date <= selected_filters['date'][1])]
        df_weekly_cases_level_up_up = df_weekly_cases_level_up_up.loc[
            (df_weekly_cases_level_up_up['data'].dt.date >= selected_filters['date'][0])
            & (df_weekly_cases_level_up_up['data'].dt.date <= selected_filters['date'][1])]
        df_weekly_cases_level_up = df_weekly_cases_level_up.loc[
            (df_weekly_cases_level_up['data'].dt.date >= selected_filters['date'][0])
            & (df_weekly_cases_level_up['data'].dt.date <= selected_filters['date'][1])]
        df_weekly_cases_level_down = df_weekly_cases_level_down.loc[
            (df_weekly_cases_level_down['data'].dt.date >= selected_filters['date'][0])
            & (df_weekly_cases_level_down['data'].dt.date <= selected_filters['date'][1])]

    return selected_filters, level, df_vacina, df_weekly_cases_level_up_up, df_weekly_cases_level_up, df_weekly_cases_level_down


def home():
    st.title('Início')


def predictive_models():
    st.title('Modelos preditivos')

    selected_filters, cities_shape_filtered = common_filters_pred(df_clusters,
                                                                  cities_shape,
                                                                  df_weekly_deaths)

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
        selected_filters, level, df_filtered_vacina, df_weekly_cases_level_up_up, df_weekly_cases_level_up, df_weekly_cases_level_down = common_filters_desc(
            df_vacina, df_weekly_deaths)

        html_card_header1 = """
            <div class="card">
            <div class="card-body" style="border-radius: 10px 10px 0px 0px; background: #eef9ea; padding-top: 5px; width: 100%; height: 100%;">
                <h3 class="card-title" style="background-color:#eef9ea; color:#008080; font-family:Georgia; text-align: center; padding: 0px 0;">Óbitos semanais (última data selecionada):</h3>
            </div>
            </div>
            """
        st.markdown(html_card_header1, unsafe_allow_html=True)
        mean_ob = np.mean(df_weekly_cases_level_up.loc[df_weekly_cases_level_up['week_number'] ==
                                                           df_weekly_cases_level_up['week_number'].max(), "new_deaths_week_division"])
        figin = go.Figure().add_trace(go.Indicator(
                mode="number",
                value=mean_ob,
                domain={'row': 1, 'column': 0}))

        st.plotly_chart(figin.update_layout(autosize=False,
                                                width=150, height=90, margin=dict(l=10, r=10, b=20, t=30),
                                                paper_bgcolor="#fbfff0", font={'size': 20}), use_container_width=True)

            # fig = make_subplots(1, 1)
            #
            # fig.add_trace(
            #     go.Bar(
            #         x=df_weekly_cases_level_up_up['data'],
            #         y=df_weekly_cases_level_up_up['new_deaths_week_division'],
            #         customdata=df_weekly_cases_level_up_up['noticia'].to_numpy(),
            #         text=df_weekly_cases_level_up_up['data'],
            #         hoverinfo='text',
            #         hovertemplate='%{customdata}'
            #     )
            # )

            #fig = px.bar(df_weekly_cases_level_up_up,
             #            x=df_weekly_cases_level_up_up['data'],
              #           y=df_weekly_cases_level_up_up['new_deaths_week_division'],
               #          custom_data=[df_weekly_cases_level_up_up['noticia']],
                #         )

        fig = go.Figure()
        fig.add_trace(go.Histogram(
                                       x=df_weekly_cases_level_up['data'],
                                       y =df_weekly_cases_level_up['new_deaths_week_division'],histfunc="avg", nbinsx=50))
        fig.add_trace(go.Histogram(
                         x=df_weekly_cases_level_up_up['data'],
                         y=df_weekly_cases_level_up_up['new_deaths_week_division'], histfunc="avg", nbinsx=50))
            


            # Overlay both histograms
            # Reduce opacity to see both histograms
        fig.update_traces(opacity=0.55, hovertemplate=df_weekly_cases_level_up_up['noticia'], selector=dict(type="histogram"))

        fig.update_layout(yaxis_title="Óbitos semanais",
                              font=dict(
                                  family="arial",
                                  size=14),
                              template="plotly_white",
                              plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=20, r=20, b=20, t=30),
                              width=1650,
                              height=350, barmode='stack',
                              hoverlabel=dict(
                                  bgcolor="white",
                                  font_size=14,
                                  font_family="Rockwell"
                              ))

        st.plotly_chart(fig, use_container_width=False)
            
        fig2 = px.histogram(df_weekly_cases_level_down,
                                x=df_weekly_cases_level_down['data'],
                                y=df_weekly_cases_level_down['percentage_deaths'],
                                color=level,
                                # labels={
                                #     "regiao": "Região",
                                # },
                                barmode="stack",
                                histfunc="avg",
                                barnorm="percent",
                                nbins=50)
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
    about()
elif selected_page == 'Modelos preditivos':
    predictive_models()
elif selected_page == 'Modelos descritivos':
    descriptive_models()
elif selected_page == 'Sobre':
    about()

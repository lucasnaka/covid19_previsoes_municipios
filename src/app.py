#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import matplotlib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime as dt
from urllib.request import urlopen
import json
from ipywidgets import Output, VBox
from st_btn_select import st_btn_select
from itertools import cycle

# Local files
import utils

# specify the primary menu definition
# palette = cycle(px.colors.sequential.PuBu)
# palette = cycle(['#e1f5fe', '#01579b',
#                  '#0277bd', '#b3e5fc',
#                  '#0288d1', '#80d8ff',
#                  '#0091ea', '#81d4fa',
#                  '#039be5', '#4fc3f7',
#                  '#00b0ff', '#40c4ff',
#                  '#03a9f4', '#29b6f6',
#                  ])

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
    page_title="Previsão Covid-19 ICMC/USP", page_icon="🖖"
)

matplotlib.use("Agg")

st.sidebar.title('Menu')
# pages = ('Início', 'Modelos preditivos', 'Modelos descritivos', 'Sobre')
# selected_page = st.sidebar.radio('Paginas', pages)
page = st_btn_select(
    # The different pages
    ('Início', 'Modelos descritivos','Modelos preditivos', 'Sobre'),
    # Enable navbar
    nav=True,
    # You can pass a formatting function. Here we capitalize the options
    format_func=lambda name: name.capitalize(),
)


# suppress_st_warning=True para usar depois e "desaparecer" as mensagens de carregamento

@st.cache(allow_output_mutation=True)
def load_data():
    df_weekly_deaths = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/covid_saude_obito_grouped.parquet')
    df_depara_levels = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/depara_levels.parquet')
    df_vaccine = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/opendatasus_vacinacao.parquet')
    df_regional_clusters = pd.read_parquet('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/clusters.parquet')
    json_file = open('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/cities_shape.json')
    df_death_predictions = pd.read_csv('C:/Users/mscamargo/Desktop/estudos/my_proj/covid19_previsoes_municipios/data/app/death_predictions.csv')
    #df_weekly_deaths = pd.read_parquet('../data/app/covid_saude_obito_grouped.parquet')
    #df_depara_levels = pd.read_parquet('../data/app/depara_levels.parquet')
    #df_vaccine = pd.read_parquet('../data/app/opendatasus_vacinacao.parquet')
    #df_regional_clusters = pd.read_parquet('../data/app/clusters.parquet')
    #df_death_predictions = pd.read_parquet('../data/app/death_predictions.parquet')
    #json_file = open('../data/app/cities_shape.json')

    df_vaccine['data'] = pd.to_datetime(df_vaccine['data'])
    df_weekly_deaths['data'] = pd.to_datetime(df_weekly_deaths['data'])
    df_death_predictions['data'] = pd.to_datetime(df_death_predictions['data'])
    list_regions = list(df_depara_levels['regiao'].drop_duplicates().sort_values())
    list_states = list(df_depara_levels['estado'].drop_duplicates().sort_values())
    json_cities_shape = json.load(json_file)
    return list_regions, list_states, df_depara_levels, df_vaccine, df_regional_clusters, \
           json_cities_shape, df_weekly_deaths, df_death_predictions


list_regions, list_states, df_depara_levels, df_vacina, df_clusters, cities_shape, df_weekly_deaths, df_death_predictions = load_data()


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


def common_filters_desc(df_vacina, df_weekly_cases, df_death_predictions):
    selected_filters = dict()
    # selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
    selected_reg, selected_state, selected_regsaude, selected_city = filter_aggregation_level()

    if selected_reg:
        if selected_state:
            if selected_regsaude:
                if selected_city:
                    df_weekly_cases_level_up = df_weekly_cases.loc[
                        (df_weekly_cases['nomeRegiaoSaude'] == selected_regsaude) & (
                            df_weekly_cases['municipio'].isna())]
                    df_weekly_cases_level_selected = df_weekly_cases.loc[
                        (df_weekly_cases['municipio'] == selected_city)]
                    cities_at_this_level = df_depara_levels.loc[
                        df_depara_levels['nomeRegiaoSaude'] == selected_regsaude, 'municipio'].unique()
                    df_weekly_cases_level_down = df_weekly_cases.loc[
                        (df_weekly_cases['municipio'].isin(cities_at_this_level)) & (
                            df_weekly_cases['municipio'].notna())]
                    df_death_filtered = df_death_predictions.loc[df_death_predictions['municipio'] == selected_city]
                    level = 'municipio'
                else:
                    df_weekly_cases_level_up = df_weekly_cases.loc[
                        (df_weekly_cases['estado'] == selected_state) & (df_weekly_cases['nomeRegiaoSaude'].isna())]
                    df_weekly_cases_level_selected = df_weekly_cases.loc[
                        (df_weekly_cases['nomeRegiaoSaude'] == selected_regsaude) & (
                            df_weekly_cases['municipio'].isna())]
                    cities_at_this_level = df_depara_levels.loc[
                        df_depara_levels['nomeRegiaoSaude'] == selected_regsaude, 'municipio'].unique()
                    df_weekly_cases_level_down = df_weekly_cases.loc[
                        (df_weekly_cases['municipio'].isin(cities_at_this_level)) & (
                            df_weekly_cases['municipio'].notna())]
                    df_death_filtered = pd.DataFrame()
                    level = 'municipio'
            else:
                df_weekly_cases_level_up = df_weekly_cases.loc[
                    (df_weekly_cases['regiao'] == selected_reg) & (df_weekly_cases['estado'].isna())]
                df_weekly_cases_level_selected = df_weekly_cases.loc[
                    (df_weekly_cases['estado'] == selected_state) & (df_weekly_cases['nomeRegiaoSaude'].isna())]
                regsaude_at_this_level = df_depara_levels.loc[
                    df_depara_levels['estado'] == selected_state, 'nomeRegiaoSaude'].unique()
                df_weekly_cases_level_down = df_weekly_cases.loc[
                    (df_weekly_cases['nomeRegiaoSaude'].isin(regsaude_at_this_level)) & (
                        df_weekly_cases['nomeRegiaoSaude'].notna()) & (
                        df_weekly_cases['municipio'].isna())]
                df_death_filtered = pd.DataFrame()
                level = 'nomeRegiaoSaude'
        else:
            df_weekly_cases_level_up = df_weekly_cases.loc[
                (df_weekly_cases['regiao'].isna()) & (df_weekly_cases['estado'].isna()) & (
                    df_weekly_cases['codmun'].isna()) & (df_weekly_cases['codRegiaoSaude'].isna())]
            df_weekly_cases_level_selected = df_weekly_cases.loc[
                (df_weekly_cases['regiao'] == selected_reg) & (df_weekly_cases['estado'].isna())]
            states_at_this_level = df_depara_levels.loc[df_depara_levels['regiao'] == selected_reg, 'estado'].unique()
            df_weekly_cases_level_down = df_weekly_cases.loc[
                (df_weekly_cases['estado'].isin(states_at_this_level)) & (df_weekly_cases['estado'].notna()) & (
                    df_weekly_cases['codRegiaoSaude'].isna())]
            df_death_filtered = pd.DataFrame()
            level = 'estado'
    else:
        df_weekly_cases_level_up = df_weekly_cases.loc[
            (df_weekly_cases['regiao'].isna()) & (df_weekly_cases['estado'].isna()) & (
                df_weekly_cases['codmun'].isna()) & (df_weekly_cases['codRegiaoSaude'].isna())]
        df_weekly_cases_level_selected = pd.DataFrame()
        df_weekly_cases_level_down = df_weekly_cases.loc[
            (df_weekly_cases['regiao'].notna()) & (df_weekly_cases['estado'].isna())]
        df_death_filtered = pd.DataFrame()
        level = 'regiao'

    selected_date_range = filter_date(df_weekly_cases_level_up)

    # selected_filters['database'] = selected_data
    selected_filters['date'] = selected_date_range

    if selected_filters['date']:
        df_vacina = df_vacina.loc[(df_vacina['data'].dt.date >= selected_filters['date'][0])
                                  & (df_vacina['data'].dt.date <= selected_filters['date'][1])]
        df_weekly_cases_level_up = df_weekly_cases_level_up.loc[
            (df_weekly_cases_level_up['data'].dt.date >= selected_filters['date'][0])
            & (df_weekly_cases_level_up['data'].dt.date <= selected_filters['date'][1])]
        if not df_weekly_cases_level_selected.empty:
            df_weekly_cases_level_selected = df_weekly_cases_level_selected.loc[
                (df_weekly_cases_level_selected['data'].dt.date >= selected_filters['date'][0])
                & (df_weekly_cases_level_selected['data'].dt.date <= selected_filters['date'][1])]
        if not df_death_filtered.empty:
            df_death_filtered = df_death_filtered.loc[
                (df_death_filtered['data'].dt.date >= selected_filters['date'][0])
                & (df_death_filtered['data'].dt.date <= selected_filters['date'][1])]
        df_weekly_cases_level_down = df_weekly_cases_level_down.loc[
            (df_weekly_cases_level_down['data'].dt.date >= selected_filters['date'][0])
            & (df_weekly_cases_level_down['data'].dt.date <= selected_filters['date'][1])]

    return selected_filters, level, df_vacina, df_weekly_cases_level_up, df_weekly_cases_level_selected, df_weekly_cases_level_down, df_death_filtered


def home():
    st.title('Início')


def predictive_models():
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
    st.write(
        """
    <div class="base-wrapper primary-span">
        <span class="section-header">Acompanhamento de óbitos semanais</span>
    </div>
    <div class="base-wrapper">
        <span>
            A partir dos gráficos abaixo, podemos acompanhar a evolução da pandemia tanto na perspectiva temporal quanto
            geográfica. No primeiro gráfico, é possível acompanhar em números absolutos a quantidade de óbitos semanais 
            pela Covid-19. No segundo gráfico, é possível acompanhar como o número de óbitos em cada semana era distribuído
            no nível mais granular ao selecionado.
            <br>
            Ao passar o ponteiro do mouse pelas barras, algumas notícias sobre a Covid-19 aparecem, assim conseguimos acompanhar
            as medidas governamentais que foram tomadas ao longo da pandemia. 
        </span>
    </div>""",
        unsafe_allow_html=True,
    )
    with st.container():
        col1, col2 = st.columns(2)

        selected_filters, level, df_filtered_vacina, df_weekly_cases_level_up, df_weekly_cases_level_selected, \
        df_weekly_cases_level_down, df_predictions_filtered = common_filters_desc(df_vacina, df_weekly_deaths,
                                                                                  df_death_predictions)

        fig = make_subplots(rows=2, cols=1, specs=[[{}], [{}]],
                            shared_xaxes=True, shared_yaxes=False,
                            vertical_spacing=0.05)

        widths = np.array([1] * df_weekly_cases_level_up['week_number'].nunique())  # Vetor de tamanho das barras

        ################################################################################################################
        ###########################################     Gráfico de cima     ############################################
        ################################################################################################################
        # Plotar óbitos semanais para o nível selecionado
        if not df_weekly_cases_level_selected.empty:
            df_weekly_cases_level_selected.loc[df_weekly_cases_level_selected['noticia'].isna(), 'noticia'] = ''
            trace1 = go.Bar(
                x=df_weekly_cases_level_selected['week_number'],
                y=df_weekly_cases_level_selected['new_deaths_week_division'],
                customdata=df_weekly_cases_level_selected['noticia'].to_numpy(),
                width=widths,
                offset=0,
                showlegend=False,
                # marker_color=next(palette),
            )
            fig.append_trace(trace1, 1, 1)

            # Como o gráfico é um stacked bar, para corrigir a quantidade de óbitos devemos fazer a diferença entre os
            # óbitos no nível acima do selecionado e o nível selecionado
            df_weekly_cases_level_up_fixed = df_weekly_cases_level_up.merge(df_weekly_cases_level_selected, how='left',
                                                                            on=['week_number', 'noticia'])
            df_weekly_cases_level_up_fixed['new_deaths_week_division'] = df_weekly_cases_level_up_fixed[
                                                                             'new_deaths_week_division_x'] - \
                                                                         df_weekly_cases_level_up_fixed[
                                                                             'new_deaths_week_division_y']
        else: # Caso o usuário ainda não tenha selecionado nenhum nível, apenas copiamos os dados a nível Brasil para
              # serem plotados
            df_weekly_cases_level_up_fixed = df_weekly_cases_level_up.copy()

        # Plotar óbitos semanais para acima ao nível selecionado
        trace2 = go.Bar(
            x=df_weekly_cases_level_up_fixed['week_number'],
            y=df_weekly_cases_level_up_fixed['new_deaths_week_division'],
            customdata=df_weekly_cases_level_up_fixed['noticia'].to_numpy(),
            width=widths,
            offset=0,
            showlegend=False,
            # marker_color=next(palette),    
            marker=dict(
                color='rgba(219, 64, 82, 0.7)',
                line=dict(
                    color='rgba(219, 64, 82, 1.0)',
                    width=2)
        ))
        fig.append_trace(trace2, 1, 1)
        

        # Plotar as predições de óbitos diária
        if not df_predictions_filtered.empty: # Plotar apenas se o usuário chegou a selecionar algum município
            trace3 = go.Scatter(
                x=df_predictions_filtered['week_number_day'],
                y=df_predictions_filtered['obitosPreditos'],
                line=dict(color='rgb(0,100,80)'),
                mode='lines',
                customdata=df_predictions_filtered['obitosPreditos'],
                showlegend=False
            )
            trace4 = go.Scatter(
                name='Upper Bound',
                x=df_predictions_filtered['week_number_day'],
                y=df_predictions_filtered['upper'],
                line=dict(width=0),
                mode='lines',
                customdata=df_predictions_filtered['upper'],
                marker=dict(color="#444"),
                showlegend=False
            )
            trace5 = go.Scatter(
                name='Lower Bound',
                x=df_predictions_filtered['week_number_day'],
                y=df_predictions_filtered['lower'],
                line=dict(width=0),
                mode='lines',
                customdata=df_predictions_filtered['lower'],
                marker=dict(color="#444"),
                showlegend=False,
                fillcolor='rgba(68, 68, 68, 0.3)',
                fill='tonexty',
            )
            fig.append_trace(trace3, 1, 1)
            fig.append_trace(trace4, 1, 1)
            fig.append_trace(trace5, 1, 1)

        ################################################################################################################
        ###########################################     Gráfico de baixo     ###########################################
        ################################################################################################################
        widths = np.array([1] * df_weekly_cases_level_down['week_number'].nunique())  # Vetor de tamanho das barras

        # Plotar porcentagem de óbitos grupo a grupo em um stacked bar chart
        for group, dfg in df_weekly_cases_level_down.groupby(by=level):
            trace_bar = go.Bar(name=group,
                               x=dfg['week_number'],
                               y=dfg['percentage_deaths'],
                               width=widths,
                               offset=0,
                               # marker_color=next(palette),
                        )

            fig.append_trace(trace_bar, 2, 1)

        ################################################################################################################
        ######################################     Ajustar layout das figuras     ######################################
        ################################################################################################################
        fig.update_traces(
            hovertemplate="%{customdata}<extra></extra>",
             hoverlabel = dict(bgcolor = 'yellow', font_size=14,
                              font_family="Arial"),
            row=1
        )

        fig.update_xaxes(
            tickvals=np.cumsum(widths) - widths / 2,
            # ticktext=["%s<br>%d" % (l, w) for l, w in zip(labels, widths)]
            ticktext=[pd.to_datetime(d).strftime('%m/%y') for d in df_weekly_cases_level_up['data'].unique()], 
            tickfont_size=14,  tickangle = 90     )

        fig.update_layout(yaxis_title="Óbitos semanais",
                          font=dict(
                              family="arial",
                              size=14),
                          template="plotly_white",
                          plot_bgcolor='rgba(0,0,0,0)',
                          margin=dict(l=20, r=20, b=20, t=30),
                          width=1050,
                          height=650,
                          hoverlabel=dict(
                              bgcolor="white",
                              font_size=14,
                              font_family="Arial"
                          ),
                          xaxis_tickformat='<b>%d %B (%a)<br>%Y </b>',
                          barmode='stack',
                          )

        st.plotly_chart(fig, use_container_width=True)

        ################################################################################################################
        # Área destinada ao teste de clicks
        ################################################################################################################
        # out = Output()
        #
        # @out.capture(clear_output=False)
        # def handle_click(trace, points, state):
        #     st.text_area('opaaaaaaa')
        #
        # stacked_bar.data[0].on_click(handle_click)
        # VBox([stacked_bar, out])
        ################################################################################################################


def about():
    st.write(
        """
    <div class="base-wrapper primary-span">
        <span class="section-header">O Projeto</span>
    </div>
    <div class="base-wrapper">
        <span>
            Plataforma Web para disponibilizar publicamente a previsão de casos 
            de óbito e vacinação relacionados à Covid-19 em nível municipal.
        </span>
    </div>""",
        unsafe_allow_html=True,
    )

    st.write(
        """
    <div class="base-wrapper primary-span">
        <span class="section-header">A Gerência</span>
    </div>""",
        unsafe_allow_html=True,
    )

    st.write(
        """
    <div class="base-wrapper">
        <div style="font-size: 12px">
        </div>
        <div>
            <table class="info-table">
            <tbody>
                <tr>
                    <td class="grey-bg"><strong>Membro</strong></td>
                    <td class="grey-bg"><strong>Função</strong></td>
                </tr>
                <tr>
                    <td><span>Francisco Louzada Neto</span></td>
                    <td><span>CEO</span></td>
                </tr>
                <tr>
                    <td><span>Loriz Sallum </span></td>
                    <td><span>Diretora</span></td>
                </tr>
                <tr>
                    <td><span>Oilson Gonzatto</span></td>
                    <td><span>Diretor</span></td>
                </tr>
            </tbody>
            </table>
        </div>
    </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        """
    <div class="base-wrapper primary-span">
        <span class="section-header">Os membros da equipe</span>
    </div>""",
        unsafe_allow_html=True,
    )

    st.write(
        """
        <div class="base-wrapper">
            <div style="font-size: 12px">
            </div>
            <div>
                <table class="info-table">
                <tbody>
                    <tr>
                        <td class="grey-bg"><strong>Aluno</strong></td>
                        <td class="grey-bg"><strong>Função</strong></td>
                    </tr>
                    <tr>
                        <td><span>Bernardo</span></td>
                        <td><span>Estatístico</span></td>
                    </tr>
                    <tr>
                        <td><span>Bruno Braziel </span></td>
                        <td><span>Programador</span></td>
                    </tr>
                    <tr>
                        <td><span>Francisco Pigato</span></td>
                        <td><span>Coordenador</span></td>
                    </tr>
                    <tr>
                        <td><span>Lucas Nakadaira</span></td>
                        <td><span>Programador</span></td>
                    </tr>
                    <tr>
                        <td><span>Mariana Spanol</span></td>
                        <td><span>Estatística</span></td>
                    </tr>
                </tbody>
                </table>
            </div>
        </div>
            """,
        unsafe_allow_html=True,
    )


utils.localCSS(r"C:\Users\mscamargo\Desktop\estudos\my_proj\covid19_previsoes_municipios\src\style.css")
#utils.localCSS("style.css")
st.write(f"""<div>
            <div class="base-wrapper flex flex-column" style="background-color:#0277bd">
                <div class="white-span header p1" style="font-size:30px;">Acompanhamento Covid-19 - ICMC/MECAI - USP</div>
        </div>""",
         unsafe_allow_html=True,
         )
if page == 'Início':
    about()
elif page == 'Modelos preditivos':
        descriptive_models()
elif page == 'Modelos descritivos':
    predictive_models()
elif page == 'Sobre':
    about()

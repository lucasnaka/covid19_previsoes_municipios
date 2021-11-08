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

def main():
    st.set_page_config(
     layout="wide",
     initial_sidebar_state="expanded")
    
    matplotlib.use("Agg")
    st.title("Previsão de Obitos COVID-19 - ICMC/MECAI - USP")
    
    st.sidebar.title('Menu')
    pages = ('Início', 'Modelos preditivos', 'Modelos descritivos', 'Sobre')
    selected_page = st.sidebar.radio('Paginas', pages)

    csv_file = pd.read_csv('website/web_data/est_cidade.csv', sep=';', encoding='latin-1')
    states = list(csv_file['UF'].drop_duplicates().sort_values())

    df_casos = pd.read_parquet('data/app/covid_saude_obito_municipio.parquet')
    df_casos_reg = pd.read_parquet('data/app/covid_saude_obito_regiao.parquet')
    #csv_file = pd.read_csv('web_data/est_cidade.csv', sep=';', encoding='latin-1')
    #states = list(csv_file['UF'].drop_duplicates().sort_values())

    #df_casos = pd.read_parquet('../data/app/covid_saude_obito_municipio.parquet')
    #df_casos_reg = pd.read_parquet('../data/app/covid_saude_obito_regiao.parquet')


    df_casos['data'] = pd.to_datetime(df_casos['data'])
    df_casos_reg['data'] = pd.to_datetime(df_casos_reg['data'])

    def SetNewsSize(x):
        if not pd.isnull(x):
            return 7.5
        else:
            return 0


    def find_cities(selected_states):
        return list(csv_file[csv_file['UF'] == selected_states]['Município'].sort_values())


    def filter_state_city():
        choose_state = st.sidebar.checkbox('Filtrar por estado')
        choose_city = None
        selected_state = None
        selected_city = None

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


    def filters(df_casos, df_casos_reg):
        selected_filters = dict()
        selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
        selected_state, selected_city = filter_state_city()

        selected_filters['state'] = selected_state
        selected_filters['city'] = selected_city

        if selected_filters['city']:
            df_filtered = df_casos.loc[(df_casos['municipio'] == selected_filters['city'])]
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

        return selected_filters, df_filtered, df_casos_reg


    def home():
        st.title('Início')



    def predictive_models():
        st.title('Modelos preditivos')

        selected_filters, df_filtered, df_filtered_reg = filters(df_casos, df_casos_reg)
        if selected_filters:
            st.info(f"{selected_filters}")



    def descriptive_models():
        st.header('Modelos descritivos')

        col1, col2, col3 = st.beta_columns((13.0,2.0, 1.5))
        
        selected_filters, df_filtered, df_filtered_reg = filters(df_casos, df_casos_reg)
        if selected_filters:
            st.info(f"{selected_filters}")

        #     st.title('Número de óbitos por dia')
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df_filtered["data"],
                                y=df_filtered["obitosNovos"],
                                text=df_filtered['event'],
                                hoverinfo='text',
                                mode='lines+markers',
                                marker=dict(size=list(map(SetNewsSize, df_filtered['event'])),
                                           color=['orange'] * df_filtered.shape[0])
                                ),
                                                 hover_data=['noticia'],
                           title='Número de óbitos por dia')

        fig.update_layout(title="Line time series",
                        title_font_color="black",
                        font=dict(
                            family="arial",
                            size=15),
                        template="plotly_white")

        col1.plotly_chart(fig,use_container_width=True)

        fig = px.bar(df_filtered_reg,
                    x=df_filtered_reg['data'],
                    y=df_filtered_reg['percentage_deaths'],
                    color='regiao',
                    text=df_filtered_reg['percentage_deaths'].apply(lambda x: '{0:1.2f}%'.format(x)))
        fig.update_layout(title="Stacked bar with '%' for Regions",
                        title_font_color="black",
                        yaxis_title="% Casos por Regiao",
                        font=dict(
                            family="arial",
                            size=15),
                        template="plotly_white")
        
        col1.plotly_chart(fig,use_container_width=True)

        mean_ob = np.mean(df_filtered["obitosNovos"])
        new_title = f'<p style="background: #76BCFB;width: 100px; height: 100px; font-family:arial; color:Black; font-size: 18px;">Média Obitos BR: {mean_ob: .2f}</p>'
        col2.markdown(new_title, unsafe_allow_html=True)
        
        new_title = f'<p style="background: #76BCFB; ;width: 100px; height: 100px;font-family:arial; color:Black; font-size: 18px;">Média Obitos BR: {mean_ob: .2f}</p>'
        col3.markdown(new_title, unsafe_allow_html=True)
        
        new_title = f'<p style="background: #76BCFB;width: 100px; height: 100px; font-family:arial; color:Black; font-size: 18px;">Média Obitos BR: {mean_ob: .2f}</p>'
        col2.markdown(new_title, unsafe_allow_html=True)
        
        new_title = f'<p style="background: #76BCFB; ;width: 100px; height: 100px;font-family:arial; color:Black; font-size: 18px;">Média Obitos BR: {mean_ob: .2f}</p>'
        col3.markdown(new_title, unsafe_allow_html=True)





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


    # In[ ]:
    if selected_page == 'Início':
        home()
    elif selected_page == 'Modelos preditivos':
        predictive_models()
    elif selected_page == 'Modelos descritivos':
        descriptive_models()
    elif selected_page == 'Sobre':
        about()

main()
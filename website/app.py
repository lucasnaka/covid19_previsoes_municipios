#!/usr/bin/env python
# coding: utf-8

import streamlit as st 
from PIL import Image

import matplotlib.pyplot as plt 
import matplotlib
import seaborn as sns
import pandas as pd 
import numpy as np
import datetime as dt

matplotlib.use("Agg")

st.sidebar.title('Menu')
pages = ('Início', 'Modelos preditivos', 'Modelos descritivos', 'Sobre')
selected_page = st.sidebar.radio('Paginas', pages)

csv_file = pd.read_csv('../covid19_previsoes_municipios/website/web_data/est_cidade.csv', sep=';', encoding='latin-1')
states = list(csv_file['UF'].drop_duplicates().sort_values())

df_casos = pd.read_parquet('../covid19_previsoes_municipios/data/app/covid_saude_obito_municipio.parquet')
df_casos['data'] = pd.to_datetime(df_casos['data'])

def find_cities(selected_states):
    return list(csv_file[csv_file['UF']==selected_states]['Município'].sort_values())

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
    date_range = (dt.date(min_date.year, min_date.month, min_date.day), dt.date(max_date.year, max_date.month, max_date.day))
    selected_date = None    

    if choose_date:
        selected_date = st.sidebar.slider('Data', value=date_range, format="DD/MM/YYYY")

    return selected_date

def filters(df_casos):
    selected_filters = dict()
    selected_data = st.sidebar.selectbox('Dados disponíveis', ('Casos Confirmados', 'Óbitos', 'Vacinação'))
    selected_state, selected_city = filter_state_city()
    
    selected_filters['state'] =  selected_state
    selected_filters['city']  = selected_city
    
    if selected_filters['city']:
        df_filtered = df_casos.loc[(df_casos['municipio']==selected_filters['city'])]
    else:
        df_filtered = df_casos.loc[(df_casos['municipio']=='São Paulo')]
        
    selected_date_range = filter_date(df_filtered)

    selected_filters['database'] = selected_data
    selected_filters['date'] = selected_date_range
    
    if selected_filters['date']:
        df_filtered = df_filtered.loc[(df_filtered['data'].dt.date>=selected_filters['date'][0]) & (df_filtered['data'].dt.date<=selected_filters['date'][1])]
    
    return selected_filters, df_filtered

def home():
    st.title('Início')

def predictive_models():
    st.title('Modelos preditivos')

    selected_filters, df_filtered = filters(df_casos)
    if selected_filters:
        st.info(f"{selected_filters}") 


def descriptive_models():
    st.title('Modelos descritivos')

    selected_filters, df_filtered = filters(df_casos)
    if selected_filters:
        st.info(f"{selected_filters}")
    
    st.title('Número de óbitos por dia')
    st.line_chart(df_filtered[['data', 'obitosNovos']].set_index('data'))
        
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

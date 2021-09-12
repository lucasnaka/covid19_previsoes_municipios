#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st 
from PIL import Image

import matplotlib.pyplot as plt 
import matplotlib
matplotlib.use("Agg")
import seaborn as sns
import pandas as pd 
import numpy as np
import datetime as dt


# In[ ]:


st.markdown("# COVID-19")
st.markdown("Explore the dataset to know more about palmerpenguins")
# img=Image.open('images/palmerpenguins.png')
# st.image(img,width=100)
st.markdown("**Penguins** are some of the most recognizable and beloved birds in the world and even have their own holiday: **World Penguin Day is celebrated every year on April 25**. Penguins are also amazing birds because of their physical adaptations to survive in unusual climates and to live mostly at sea. Penguins propel themselves through water by flapping their flippers.  Bills tend to be long and thin in species that are primarily fish eaters, and shorter and stouter in those that mainly eat krill.”)st.markdown(“The data presented are of 3 different species of penguins - **Adelie, Chinstrap, and Gentoo,** collected from 3 islands in the **Palmer Archipelago, Antarctica.**")


# In[ ]:


df_covid_saude_obitos = pd.read_parquet('../data/app/covid_saude_obito_municipio.parquet')


# In[ ]:


def filter_slider_dates(message, df):
    date_array = np.array(df['data'].unique())
    date_len = df['data'].nunique()
    
    slider_1, slider_2 = st.slider('%s' % (message), 0, date_len-1, [0,date_len-1], 1)

    # Ordenar array para buscarmos valor pelos index slider_1 e slider_2
    date_array.sort()
    
    start_date = dt.datetime.strptime(str(date_array[slider_1]),'%Y-%m-%d')
    start_date = start_date.strftime('%d %b %Y')

    end_date = dt.datetime.strptime(str(date_array[slider_2]),'%Y-%m-%d')
    end_date = end_date.strftime('%d %b %Y')

    st.info('Início: **%s** Fim: **%s**' % (start_date,end_date))

    filtered_df = df.loc[(df['data']>=date_array[slider_1]) & (df['data']<=date_array[slider_2])]

    return filtered_df


# In[ ]:


def filter_slider_city(message, df):
    cities_list = list(df['municipio'].unique())
    
    city = st.selectbox('%s' % (message), options=tuple(cities_list), index=cities_list.index("São Paulo"))
    
    filtered_df = df.loc[df['municipio']==city]

    return filtered_df


# In[ ]:


column_1, column_2 = st.beta_columns(2)


# In[ ]:


with column_1:
    st.title('Filtro de datas')
    df_filtered = filter_slider_dates('Move sliders to filter dataframe', df_covid_saude_obitos)


# In[ ]:


with column_2:
    st.title('Filtro de Municípios')
    df_filtered = filter_slider_city('Move sliders to filter dataframe', df_filtered)


# In[ ]:


st.title('Número de óbitos por dia')
st.line_chart(df_filtered[['data', 'obitosNovos']].set_index('data'))


# In[ ]:





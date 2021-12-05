# Instala pacotes

#install.packages('fable')
#install.packages('tidyverse')
#install.packages('urca')
#install.packages("arrow")

# Importa bibliotecas

library(tidyverse)
library(tsibble)
library(lubridate)
library(fable)
library(arrow)
library(forecast)
library(feasts)

# Declara o caminho para os dataframes principais

path_data = 'C:/Users/berna/Desktop/covid/results/'

# Cria os dataframes de município, estado, brasil, regional e regionais de saúde

df_mun <-
  read.csv(paste0(path_data,'df_mun.csv'), encoding = 'UTF-8',
           na.strings=c("","NA")) %>% select(-index) 
df_mun$data <- as.Date(df_mun$data)
df_mun <- df_mun %>% as_tsibble(key = codmun, index = data)

df_uf <-
  read.csv(paste0(path_data,'df_uf.csv'), encoding = 'UTF-8',
           na.strings=c("","NA")) %>% select(-index)
df_uf$data <- as.Date(df_uf$data)
df_uf <- df_uf %>% as_tsibble(key = estado, index = data)

df_regional_saude <-
  read.csv(paste0(path_data,'df_regional_saude.csv'), encoding = 'UTF-8',
           na.strings=c("","NA")) %>% select(-index)
df_regional_saude$data <- as.Date(df_regional_saude$data)
df_regional_saude <- df_regional_saude %>% as_tsibble(key = codRegiaoSaude, index = data)

df_regional <-
  read.csv(paste0(path_data,'df_regional.csv'), encoding = 'UTF-8',
           na.strings=c("","NA")) %>% select(-index)
df_regional$data <- as.Date(df_regional$data)
df_regional <- df_regional %>% as_tsibble(key = regiao, index = data)

df_brasil <-
  read.csv(paste0(path_data,'df_brasil.csv'), encoding = 'UTF-8',
           na.strings=c("","NA")) %>% select(-index)
df_brasil$data <- as.Date(df_brasil$data)
df_brasil <- df_brasil %>% as_tsibble(key = regiao, index = data)

# Ajusta os modelos para todos os níveis0

I = Sys.time()

fit_mun <- df_mun %>%
  model(arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
        sarima = ARIMA(obitosNovos)) %>%
  mutate(mixed = (arima + sarima) / 2)
fit_mun

fit_uf <- df_uf %>%
  model(arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
        sarima = ARIMA(obitosNovos)) %>%
  mutate(mixed = (arima + sarima) / 2)
fit_uf

fit_reg <- df_regional %>%
  model(arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
        sarima = ARIMA(obitosNovos)) %>%
  mutate(mixed = (arima + sarima) / 2)
fit_reg

fit_reg_saude <- df_regional_saude %>%
  model(arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
        sarima = ARIMA(obitosNovos)) %>%
  mutate(mixed = (arima + sarima) / 2)
fit_reg_saude

fit_brasil <- df_brasil %>%
  model(arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
        sarima = ARIMA(obitosNovos)) %>%
  mutate(mixed = (arima + sarima) / 2)
fit_brasil

# fit_mun <- df_mun %>%
#   model(
#     arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
#     sarima = ARIMA(obitosNovos),
#     nnetar = NNETAR(obitosNovos)#,
#   ) %>%
#   mutate(mixed = (arima + sarima + nnetar) / 3)
# fit_mun

# fit_uf <- df_uf %>%
#   model(
#     arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
#     sarima = ARIMA(obitosNovos),
#     nnetar = NNETAR(obitosNovos)#,
#   ) %>%
#   mutate(mixed = (arima + sarima + nnetar) / 3)
# fit_uf

# fit_reg <- df_regional %>%
#   model(
#     arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
#     sarima = ARIMA(obitosNovos),
#     nnetar = NNETAR(obitosNovos)#,
#   ) %>%
#   mutate(mixed = (arima + sarima + nnetar) / 3)
# fit_reg

# fit_reg_saude <- df_regional_saude %>%
#   model(
#     arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
#     sarima = ARIMA(obitosNovos),
#     nnetar = NNETAR(obitosNovos)#,
#   ) %>%
#   mutate(mixed = (arima + sarima + nnetar) / 3)
# fit_reg_saude

# fit_brasil <- df_brasil %>%
#   model(
#     arima = ARIMA(obitosNovos ~ PDQ(0, 0, 0)),
#     sarima = ARIMA(obitosNovos),
#     nnetar = NNETAR(obitosNovos)#,
#   ) %>%
#   mutate(mixed = (arima + sarima + nnetar) / 3)
# fit_brasil

# Realiza as predições para 30 dias a frente com um certo intervalo de confiança

fc_mun <-
  fit_mun %>% forecast(h = 30) %>% hilo(level = c(80)) %>% unpack_hilo("80%")

fc_uf <-
  fit_uf %>% forecast(h = 30) %>% hilo(level = c(80)) %>% unpack_hilo("80%")

fc_reg_saude <-
  fit_reg_saude %>% forecast(h = 30) %>% hilo(level = c(80)) %>% unpack_hilo("80%")

fc_reg <-
  fit_reg %>% forecast(h = 30) %>% hilo(level = c(80)) %>% unpack_hilo("80%")

fc_brasil <-
  fit_brasil %>% forecast(h = 30) %>% hilo(level = c(80)) %>% unpack_hilo("80%")

# Renomea as colunas das tabelas de resultados

fc_mun = as.data.frame(fc_mun %>% rename(obitosPreditos = .mean, modelo = .model))
names(fc_mun)[7] <- 'ic_lower'
names(fc_mun)[8] <- 'ic_upper'

fc_uf = as.data.frame(fc_uf %>% rename(obitosPreditos = .mean, modelo = .model))
names(fc_uf)[6] <- 'ic_lower'
names(fc_uf)[7] <- 'ic_upper'

fc_reg_saude = as.data.frame(fc_reg_saude %>% rename(obitosPreditos = .mean, modelo = .model))
names(fc_reg_saude)[6] <- 'ic_lower'
names(fc_reg_saude)[7] <- 'ic_upper'

fc_reg = as.data.frame(fc_reg %>% rename(obitosPreditos = .mean, modelo = .model))
names(fc_reg)[6] <- 'ic_lower'
names(fc_reg)[7] <- 'ic_upper'

fc_brasil = as.data.frame(fc_brasil %>% rename(obitosPreditos = .mean, modelo = .model))
names(fc_brasil)[6] <- 'ic_lower'
names(fc_brasil)[7] <- 'ic_upper'

# Adiciona colunas as tabela de resultados

df_join = df_mun[, c(
  'municipio',
  'codmun',
  'estado',
  'coduf',
  'codRegiaoSaude',
  'nomeRegiaoSaude',
  'regiao'
)] %>% distinct()
output_mun <-
  left_join(fc_mun, df_join, by = c("codmun" = "codmun"))

df_join = df_mun[, c('estado',
                    'coduf',
                    'codRegiaoSaude',
                    'nomeRegiaoSaude',
                    'regiao')] %>% distinct()
output_uf <- left_join(fc_uf, df_join, by = c("estado" = "estado"))

df_join = df_mun[, c('codRegiaoSaude', 'nomeRegiaoSaude', 'regiao')] %>% distinct()
output_reg_saude <-
  left_join(fc_reg_saude,
            df_join,
            by = c("codRegiaoSaude" = "codRegiaoSaude"))

# Considera os intervalos mais conservadores para o modelo de mistura

output_mun$codmun_data = paste0(output_mun$codmun, output_mun$data)
output_mun = merge(
  output_mun,
  aggregate(ic_upper ~ codmun_data, output_mun, FUN = max),
  all.x = TRUE,
  by = "codmun_data"
) %>% rename(upper = ic_upper.y)

output_mun = merge(
  output_mun,
  aggregate(ic_lower ~ codmun_data, output_mun, FUN = min),
  all.x = TRUE,
  by = "codmun_data"
) %>% rename(lower = ic_lower.y)

output_uf$coduf_data = paste0(output_uf$coduf, output_uf$data)
output_uf = merge(
  output_uf,
  aggregate(ic_upper ~ coduf_data, output_uf, FUN = max),
  all.x = TRUE,
  by = "coduf_data"
) %>% rename(upper = ic_upper.y)

output_uf = merge(
  output_uf,
  aggregate(ic_lower ~ coduf_data, output_uf, FUN = min),
  all.x = TRUE,
  by = "coduf_data"
) %>% rename(lower = ic_lower.y)

output_reg_saude$codRegiaoSaude_data = paste0(output_reg_saude$codRegiaoSaude, output_reg_saude$data)
output_reg_saude = merge(
  output_reg_saude,
  aggregate(ic_upper ~ codRegiaoSaude_data, output_reg_saude, FUN = max),
  all.x = TRUE,
  by = "codRegiaoSaude_data"
) %>% rename(upper = ic_upper.y)

output_reg_saude = merge(
  output_reg_saude,
  aggregate(ic_lower ~ codRegiaoSaude_data, output_reg_saude, FUN = min),
  all.x = TRUE,
  by = "codRegiaoSaude_data"
) %>% rename(lower = ic_lower.y)

fc_reg$regiao_data = paste0(fc_reg$regiao, fc_reg$data)
output_reg = merge(
  fc_reg,
  aggregate(ic_upper ~ regiao_data, fc_reg, FUN = max),
  all.x = TRUE,
  by = "regiao_data"
) %>% rename(upper = ic_upper.y)

output_reg = merge(
  output_reg,
  aggregate(ic_lower ~ regiao_data, output_reg, FUN = min),
  all.x = TRUE,
  by = "regiao_data"
) %>% rename(lower = ic_lower.y)

output_brasil = merge(
  fc_brasil,
  aggregate(ic_upper ~ data, fc_brasil, FUN = max),
  all.x = TRUE,
  by = "data"
) %>% rename(upper = ic_upper.y)

output_brasil = merge(
  output_brasil,
  aggregate(ic_lower ~ data, output_brasil, FUN = min),
  all.x = TRUE,
  by = "data"
) %>% rename(lower = ic_lower.y)

# Filtra as colunas finais e salva os resultados em csvs

output_mun = output_mun %>% filter(modelo == 'mixed') %>%
  select(
    municipio,
    codmun,
    estado,
    coduf,
    codRegiaoSaude,
    nomeRegiaoSaude,
    regiao,
    data,
    obitosPreditos,
    lower,
    upper
  )
output_mun$lower = pmax(output_mun$lower,0)
output_mun$upper = pmax(output_mun$upper,0)
output_mun$obitosPreditos = pmax(output_mun$obitosPreditos,0)

write.csv(output_mun, 'results/prediction_mun.csv', row.names = FALSE)

output_uf = output_uf %>% filter(modelo == 'mixed') %>%
  select(estado,
         coduf,
         codRegiaoSaude,
         nomeRegiaoSaude,
         regiao,
         data,
         obitosPreditos,
         lower,
         upper
  )
output_uf$lower = pmax(output_uf$lower,0)
output_uf$upper = pmax(output_uf$upper,0)
output_uf$obitosPreditos = pmax(output_uf$obitosPreditos,0)

write.csv(output_uf, 'results/prediction_uf.csv', row.names = FALSE)

output_reg_saude = output_reg_saude %>% filter(modelo == 'mixed') %>%
  select(codRegiaoSaude,
             nomeRegiaoSaude,
             regiao,
             data,
             obitosPreditos,
             lower,
             upper)
output_reg_saude$lower = pmax(output_reg_saude$lower,0)
output_reg_saude$upper = pmax(output_reg_saude$upper,0)
output_reg_saude$obitosPreditos = pmax(output_reg_saude$obitosPreditos,0)

write.csv(output_reg_saude, 'results/prediction_reg_saude.csv', row.names = FALSE)

output_reg = output_reg %>% filter(modelo == 'mixed') %>%
  select(regiao,
         data,
         obitosPreditos,
         lower,
         upper)
output_reg$lower = pmax(output_reg$lower,0)
output_reg$upper = pmax(output_reg$upper,0)
output_reg$obitosPreditos = pmax(output_reg$obitosPreditos,0)

write.csv(output_reg, 'results/prediction_reg.csv', row.names = FALSE)

output_brasil = output_brasil %>% filter(modelo == 'mixed') %>%
  select(data,
         obitosPreditos,
         lower,
         upper)
output_brasil$lower = pmax(output_brasil$lower,0)
output_brasil$upper = pmax(output_brasil$upper,0)
output_brasil$obitosPreditos = pmax(output_brasil$obitosPreditos,0)

write.csv(output_brasil, 'results/prediction_brasil.csv', row.names = FALSE)

print(Sys.time() - I)

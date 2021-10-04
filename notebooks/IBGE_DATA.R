install.packages("basedosdados")
library(basedosdados)

set_billing_id("covid-data-master")

# renda per capita, densidade de moradores por comodo, quantidade de comodos
query <- "SELECT 
*
FROM `basedosdados.br_ibge_censo_demografico.microdados_domicilio_2010` 
limit 1"

#id_municipio, v6531, v0203, v6203, sigla_uf 

b <- read_sql(query)

# total pop
query <- "SELECT 
* 
FROM `basedosdados.br_ibge_populacao.municipio` 
limit 10"

b <- read_sql(query)

#% alfabetizados e % adultos alfabetizados
query <-  "SELECT 
* 
FROM `basedosdados.br_ibge_censo_demografico.setor_censitario_alfabetizacao_total_2010`
limit 10"

b <- read_sql(query)

# % da pop jovem adulto idoso
query <-  "SELECT 
* 
FROM `basedosdados.br_ibge_censo_demografico.setor_censitario_idade_total_2010`
limit 10"

b <- read_sql(query)

query <- "SELECT 
* 
FROM `basedosdados.br_bd_diretorios_brasil.setor_censitario`
limit 10"
b <- read_sql(query)


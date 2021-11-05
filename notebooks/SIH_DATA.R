install.packages("devtools")
devtools::install_github("rfsaldanha/microdatasus")
library(microdatasus)

dados <- fetch_datasus(year_start = 2021, month_start = 1, year_end = 2021, month_end = 7,
              uf = "TO", information_system = "SIH-RD")

dados <- process_sih(dados, municipality_data = T)

unique(dados$ESPEC)


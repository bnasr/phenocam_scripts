library(data.table)

output_file <- '~/Projects/crowdSource/outputFile.txt'

dt <- setDT(read.csv(output_file, col.names = c('time', 'user', 'id', 'file', 'question', 'value', 'comment')))
dt[,file := paste0('/projects/phenocam', file)]
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Snow', .(file, value)], file = 'snow_training_data.csv', row.names = F)
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Cloud', .(file, value)], file = 'cloud_training_data.csv', row.names = F)
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Fog or Haze', .(file, value)], file = 'haze_training_data.csv', row.names = F)

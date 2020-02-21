library(data.table)

output_file <- '~/Projects/crowdSource/outputFile.txt'

dt <- setDT(read.csv(output_file, col.names = c('time', 'user', 'id', 'file', 'question', 'value', 'comment')))
dt[,file := paste0('/projects/phenocam', file)]
dt[,local:=paste0('images/', basename(as.character(file)))]
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Snow', .(files = local, label = value)], file = '/hdd/Projects/phenocam_scripts/crow_source_compile/snow_training_data.csv', row.names = F)
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Cloud', .(files = local, label = value)], file = '/hdd/Projects/phenocam_scripts/crow_source_compile/cloud_training_data.csv', row.names = F)
write.csv(dt[user!='test' & user!='bijan' & value !=9 & question == 'Fog or Haze', .(files = local, label = value)], file = '/hdd/Projects/phenocam_scripts/crow_source_compile/haze_training_data.csv', row.names = F)

file.copy(from = unique(gsub(dt$file, pattern = '/projects/phenocam/data/archive', replacement = '/data/thumbnails')), 
          overwrite = F,
          to = '/hdd/Projects/phenocam_scripts/crow_source_compile/thumbnails/')

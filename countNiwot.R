library(data.table)
y <- year(Sys.Date())

inout_dir <- '/home/bijan/phenocam_scripts/'

dt <- fread(paste0(inout_dir, 'countNiwot.txt'), skip =2)
dt[, V1 := as.numeric(gsub(pattern = 'DOY |:', replacement = '', V1))]
dt[, date := as.Date(sprintf('%04d-12-31', y - 1)) + V1]
dt[, n := V2]
dt$V1 <- NULL
dt$V2 <- NULL


# today's date
today <- Sys.Date()

# date range to plot
date_range <- today - c(33:26)


png(paste0(inout_dir, 'countNiwot.png'),
    width = 8, height = 5, units = 'in', res = 300)
plot(dt[date  %in% date_range],
     xlim = range(date_range),
     ylab = 'Daily Count',
     type = 'l')
mtext('Number of files', line = 1)
dev.off()


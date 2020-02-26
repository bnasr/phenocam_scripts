library(phenocamapi)
library(xROI)
library(jpeg)


rois <- get_rois()
phenos <- get_phenos()

rois <- merge(rois, phenos[,.(site, site_type)])

n <- nrow(rois)
# i=233
pb <- txtProgressBar(1, n, style = 3)
for(i in 1:n){
  site <- rois[i, site]
  roi_name <- rois[i, roi_name]
  site_type <- rois[i, site_type]
  
  roi <- parseROI(paste0('/data/archive/', site, '/ROI/', roi_name, '_roi.csv'))
  startdate <- as.Date(sapply(roi$masks, FUN = function(x){x$startdate}))
  enddate <- as.Date(sapply(roi$masks, FUN = function(x){x$enddate}))
  
  ts1 <- as.data.table(read.csv(paste0('/data/archive/', site, '/ROI/', roi_name, '_1day.csv'), header = T, skip =22))
  ts1[, date := as.Date(date)]
  ts3 <- as.data.table(read.csv(paste0('/data/archive/', site, '/ROI/', roi_name, '_3day.csv'), header = T, skip =22))
  ts3[, date := as.Date(date)]
  
  # clRange <- range(ts3$date)
  
  cli <- try(readJPEG(paste0('/data/archive/', site, '/ROI/', site, '-cli.jpg')))
  if(class(cli)=='try-error') next()
  clitxt <- as.data.table(read.csv(paste0('/data/archive/', site, '/ROI/', site, '-cli.txt')))
  clitxt[, Date := as.Date(Date)]
  xrange <- range(as.Date(clitxt$Date))
  
  # w <- (clitxt$Date>=clRange[1]) & (clitxt$Date<=clRange[2]) 
  
  png(file = paste0('rois/', roi_name, '.png'), width = 11, height = 5, res = 300, units = 'in')
  
  par(mfrow = c(2,1), mar = c(0,0,0,0), oma = c(2,2,2,0))
  plot(ts1$date, ts1$gcc_90, col = 'cyan', type = 'l', xaxs='i',yaxs='i',  xaxt = 'n', xlim = xrange)
  lines(ts3$date, ts3$gcc_90, col = 'black', lty =1)
  abline(v = startdate, col = 'red')
  abline(v = enddate, col = 'red')
  
  legend('topright', legend = c('1-day', '3-day', 'mask'), 
         col = c('cyan', 'black', 'red'), lty = c(1,1,1), lwd = c(2,2,2), bty = 'n')
  
  plot(ts3$date, ts3$gcc_90, type = 'n', xaxs='i',yaxs='i', yaxt = 'n', xlim = xrange)
  usr <- par()$usr
  rasterImage(cli, usr[1], usr[3], usr[2], usr[4])
  abline(v = startdate, col = 'yellow')
  abline(v = enddate, col = 'yellow')
  # polygon(usr[c(1,2,2,1)], usr[c(3,3,4,4)], border = 'yellow', lwd= 5)
  
  mtext(paste(roi_name, '   Type = ', site_type), outer = T)
  
  dev.off()
  
  setTxtProgressBar(pb, i)
}


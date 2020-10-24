# ROI	Status
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D03.OSBS.DP1.00033/EN_1001/	Redundant ROI
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D10.ARIK.DP1.20002/GR_1000/	Borken time series
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D10.CPER.DP1.00033/GR_1000/	Check
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D15.ONAQ.DP1.00042/GR_1000/	Dry 2020
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D16.WREF.DP1.00033/EN_1000/	Check
# https://phenocam.sr.unh.edu/webcam/roi/NEON.D17.SOAP.DP1.00033/EN_1000/	Chek

library(phenocamapi, warn.conflicts = TRUE, quietly = TRUE)
library(data.table)

phenos <- get_phenos()
rois <- get_rois()

out_dir <- '/home/bijan/phenocam_scripts/'
if(Sys.info()['nodename'] =='Bijans-MacBook-Pro.local') out_dir ='~/Projects/phenocam_scripts/'

neon_rois <- rois[(sequence_number%%1000==0) & grepl(site, pattern = 'NEON')]

neon_rois <- merge(neon_rois[, .(roi_name, site, 
                                 roi_first_date = first_date,
                                 roi_last_date = last_date, 
                                 one_day_summary, 
                                 site_years,
                                 missing_data_pct)], 
                   phenos[, .(site, 
                              site_first_date = date_first, 
                              site_last_date = date_last)], 
                   by = 'site')

write.table(phenos[grepl(x= site, pattern = 'NEON'), 
                   .(site, lat, lon, elev, 
                     utc_offset, contact1, contact2, 
                     site_description, site_acknowledgements, site_type, group, 
                     camera_description, camera_orientation, 
                     flux_data, flux_networks_name, flux_sitenames, 
                     dominant_species, primary_veg_type, secondary_veg_type, 
                     MAT_site, MAP_site)], 
            sep = ',',
            file = paste0(out_dir, 'neon_sites_metadata.csv'),
            row.names = FALSE)


phenocam_server = "http://phenocam.sr.unh.edu"

n <- nrow(neon_rois)
neon_rois[, skipped_dates := NA]

pb = txtProgressBar(1, n, style = 3)

skipped_dates_file <- file(paste0(out_dir, 'check_neon_skipped_dates_file.csv'), open = 'w')
close(skipped_dates_file)

skipped_middays_file <- file(paste0(out_dir, 'check_neon_skipped_middays_file.csv'), open = 'w')
close(skipped_middays_file)

check_neon <- file(paste0(out_dir, 'check_neon.csv'), open = 'w')
writeLines('roi_name,site_years,missing_data_pct,skipped_dates,skipped_middays', con = check_neon)
close(check_neon)


for(i in 1:n){
  roi_name <- neon_rois[i, roi_name]
  site <- neon_rois[i, site]
  roi_first_date <- neon_rois[i, roi_first_date]
  roi_last_date <- neon_rois[i, roi_last_date]
  
  ts <- fread(neon_rois[i, one_day_summary], verbose = FALSE, showProgress = FALSE)
  
  url <- sprintf("%s/webcam/network/middayimglist/%s", phenocam_server, site)
  midday_table <- try(jsonlite::fromJSON(url))  
  
  if(class(midday_table)!='try-error'){
    midday <- setDT(midday_table$images)
    
    dt <- merge(midday[as.Date(date) > roi_first_date & as.Date(date) < roi_last_date,
                       .(date, midday = TRUE)], ts[!is.na(gcc_mean),.(date, gcc = TRUE)], all = TRUE)
    
    skipped_dates <- dt[!is.na(midday) & is.na(gcc), date]
    skipped_middays <- dt[is.na(midday) & !is.na(gcc), date]
    
    if(length(skipped_dates) > 0 ){
      skipped_dates_file <- file(paste0(out_dir, 'check_neon_skipped_dates_file.csv'), open = 'a')
      writeLines(paste(site, skipped_dates, sep = ','), con = skipped_dates_file)
      close(skipped_dates_file)
    }    
    
    if(length(skipped_middays) > 0 ){
      skipped_middays_file <- file(paste0(out_dir, 'check_neon_skipped_middays_file.csv'), open = 'a')
      writeLines(paste(site, skipped_middays, sep = ','), con = skipped_middays_file)
      close(skipped_middays_file)
    }    
    
    check_neon <- file(paste0(out_dir, 'check_neon.csv'), open = 'a')
    writeLines(paste(neon_rois$roi_name[i],
                     neon_rois$site_years[i],
                     neon_rois$missing_data_pct[i],
                     length(skipped_dates), 
                     length(skipped_middays), 
                     sep = ','), 
               con = check_neon)
    close(check_neon)
    
  }
  setTxtProgressBar(pb, i)
}


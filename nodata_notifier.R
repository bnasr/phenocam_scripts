# Send notifying emails when data is not available

#library(R.oo, warn.conflicts = F)
#library(R.methodsS3, warn.conflicts = F)
#library(methods)

library(lubridate, warn.conflicts = F)
library(data.table, warn.conflicts = F)
library(rjson, warn.conflicts = F)
#library(rJava, warn.conflicts = F)
library(mailR, warn.conflicts = F)
library(phenocamapi, warn.conflicts = F)

phenos <- get_phenos()

#current path on klima
working_dir <- '~/phenocam_scripts/'

#path on Bijan's machine for debug
if(Sys.info()['nodename']=="Bijans-MacBook-Pro.local") working_dir <- './'

email_body_template <- readLines(paste0(working_dir, 'nodata_notifier.template'))
delay_table <- fread(paste0(working_dir, 'nodata_notifier.delayed'))
password <- readLines(paste0(working_dir, '.key'))
lastrun.file <- '/tmp/~lastrun.phenoemail'

reminder_interval <- c(3, 5, 10, 20, 30, 60, 90, 120)
today <- as.Date(Sys.Date())


sites_table <- phenos[active & site_type%in%c('I','II') & !grepl(pattern = 'NEON', x = site), 
                      .(site, 
                        site_type,
                        date_last = as.Date(date_last),
                        contact1, 
                        contact2)]

sites_table <- merge(sites_table, delay_table, by = 'site', all.x = TRUE)
sites_table[is.na(normal_delay), normal_delay := 0]
sites_table[, delay := as.integer(today - date_last)]

#excluding Dennis's email
sites_table[grepl(tolower(contact1), pattern = 'baldocchi@berkeley.edu'), contact1 := contact2]
sites_table[grepl(tolower(contact1), pattern = 'berkeley.edu'), contact2 := '']

delay_table <- sites_table[delay > 1]

email_table <- delay_table[(delay- normal_delay) %in% reminder_interval & contact1!='']


send_email <- function(to, subject, body){
  
  send.mail(from = "PhenoCam Network <phenocam.network@gmail.com>",
            to = to,
            subject = subject,
            body = body, 
            replyTo='Bijan Seyednasrollah <bijan.s.nasr@gmail.com>',
            smtp = list(host.name = "smtp.gmail.com", 
                        port = 465,
                        user.name = "phenocam.network@gmail.com",
                        passwd = password,
                        ssl = TRUE
            ),
            authenticate = TRUE,
            send = TRUE)
  
}


#alternative function in case the first one stops working
send_email2 <- function(to, subject, body){
  sender <- "PhenoCam Network <phenocam.netwrok@gmail.com>"
  Server=list(smtpServer='localhost')
  sendmail(sender, to, subject, body, control=Server)
}




# sending emails to the admins
send_email(to = c('bijan.s.nasr@gmail.com','adam.young@nau.edu'),
           body = paste(
             'Email list:\n----\n', paste(capture.output(as.data.frame(email_table[,.(site, date_last, delay, contact1, contact2)])), collapse="\n"),
             '\n\n',
             'Delay list:\n----\n', paste(capture.output(as.data.frame(delay_table[, .(site, date_last, delay, contact1, contact2)])), collapse="\n"), 
             sep = '\n'), 
           subject = paste('PhenCams', as.character(Sys.Date())))




#check the last run to avoid sending more than one email accidentally
if(file.exists(lastrun.file)) lastrun.phenoemail <- readLines(lastrun.file)



# sending emails one by one
n <- nrow(email_table)

if(n!=0 & n<20)for(i in 1:n){
  if(exists('lastrun.phenoemail')){
    if(lastrun.phenoemail!=as.character(Sys.Date()))
    {  
      site <- email_table[i, site]
      delay <- email_table[i, delay]
      
      subject <- paste0('phenocam at ', site, ': no image in ', delay,' days')
      
      to <- email_table[i, contact1]
      if(email_table[i,contact2]!='' & email_table[i,contact1]!=email_table[i,contact2]) to <- c(to, email_table[i, contact2])
      
      email_body <- gsub(email_body_template,
                         pattern = '$SITENAME', replacement = site)
      email_body <- gsub(email_body,
                         pattern = '$DELAY', replacement = delay)
      print(to, subject, email_body)
      send_email(to = to,
                 subject = subject,
                 body = email_body)
    }else{
      print('The script has been run alread today!')
    }  
  }else{
    print('Unknown last run!') 
  }
  
}


# write today's date to the local file
writeLines(as.character(Sys.Date()), lastrun.file)


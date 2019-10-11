library(methods)
library(lubridate, warn.conflicts = F)
library(data.table, warn.conflicts = F)
library(rjson, warn.conflicts = F)
library(rJava, warn.conflicts = F)
library(mailR, warn.conflicts = F)

delayPairs <- t(data.frame(
  bouldinalfalfa = 20,
  bouldincorn = 20,
  coville = 1000,
  eastend = 20,
  eastend2 = 20,
  esalb = 7,
  eslm1 = 7,
  eslm2 = 7,
  eslma = 7,
  exglsnotel = 1000,
  imcrkfen = 7,
  imcrkridge0 = 7,
  imcrkridge1 = 7,
  imcrktussock = 7,
  kelloggcorn = 30,
  kelloggswitchgrass = 7,
  marcell = 7,
  mayberry = 20,
  montebondonegrass = 30,
  montebondonepeat = 30,
  sherman = 20,
  shermanbarn = 20,
  snipelake = 1000,
  siwetland = 20,
  tonzi = 20,
  'torgnon-ld' = 7,
  'torgnon-nd' = 7,
  twitchell = 20,
  twitchellalfalfa = 20,
  twitchellalfalfa2 = 20,
  vaira = 20,
  westpond = 20
))

colnames(delayPairs) <- 'normaldelay'
normalDelay <- as.data.table(delayPairs)
normalDelay$site <- gsub(pattern = '.', replacement = '-',rownames(delayPairs), fixed = T)
#normalDelay

sendEmail <- function(to, subject, body){
  sender <- "PhenoCam Network <bijan.s.nasr@gmail.com>"
  send.mail(from = sender,
            to = to,
            subject = subject,
            body = body, 
            replyTo='Bijan Seyednasrollah <bijan.s.nasr@gmail.com>',
            smtp = list(host.name = "smtp.gmail.com", port = 465,
                        user.name = "phenocam.network@gmail.com",
                        passwd = readLines('.key'),
                        ssl = TRUE
            ),
            authenticate = TRUE,
            send = TRUE)
}


getPhenoTable <- function(){
  
  phenoSites <- fromJSON(file ='https://phenocam.sr.unh.edu/webcam/network/siteinfo/')
  
  ns <- length(phenoSites)
  
  phenoDT <- as.data.frame(matrix(NA, nrow = ns, ncol = 35))
  colnames(phenoDT) <- names(phenoSites[[1]])
  
  for(i in 1:ns)  {
    tmp <- sapply(phenoSites[[i]]  , function(x){if(is.null(x))NA else x})
    phenoDT[i,] <- as.vector(unlist(tmp))
  }
  
  
  phenoDT <- as.data.table(phenoDT)
  phenoDT[, contact1:=gsub(' AT ', '@', contact1)]
  phenoDT[, contact2:=gsub(' AT ', '@', contact2)]
  phenoDT[, contact1:=gsub(' DOT ', '.', contact1, fixed = T)]
  phenoDT[, contact2:=gsub(' DOT ', '.', contact2, fixed = T)]
  
  phenoDT[, active:=active=='TRUE']
  phenoDT[,date_end:=as.Date(date_end)]
  phenoDT[,date_start:=as.Date(date_start)]
  phenoDT$last <- date(Sys.time()) - phenoDT$date_end 
  
  # normalDelay <- as.data.table(read.csv('/home/bijan/bijanScripts/normalDelay.csv')) 
  phenoDT <- merge(phenoDT, normalDelay, by = 'site', all.x = T)
  phenoDT[is.na(normaldelay), normaldelay:=0]
  phenoDT[,delay:= last - normaldelay]
  
  phenoDT
}

reminderInterval <- c(3, 5, 10, 20, 30, 60, 90, 120)

phenoDT <- getPhenoTable()
# phenoDT[grepl(pattern = 'rfbrown@sevilleta.unm.edu', paste(contact1, contact2)), site]

# print('List of sites with delay:')
delayList <- phenoDT[delay>1&active&site_type%in%c('I','II'),.(site, last, contact1, contact2)] #[order(last)]

#email table
emailDT <- phenoDT[(delay%in%reminderInterval|
                      (delay%in%c(2)&site=='luckyhills'))&
                     active&
                     site_type%in%c('I','II'),
                   .(site, last, normaldelay,
                     contact1, contact2, 
                     body = paste0(
                       
                       'Hi,\n\n',
                       
                       '*** This is an automatic email from the PhenoCam data management team. ***\n\n',
                       
                       'The PhenoCam camera at ', site, ' has not uploaded any image in the past ', last,' days. \n',
                       'Please let us know if you are aware of an issue at this site. Ignore this email, if you\n',
                       'have already been investigating the issue or this delay is normal for the site.\n\n',
                       'Site page: ', 'https://phenocam.sr.unh.edu/webcam/sites/', site, '/\n',
                       'Latest image: ', 'https://phenocam.sr.unh.edu/data/latest/', site, '.jpg\n\n',

                       'Please feel free to email us, if you have questions or need troubleshooting assistance \n',
                       'to resolve issues. The automated emails will continue on a schedule (3, 5, 10, 20, 30, 60, 90, \n',
                       'and 120 days beyond the normal delay) until the uploads are resolved. Let us know if you \n',
                       'would like to change the normal delay from its default value.  If you have deactivated the \n',
                       'site and do not expect any further image uploads, please let us know and these messages will \n',
                       'cease.\n\n',
                       
                       'Thank you for your continuous support of the PhenoCam network.\n',
                       '\n\n',
                       
                       'Best,\n',
                       'Bijan\n',
                       '\n',
                       '---\n',
                       'Bijan Seyednasrollah, PhD\n',
                       'PhenoCam Data Scientist\n',
                       'https://bnasr.github.io/\n',
                       'bijan.s.nasr@gmail.com\n',
                       '+1 928-523-1263\n',
                       '\n',
                       '---------------------------------------------------------------------------------\n',
                       'You are receiving this email because your email address has \n',
                       'been listed as the main contact for this site. Let us know if \n',
                       'you would like to change this information.\n',
                       '---------------------------------------------------------------------------------\n'),
                     subject = paste0('phenocam at ', site, ': no image in ', last,' days'))]

emailList <- emailDT[,.(site, last, contact1, contact2)]


con <- textConnection(object = 'myemail', 'w')
writeLines('', con = con)
writeLines('Email list:', con = con)
writeLines('------', con = con)
write.table(emailList, file  = con, row.names = F, col.names = F, quote = F, sep = '\t')
writeLines('', con = con)
writeLines('', con = con)
writeLines('Delay list:', con = con)
writeLines('------', con = con)
write.table(delayList, file  = con, row.names = F, col.names = F, quote = F, sep = '\t')
# writeLines(kable(delayList), con = con)
# writeLines(kable(emailList), con = con)
close.connection(con)

#myemailBody <- ''
#for(i in 1:length(myemail)) myemailBody <- paste(myemailBody, myemail[i], '\n')

myemailBody <- paste(myemail, collapse='\n')

sendEmail(to = c('bijan.s.nasr@gmail.com','adam.young@nau.edu'), body = myemailBody, subject = paste('PhenCams', as.character(Sys.Date())))


lastrun.file <- '/tmp/~lastrun.phenoemail'
if(file.exists(lastrun.file)) lastrun.phenoemail <- readLines(lastrun.file)


n <- nrow(emailDT)

if(n!=0)for(i in 1:n){
  
  to <- emailDT[i,contact1]
  if(to==''){
    next()
  }
  
  #excluding Dennis 
  if(grepl('baldocchi@berkeley.edu', emailDT[i,contact1]))to <- emailDT[i,contact2]
  if(grepl('baldocchi@berkeley.edu', emailDT[i,contact2]))to <- emailDT[i,contact1]

  if(emailDT[i,contact2]!=''&emailDT[i,contact1]!=emailDT[i,contact2]) to <- c(to, emailDT[i,contact2])
  
  if(exists('lastrun.phenoemail')){
    if(lastrun.phenoemail!=as.character(Sys.Date()))
    {  
      sendEmail(to = to,
                subject = emailDT[i,subject],
                body = emailDT[i,body])
    }  
  }else{
    print('Unknown last run!') 
  }
  
  
}

writeLines(as.character(Sys.Date()), lastrun.file)


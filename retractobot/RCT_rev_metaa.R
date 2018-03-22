#=====================#
#                     #
#### RETRACTOBOT   ####
#### RCTs          ####
#### REV & META-AN ####
#                     #
#=====================#

#############
### Setup ###
#############

### Clear Memory ###
rm(list = ls())

### Set Default Timezone ###
Sys.setenv(TZ = "GMT") # Necessary as this is broken on Mac. The bug might have been fixed.

### Load Required Packages ###
suppressPackageStartupMessages(library("survival")) # Survival modelling
suppressPackageStartupMessages(library("lme4")) # ME Modelling
suppressPackageStartupMessages(library("brms")) # Bayesian ME Modelling
suppressPackageStartupMessages(library("dplyr")) # Data management
suppressPackageStartupMessages(library("bit64")) # 64-bit integer data class

### Set Directory Objects ###
paperdata <- "~/Documents/DataLab/Retracto-bot/Data/datav8_2018"
figures <- "~/Documents/Datalab/Retracto-bot/Figures"

### Import Data ###
setwd(paperdata)
#readLines("citation_rates_20180112.tsv", n = 2) # Sample file
col.classes <- c("double", "integer",rep("character",7),"integer",rep("character",3),"double","integer",rep("character",8))
dt <- tbl_df(read.delim("citation_rates_20180112.tsv",
                        na.strings = "",
                        colClasses = col.classes))
print(object.size(dt), units = "MB")


### Drop Useless Crud ###
#any(is.na(dt$citing_scopus_id)) #use to search for missing

dt <- select(dt,  retracted_pmid, retracted_scopus_id, retracted_artdate, retracted_journaldate,  retracted_title, retracted_pub_types, citing_scopus_id, citing_pmid, citing_doi, citing_artdate, citing_journaldate, citing_title, citing_pub_types, notice_pmid, notice_journaldate, notice_artdate)


### Convert Scopus IDs to 64-Bit Integers ###
dt <- mutate_at(dt, vars(contains("scopus")), funs(as.integer64(.)))

### Convert Dates ###
dt <- mutate_at(dt, vars(contains("date")), funs(as.Date(.)))

### Drop Observations with No Dates ###
dt <- filter(dt, !{is.na(retracted_artdate) & is.na(retracted_journaldate)})
dt <- filter(dt, !{is.na(notice_artdate) & is.na(notice_journaldate)})
dt <- filter(dt, !{is.na(citing_artdate) & is.na(citing_journaldate)})

### Unify Date Columns ###
dt <- mutate(dt, retracted_bestdate = ifelse(is.na(retracted_artdate), retracted_journaldate, retracted_artdate))
dt <- mutate(dt, notice_bestdate = ifelse(is.na(notice_artdate), notice_journaldate, notice_artdate))
dt <- mutate(dt, citing_bestdate = ifelse(is.na(citing_artdate), citing_journaldate, citing_artdate))
dt <- select(dt, -matches("artdate|journaldate"))
dt <- mutate_at(dt, vars(contains("date")), funs(as.Date(., origin = "1970-01-01"))) #converts the date number to a human readable date format

### Sanity Checks ###
dt <- filter(dt, notice_bestdate >= retracted_bestdate) # Retraction notice must be after article publication
dt <- filter(dt, citing_bestdate >= retracted_bestdate) # Citation must be after publication
### Sort Dataset ###
#names(dt) <-  gsub("scopus_id|pmid", "id", names(dt))
dt <- select(dt, retracted_id, retracted_pmid, retracted_scopus_id, retracted_bestdate, retracted_pub_types, retracted_title, citing_id, citing_pmid, citing_scopus_id, citing_bestdate, citing_pub_types, citing_title, notice_pmid, notice_bestdate)

dt <- arrange(dt, retracted_id, citing_bestdate) # sorts the rows

### Generate Lags ###
dt <- mutate(dt, ret2cit = as.integer(citing_bestdate - retracted_bestdate))
dt <- mutate(dt, not2cit = as.integer(citing_bestdate - notice_bestdate))
dt <- mutate(dt, not2ret = as.integer(retracted_bestdate - notice_bestdate))
dt <- mutate(dt, not2now = as.integer(as.Date("2018-01-12") - notice_bestdate))

### Variable Indicating Citation of Retracted Paper ###
dt <- mutate(dt, cited_retracted = ifelse(citing_bestdate >= notice_bestdate, 1L, 0L)) #generates new variable
dt <- mutate(dt, cited_retracted = factor(cited_retracted, labels = c("No", "Yes")))   #factorises the variable with the lowest value being the first;  alternatively levels=c(0,1), labels =  c("No", "Yes")


### find all the retracted RCT searching by [pt] and title
foo <- c("(r|R)andomi(s|z)ed (c|C)ontrolled (t|T)rial(s)?", "\\bRCT(s|S)?\\b") # \\b boundary - so that there is nothing adjacent
foo <- paste(foo, collapse = "|")
dt <- mutate(dt, rct = ifelse(grepl(foo, retracted_title), 1L, 0L))
dt <- mutate(dt, rct = ifelse(grepl(foo, retracted_pub_types), 1L, rct)) #if it is not true leave as it is

### find all the citing papers that are systematic reviews
dt <- mutate(dt, sysrev = ifelse(grepl("systematic review(s)?", citing_title, ignore.case = T), 1L, 0L))
dt <- mutate(dt, sysrev = ifelse(grepl("systematic review(s)?", citing_pub_types, ignore.case = T), 1L, sysrev))


### find all the citing papers that are meta-analyses
dt <- mutate(dt, metaa = ifelse(grepl("meta(-| )?analys(e|i)s", citing_title, ignore.case = T), 1L, 0L))
dt <- mutate(dt, metaa = ifelse(grepl("meta(-| )?analys(e|i)s", citing_pub_types, ignore.case = T), 1L, metaa))

# keep only systematic reviews and meta-analyses citing retracted rcts

dt <- filter(dt, rct == 1)
dt <- filter(dt, sysrev == 1 | metaa == 1)

setwd("/Users/kawa/Documents/DataLab/Retracto-bot/ReMeta") 
write.table(dt, "RetractedRCTs.txt", quote=F, sep = "\t", na = "", row.names = F)










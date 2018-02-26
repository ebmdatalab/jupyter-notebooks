#=====================#
#                     #
#### RETRACTOBOT   ####
#### AUTHORS       ####
#### RANDOMISATION ####
#                     #
#=====================#

#############
### Setup ###
#############

### Clear Memory ###
rm(list = ls())

### Set Default Timezone ###
Sys.setenv(TZ = "GMT") # Necessary as this is broken on Mac. The bug might have been fixed.

### Install packages that are already installed
suppressPackageStartupMessages(library("survival")) # Survival modelling
suppressPackageStartupMessages(library("lubridate")) # Function for handling dates.
suppressPackageStartupMessages(library("dplyr")) # Data management
suppressPackageStartupMessages(library("bit64")) # 64-bit integer data class

### Set Directory Objects ###
paperdata <- "~/Documents/DataLab/Retracto-bot/Data/datav8_2018"
authdata <- "~/Documents/DataLab/Retracto-bot/Data/authors_2018"
figures <- "~/Documents/Datalab/Retracto-bot/Figures"

### Import Data ###
setwd(paperdata)
#readLines("citation_rates_20180112.tsv", n = 2) # Sample file
dt <- tbl_df(read.delim("citation_rates_20180112.tsv",
                      na.strings = "",
                      stringsAsFactors = F))
print(object.size(dt), units = "MB")

setwd(authdata)
auth <- tbl_df(read.delim("citing_authors_20180212.tsv", 
                          na.strings = "",
                          stringsAsFactors = F))
print(object.size(auth), units = "MB")

### Drop Useless Crud ###
#any(is.na(dt$citing_scopus_id)) #use to search for missing

auth <- select(auth, scopus_auid, retracted_scopus_id, citing_scopus_id, given_name, surname, email_address)

dt <- select(dt,  retracted_scopus_id, retracted_artdate, retracted_journaldate,  retracted_pub_types, retracted_issn, citing_scopus_id, citing_artdate, citing_journaldate, citing_pub_types, citing_issn, notice_pmid, notice_journaldate, notice_artdate)


### Convert Scopus IDs to 64-Bit Integers ###
dt <- mutate_at(dt, vars(contains("scopus")), funs(as.integer64(.)))
auth <- mutate_at(auth, vars(contains("scopus")), funs(as.integer64(.)))

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
names(dt) <-  gsub("scopus_id|pmid", "id", names(dt))
dt <- select(dt, retracted_id, retracted_bestdate, retracted_pub_types, retracted_issn, citing_id, citing_bestdate, citing_pub_types, citing_issn, notice_id, notice_bestdate)
dt <- arrange(dt, retracted_id, citing_bestdate) # sorts the rows

### Generate Lags ###
dt <- mutate(dt, ret2cit = as.integer(citing_bestdate - retracted_bestdate))
dt <- mutate(dt, not2cit = as.integer(citing_bestdate - notice_bestdate))
dt <- mutate(dt, not2ret = as.integer(retracted_bestdate - notice_bestdate))

# dt.grp <- dt %>%
#   group_by(retracted_id) %>%
#   slice(1) %>%
#   select(retracted_id, retracted_bestdate, notice_id, notice_bestdate) %>%
#   mutate(ret2not = as.integer(notice_bestdate - retracted_bestdate)) %>%
#   ungroup()

### Variable Indicating Citation of Retracted Paper ###
dt <- mutate(dt, cited_retracted = ifelse(citing_bestdate >= notice_bestdate, 1L, 0L)) #generates new variable
dt <- mutate(dt, cited_retracted = factor(cited_retracted, labels = c("No", "Yes")))   #factorises a variable with the lowest value being the first;  alternatively levels=c(0,1), labels =  c("No", "Yes")

# auth <- group_by(auth, scopus_auid)
# auth <- arrange(auth, scopus_auid, email_address)
# auth <- mutate(auth, email_address = first(email_address))
# auth <- filter(auth, complete.cases(email_address))  # we have more than one email address

###================================###
### Poisson model for the analysis ###
###================================###



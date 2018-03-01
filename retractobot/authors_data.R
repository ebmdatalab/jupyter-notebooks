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

### Load Required Packages ###
suppressPackageStartupMessages(library("survival")) # Survival modelling
suppressPackageStartupMessages(library("lme4")) # ME Modelling
suppressPackageStartupMessages(library("brms")) # Bayesian ME Modelling
suppressPackageStartupMessages(library("dplyr")) # Data management
suppressPackageStartupMessages(library("bit64")) # 64-bit integer data class

### Set Directory Objects ###
paperdata <- "~/Documents/DataLab/Retracto-bot/Data/datav8_2018"
authdata <- "~/Documents/DataLab/Retracto-bot/Data/authors_2018"
figures <- "~/Documents/Datalab/Retracto-bot/Figures"

### Import Data ###
setwd(paperdata)
#readLines("citation_rates_20180112.tsv", n = 2) # Sample file
col.classes <- c("double", "integer",rep("character",7),"integer",rep("character",3),"double","integer",rep("character",8))
dt <- tbl_df(read.delim("citation_rates_20180112.tsv",
                        na.strings = "",
                        colClasses = col.classes))
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
dt <- mutate(dt, not2now = as.integer(as.Date("2018-01-12") - notice_bestdate))

### Variable Indicating Citation of Retracted Paper ###
dt <- mutate(dt, cited_retracted = ifelse(citing_bestdate >= notice_bestdate, 1L, 0L)) #generates new variable
dt <- mutate(dt, cited_retracted = factor(cited_retracted, labels = c("No", "Yes")))   #factorises the variable with the lowest value being the first;  alternatively levels=c(0,1), labels =  c("No", "Yes")

#### Merging ###
auth <- rename(auth, citing_id = citing_scopus_id) # rename new = old in dplyr
auth <- select(auth, -retracted_scopus_id, -given_name, -surname) # drop these variables
auth <- left_join(dt, auth, by = "citing_id") # only rows present in the left dataset; here: "dt"

auth <- arrange(auth, scopus_auid, desc(citing_bestdate)) # sorting by scopus_auid and then by descending values
auth <- auth %>% 
  group_by(scopus_auid) %>%
  mutate(email_address = email_address[which(!is.na(email_address))[1]]) %>% # create&overrate with first non-missing missing email within a group.
  ungroup()
auth <- filter(auth, complete.cases(email_address)) # Only scopus author IDs with email addresses.

### Create Randomisation Sequence ###
indices <- distinct(auth, retracted_id)
indices <- select(indices, retracted_id)
set.seed(42) #randomisation seed
indices_int <- sample_frac(indices, 0.5) # all the studies in the intervention group
indices_comp <- setdiff(indices, indices_int) # all the studies in the control group
indices_int <- mutate(indices_int, intervention = 1L)
indices_comp <- mutate(indices_comp, intervention = 0L)
indices <- bind_rows(indices_int, indices_comp)
rm(indices_int, indices_comp)

auth <- left_join(auth, indices, by = "retracted_id")
rm(indices)

###================================###
### Poisson model for the analysis ###
###================================###

### Data Binning for Count Models ###
dt <- select(dt, retracted_id, retracted_bestdate, citing_id, ret2cit, not2cit, not2ret, not2now, cited_retracted)
dt <- mutate(dt, year_bin = ifelse(not2cit > 0, ceiling(not2cit/365.25), NA))
dt <- mutate(dt, year_bin = ifelse(not2cit == 0, 1, year_bin)) # if TRUE set to 1 ; otherwise leave as it is
dt <- mutate(dt, year_bin = ifelse(not2cit < 0, floor(not2cit/365.25), year_bin))

dt <- mutate(dt, fup = ifelse(year_bin < 0, pmin(abs(fup - not2ret), 365.25), NA))
dt <- mutate(dt, fup = ifelse(year_bin > 0, pmin(abs(not2now - fup), 365.25), fup))

dt <- dt %>% 
  group_by(year_bin, retracted_id) %>% # for each study within one year 
  summarise(count = n(), # count number of rows within group
            fup = first(fup), #use the value from the first row
            cited_retracted = first(cited_retracted),
            retracted_bestdate = first(retracted_bestdate)) %>%
  ungroup()
dt <- filter(dt, fup != 0) # keep if not 0

### Rescale Variables ###
dt <- mutate(dt, retracted_bestdate = scale(retracted_bestdate)) # scale demeans&divides by SD = Z transform

### Poisson Model ###
pois.fit <- glmer(count ~ cited_retracted + retracted_bestdate + (1 | retracted_id),
                  offset = log(fup),
                  family = poisson(link = "log"),
                  control = glmerControl(optimizer = "bobyqa"),
                  verbose = 2L,
                  data = dt)
summary(pois.fit)
confint(pois.fit, method = "Wald")

exp(fixef(pois.fit))


### Negative Binomial Model ###
nb.fit <- glmer.nb(count ~ cited_retracted + retracted_bestdate + (1 | retracted_id),
                   offset = log(fup),
                   verbose = 2L,
                   control = glmerControl(optimizer = "bobyqa"),
                   data = dt)
summary(nb.fit)
confint(nb.fit, method = "Wald")


### Bayesian Model ### - Not working
brm.fit <- brm(count ~ offset(log(fup)) + cited_retracted + retracted_bestdate + (1 | retracted_id),
               family = poisson(),
               chains = 4L,
               cores = 4L,
               data = dt)

## we will use rate base modelling (Poisson/quasi-Poisson/negative binomials/survial models/time to first citation)

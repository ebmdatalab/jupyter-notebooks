cd "C:\Users\ajwalker\Documents\GitHub\jupyter-notebooks\Statins_paper\regression"
import delimited "regression_file.csv",clear

gen prophighdose = proportion_lm_dose_hp/100
*gen add = ruc11cd + " " + ruc11

summ,d
*misstable summ,all

xtile qof = total, nq(5)
xtile imd = value_imd, nq(5)
xtile list_size_q = list_size, nq(5)
xtile over_65 = value_over_65,nq(5)
xtile long_term_health = value_long_term_health,nq(5)
encode ruc11cd, gen(rural_urban_code)

tabstat value_over_65,by(over_65) s(min max)
tabstat value_long_term_health,by(long_term_health) s(min max)
tabstat list_size,by(list_size_q) s(min max)
tabstat total,by(qof) s(min max)

gen prop_logit =  logit(prophighdose)
replace prop_logit = log((prophighdose+(0.5/items)) / (1 - prophighdose+(0.5/items))) if prop_logit==.


foreach indepvar in over_65 long_term_health list_size_q rural_urban_code imd qof {
	tabstat prophighdose,by(`indepvar') s(median)
	regress prop_logit i.`indepvar'
}

mixed prop_logit i.over_65 i.long_term_health i.list_size_q i.rural_urban_code i.imd i.qof || pct:

predict predictions
qui corr prop_logit predictions
di "R-squared - fixed effects (%): " round(r(rho)^2*100,.1)

qui predict predictionsr, reffects
qui corr prop_logit predictionsr
di "R-squared - random effects (%): " round(r(rho)^2*100,.1)

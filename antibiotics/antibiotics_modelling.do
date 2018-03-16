cd "C:\Users\ajwalker\Documents\GitHub\jupyter-notebooks\antibiotics"
import delimited "antibiotics_for_analysis.csv",clear


misstable summ,all

xtile qof = total, nq(5)
xtile imd = value_imd, nq(5)
xtile composite_score = mean_percentile, nq(5)
recode num_gps min/1=1 2/max=0 .=0, gen(single_handed)
recode rural_urban_code 1=6 2=5 3=4 4=3 5=2 6=1,gen(rural_urban)
xtile over_65 = value_over_65,nq(5)
xtile under_18 = value_under_18,nq(5)
xtile long_term_health = value_long_term_health,nq(5)

tabstat value_over_65,by(over_65) s(min max)
tabstat value_under_18,by(under_18) s(min max)
tabstat value_long_term_health,by(long_term_health) s(min max)
tabstat total,by(qof) s(min max)


foreach indepvar in over_65 under_18 long_term_health single_handed rural_urban imd qof composite_score {
	tabstat rate,by(`indepvar') s(median)
	regress rate i.`indepvar'
}

mixed rate i.over_65 i.under_18 i.long_term_health i.single_handed i.rural_urban i.imd i.qof i.composite_score || pct:

predict predictions
qui corr rate predictions
di "R-squared - fixed effects (%): " round(r(rho)^2*100,.1)

qui predict predictionsr, reffects
qui corr rate predictionsr
di "R-squared - random effects (%): " round(r(rho)^2*100,.1)

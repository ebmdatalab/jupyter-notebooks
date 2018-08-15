# Errors in ADQ spreadsheet

## Wrong ADQ units for 20 different presentations of ibuprofen suspension
All ADQs for `1001010J0....BH` should be 1200mg/day, e.g.
1001010J0DFACBH,Galpharm_IbuprofenForChildSusp100mg/5ml,1200,ML


## There are two liquids whose SQU is grammes (rather than ml or units)
The ADQs are in mg but the product is 15mg/5ml or 0.003g / ml and the SQU is in g and the unit of measure is spponful.

It appears that a 5ml spoonful is one ADQ, but if quantity is in grams then we'd be seeing quantities of less than 1 (which never happens). It has been prescribed twice ever (2010 and 2012) in quantities of 100. We can therefore assume that the ADQ is wrong in this case, and it should be ML.
0106020M0BBAAAD,Senokot_Gran,15,MG


The same goes for this, which is a liquid supposedly measured in grammes:
0411000G0BBABAB,Ebixa_Oral Soln 5mg/0.5ml Pump Actuation,20,MG

## There are 4 liquids whose SQU is units (rather than ml)

0205051F0BCAFCT
040801050AACECE
0411000E0AAAHAH
0503010ACBBAFAF


## There are several where DMD has no form size
* Topiramate 100mg/5ml oral suspension

## Some patches just don't make sense

All the patches where the ADQ is supplied as grammes appear to have it
supplied as "3 patches" in the NHS Digital data.  Examples:

```
BNF_Code	BNF_Description	adq_value	Items	Quantity	ADQ_Usage	computed_adq	their_adq_per_quantity	our_adq_per_quantity
0407020B0AAAEAE	Buprenorphine_Patch 35mcg/hr (96hr)	0.00112	1	7	21.0	5.250000	3.0	0.750000
0407020B0BDABAF	Transtec_T/Derm Patch 52.5mcg/hr (30mg)	0.00168	1	8	24.0	6.000000	3.0	0.750000
0407020B0BKABAI	Reletrans_Transdermal Patch 10mcg/hr	0.00056	11	4	132.0	18.857143	3.0	0.428571
0407020B0AAAGAG	Buprenorphine_Patch 70mcg/hr (96hr)	0.00224	1	4	12.0	3.000000	3.0	0.750000
0407020B0BEABAI	BuTrans_Transdermal Patch 10mcg/hr	0.00056	4	8	96.0	13.714286	3.0	0.428571
0407020B0BEACAJ	BuTrans_Transdermal Patch 20mcg/hr	0.00112	4	8	96.0	13.714286	3.0	0.428571
0407020B0BMAAAH	Sevodyne_Transdermal Patch 5mcg/hr	0.00028	1	4	12.0	1.714286	3.0	0.428571
0407020B0AAAFAF	Buprenorphine_Patch 52.5mcg/hr (96hr)	0.00168	1	8	24.0	6.000000	3.0	0.750000
0407020B0AAAIAI	Buprenorphine_Patch 10mcg/hr (7day)	0.00056	1	16	48.0	6.857143	3.0	0.428571
0407020B0BGACAG	Hapoctasin_Patch 70mcg/hr	0.00224	1	8	24.0	6.000000	3.0	0.750000

```

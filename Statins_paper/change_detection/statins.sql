WITH p AS (
SELECT pct, practice, chemical, bnf_code, bnf_name, SUM(items) AS items, SUM(actual_cost) AS actual_cost, SUM(quantity) AS quantity, CAST(month AS DATE) AS month 
FROM `ebmdatalab.hscic.normalised_prescribing_standard` p

LEFT JOIN `hscic.bnf` b ON p.bnf_code = b.presentation_code

WHERE SUBSTR(bnf_code,1,9) IN (
    '0212000AA', --Rosuvastatin Calcium 
    '0212000AC', --Simvastatin & Ezetimibe
    '0212000B0', --Atorvastatin
    '0212000C0', --Cerivastatin 
    '0212000M0', --Fluvastatin Sodium
    '0212000X0', --Pravastatin Sodium 
    '0212000Y0') --Simvastatin

GROUP BY 
 pct, practice, chemical, bnf_code, bnf_name, month
 
ORDER BY
month, bnf_code)

SELECT practice AS code, SUM(items) AS denominator, CAST(month AS DATE) AS month, SUM(CASE WHEN concat(SUBSTR(bnf_code,1,9),SUBSTR(bnf_code,-2,2)) NOT IN (
    '0212000AAAA', --Rosuvastatin Calc_Tab 10mg (brand, generic) 
    '0212000AAAB', --Rosuvastatin Calc_Tab 20mg (brand, generic) 
    '0212000AAAC', --Rosuvastatin Calc_Tab 40mg (brand, generic) 
    '0212000B0AB', --Atorvastatin_Tab 20mg (brand, generic)
    '0212000B0AC', --Atorvastatin_Tab 40mg (brand, generic) 
    '0212000B0AD', --Atorvastatin_Tab 80mg (brand, generic)
    '0212000B0AN', --Atorvastatin_Tab 30mg (brand, generic)
    '0212000B0AP', --Atorvastatin_Tab 60mg (brand, generic)
    '0212000Y0AH') --Simvastatin_Tab 80mg (brand, generic)
    THEN items ELSE 0 END) AS numerator

FROM p

INNER JOIN
  ebmdatalab.hscic.practices prac
ON
  practice = prac.code
  AND setting = 4
  AND status_code = 'A'
                                                                                                       
WHERE SUBSTR(bnf_code,1,9) IN (
    '0212000AA', --Rosuvastatin Calcium 
    '0212000AC', --Simvastatin & Ezetimibe
    '0212000B0', --Atorvastatin
    '0212000C0', --Cerivastatin 
    '0212000M0', --Fluvastatin Sodium
    '0212000X0', --Pravastatin Sodium 
    '0212000Y0') --Simvastatin

GROUP BY 
 practice, month
 
ORDER BY
month
# ---
# jupyter:
#   jupytext_format_version: '1.2'
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
#   language_info:
#     codemirror_mode:
#       name: ipython
#       version: 3
#     file_extension: .py
#     mimetype: text/x-python
#     name: python
#     nbconvert_exporter: python
#     pygments_lexer: ipython3
#     version: 3.6.5
# ---

import pandas as pd

# +
ghost_df = pd.read_gbq("""
SELECT
  prac.ccg_id,
  rx.practice_code,
  rx.bnf_code,
  rx.bnf_description,
  rx.items,
  rx.quantity,
  rx.nic,
  dt.concession,
  dt.quantity as dt_quantity,
  dt.price_pence,

  SUM(rx.items*rx.quantity) AS QI,
  ROUND(IEEE_DIVIDE(rx.NIC,(rx.items*rx.quantity)),4) AS rx_ppu,
  ROUND(CASE
      WHEN dt.concession IS NOT NULL THEN IEEE_DIVIDE((dt.concession/100),dt.quantity)
      ELSE IEEE_DIVIDE((dt.price_pence/100),dt.quantity) END,4) AS dt_ppu,
  rx.quantity*rx.items*(ROUND(IEEE_DIVIDE(rx.NIC,(rx.items*rx.quantity)),4)- ROUND(CASE
        WHEN dt.concession IS NOT NULL THEN IEEE_DIVIDE((dt.concession/100),dt.quantity)
        ELSE IEEE_DIVIDE((dt.price_pence/100),dt.quantity) END,4)) AS excess_cost
FROM
  richard.prescribing_2018_09_full AS rx
JOIN
  dmd.dt_viewer AS dt
ON
  rx.bnf_code=dt.bnf_code
  join 
  hscic.practices as prac
  on
  rx.practice_code=prac.code  
WHERE
  (rx.bnf_description LIKE '%_Tab%'
    OR rx.bnf_description LIKE '%_Cap%')
  AND dt.date='2018-09-01' AND rx.bnf_code not like '0410020C0%AC'
GROUP BY
  prac.ccg_id,
  rx.practice_code,
  rx.bnf_code,
  rx.bnf_description,
  rx.quantity,
  rx.items,
  rx_ppu,
  dt_ppu,
  dt.concession,
  dt.quantity,
  dt.price_pence,
  rx.NIC
HAVING
  rx_ppu <> dt_ppu
  order by excess_cost desc
""", projectid, dialect='standard')
 
ghost_df.to_csv("Ghost Branded Generics.csv")
# -

gpd_ghost_df = ghost_df.groupby('ccg_id')['excess_cost'].sum().reset_index().sort_values('excess_cost',ascending=False)

gpd_ghost_df.head(20)

gpd_ghost_df.sum()

ghost_df.head()

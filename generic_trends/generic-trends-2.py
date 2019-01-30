# ---
# jupyter:
#   jupytext_format_version: '1.2'
#   kernelspec:
#     display_name: Python (jupyter virtualenv)
#     language: python
#     name: jupyter
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

# + {"scrolled": false}
import pandas as pd
filename = 'generic_ratios_by_chemical_4.csv'
try:
    df = pd.read_csv(filename)
except IOError:
    sql = """WITH
      num AS (
      SELECT
        month,
        SUBSTR(bnf_code, 0, 9) AS product,
        SUM(items) AS items
      FROM
        `ebmdatalab.hscic.normalised_prescribing_standard`
      WHERE
        bnf_code LIKE '_________AA%'
      GROUP BY
        month,
        product),
      denom AS (
      SELECT
        month,
        SUBSTR(bnf_code, 0, 9) AS product,
        SUM(items) AS items
      FROM
        `ebmdatalab.hscic.normalised_prescribing_standard`
      GROUP BY
        month,
        product),
      data AS (
      SELECT
        num.month,
        num.product,
        num.items / denom.items AS value,
        denom.items AS items
      FROM
        num
      INNER JOIN
        denom
      ON
        num.month = denom.month
        AND num.product = denom.product ),
      data_with_stats AS (
      SELECT
        DISTINCT month,
        product,
        value,
        data.items AS total_items,
        LAST_VALUE(value) OVER (PARTITION BY product ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) - FIRST_VALUE(value) OVER (PARTITION BY product ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS delta,
        ABS(PERCENTILE_CONT(value,
            0.75) OVER (PARTITION BY product) - PERCENTILE_CONT(value,
            0.25) OVER (PARTITION BY product)) AS iqr
      FROM
        data )
    SELECT
      bnf.chemical AS product_name,
      data_with_stats.*
    FROM
      data_with_stats
    INNER JOIN 
      (SELECT DISTINCT chemical, chemical_code FROM `ebmdatalab.hscic.bnf`) bnf 
    ON
      bnf.chemical_code = data_with_stats.product
      """
    df = pd.read_gbq(sql, 'ebmdatalab', verbose=False, dialect='standard')
    df.to_csv(filename)
# -

sql = """WITH
  num AS (
  SELECT
    month,
    SUM(items) AS items,
    SUM(actual_cost) AS actual_cost
  FROM
    `ebmdatalab.hscic.normalised_prescribing_standard`
  WHERE
    bnf_code LIKE '_________AA%'
  GROUP BY
    month),
  denom AS (
  SELECT
    month,
    SUM(items) AS items,
    SUM(actual_cost) AS actual_cost
  FROM
    `ebmdatalab.hscic.normalised_prescribing_standard`
  --WHERE
  --  bnf_code LIKE '0%'
  GROUP BY
    month)
SELECT
  num.month,
  num.items / denom.items AS items_percent,
  num.actual_cost / denom.actual_cost AS act_cost_percent
FROM
  num
INNER JOIN
  denom
ON
  num.month = denom.month"""
top_df = pd.read_gbq(sql, 'ebmdatalab', verbose=False, dialect='standard')

# # Overall generic prescribing
#
# The following chart shows that the proportion of prescriptions made generically has not dropped over the last 8 years; the proportion of spending which has been prescribed generically has dropped a lot more.
#
#

top_df = top_df.sort_values('month')
top_df.set_index('month').plot.line(title="Proportions of generic versus all prescribing")

# # Which are the chemicals showing the greatest positive and negative changes?

most_variance = df.groupby('product').min().reset_index()
most_variance = most_variance[most_variance.total_items > 10000].sort_values('iqr', ascending=False).head(50)

most_variance

# # Chemicals being prescribed more and more as generics

# + {"scrolled": false}
# %matplotlib inline
for product in most_variance[most_variance['delta'] > 0]['product']:
    df[df['product'] == product].groupby(['month', 'product_name']).sum().value.unstack().plot.line()

# -

# # Chemicals being prescribed less and less as generics
#

# + {"scrolled": false}
# %matplotlib inline
for product in most_variance[most_variance['delta'] < 0]['product']:
    df[df['product'] == product].groupby(['month', 'product_name']).sum().value.unstack().plot.line()


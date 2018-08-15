"""
Standard Quantity Unit:
This code indicates the form of the drug and the units in which quantity is measured:
 Code 1  - a unit (e.g. one tablet, capsule, pack, aerosol etc)
 Code 3  - millilitres
 Code 6  - grammes
 Code 0  - individually formulated (unit varies)
"""

import requests
from lxml import html
import pandas as pd
import json

session = requests.Session()
host = "https://www.nhsbsa.nhs.uk"
index_url = (host + "/prescription-data/"
             "dispensing-data/prescription-cost-analysis-pca-data")


SQU_LOOKUP = {
    1: 'unit',
    3: 'ml',
    6: 'g',
    0: 'individual'  # (entirely?) homeopathic remedies
}


def build_url_list(index):
    urls = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
    for month in months:
        urls.extend(index.xpath(
            "//a[starts-with(text(),'{}') "
            "and contains(@href, 'xls')]/@href".format(month))
        )
    return urls


def create_csv():
    with open('scrape-history.json', '+') as history:
        visited = json.load(history)
        bnf_codes_with_squ = set()
        index = html.fromstring(requests.get(index_url).content)
        APPLIANCE_CLASS = 4
        last_length = 0
        for url in build_url_list(index):
            if not url.startswith('http'):
                url = host + url
            if url in visited:
                print("Skipping {}".format(url))
                continue
            df = pd.read_excel(url, skiprows=[0])
            visited[url] = True
            squs = set(df[df['Preparation Class'] != APPLIANCE_CLASS].groupby(
                ['BNF Code', 'Standard Quantity Unit']).groups.keys())
            bnf_codes_with_squ.update(squs)
            print("Added {} items".format(
                len(bnf_codes_with_squ) - last_length))
            last_length = len(bnf_codes_with_squ)
        df = pd.DataFrame(
            list(bnf_codes_with_squ),
            columns=['bnf_code', 'squ']).set_index('bnf_code')
        df.squ = df.squ.apply(lambda squ: SQU_LOOKUP[squ])
        df.to_csv("squs.csv")
        json.dump(visited, history)


if __name__ == '__main__':
    create_csv()

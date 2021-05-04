import re

import pandas as pd
import numpy as np
import datetime

from portfolio.lib.degiro_api import DegiroAPI


# Todo all of these functions seem pretty crummy. Maybe structure them in a Wrapper class around the Degiro API ?
#  also just make sure they actually make any sense

def generate_portfolio_data():
    D = DegiroAPI()
    D.login(with2fa=False)
    pfs = D.get_portfolio_summary()
    portfolio = D.get_portfolio()
    total = pfs['equity']

    symbols = [x['symbol'] for x in portfolio['PRODUCT'].values()]
    name = [x['name'] for x in portfolio['PRODUCT'].values()]
    size = [int(x['size']) for x in portfolio['PRODUCT'].values()]
    price = [np.round(x['price'], 2) for x in portfolio['PRODUCT'].values()]
    subtot = [np.round(x['size'] * x['price'], 2) for x in portfolio['PRODUCT'].values()]
    alloc = [np.round(x / total, 4) for x in subtot]

    df = pd.DataFrame([name, size, price, subtot, alloc]).T
    df.index = symbols
    df.columns = ['Name', 'Size', 'Price', 'Subtotal', 'Allocation']

    return df


def get_info_by_productId(product_ids: list):
    """Return list product info by productId. Input should be a list without dublicates!"""
    D = DegiroAPI()
    D.login(with2fa=False)
    D.get_config()

    chunks = [product_ids[i * 10:(i + 1) * 10] for i in range((len(product_ids) + 9) // 10)]

    data_out = []

    for chunk in chunks:
        data_out.append(D.get_product_by_id(chunk))

    return data_out


def get_cashflows(start_dt: datetime.date):
    D = DegiroAPI()
    D.login(with2fa=False)
    D.get_config()
    data = D.get_account_movements(from_date=start_dt.strftime(format="%d/%m/%Y"),
                                   to_date=datetime.date.today().strftime(format="%d/%m/%Y"))

    df = pd.DataFrame(data)
    df = df.loc[df.type == 'TRANSACTION'].sort_values("date")
    df.date = df.date.apply(lambda x: x.date)
    df = df[['date', 'change']].groupby('date').sum()
    df = df.reset_index()
    df.change = -df.change
    df.columns = ['date', 'cashflow']

    return df


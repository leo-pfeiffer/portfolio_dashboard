import pandas as pd
import numpy as np
import datetime
from .api.degiro import Degiro


def generate_portfolio_data():
    D = Degiro()
    D.login(with2fa=False, conf_path=True)
    pfs = D.getPortfolioSummary()
    portfolio = D.getPortfolio()
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


def get_transactions(date: datetime.date):
    # date should be last date for which previous transactions are available
    D = Degiro()
    D.login(with2fa=False, conf_path=True)
    D.getConfig()
    date_as_string = date.strftime(fmt='%d/%m/%Y')
    today = datetime.date.today().strftime(format="%d/%m/%Y")
    transactions = D.getTransactions(fromDate=date_as_string, toDate=today)
    product_ids = [x['productId'] for x in transactions]
    return product_ids


def get_info_by_productId(product_ids: list):
    D = Degiro()
    D.login(with2fa=False, conf_path=True)
    D.getConfig()

    chunks = [product_ids[i * 10:(i + 1) * 10] for i in range((len(product_ids) + 9) // 10)]

    data_out = []

    for chunk in chunks:
        data_out.append(D.getProductByIds(chunk))

    return data_out

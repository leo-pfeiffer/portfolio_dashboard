import pandas as pd
import numpy as np
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



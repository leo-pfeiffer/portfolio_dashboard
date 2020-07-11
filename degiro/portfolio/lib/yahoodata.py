import yfinance as yf
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta


def get_yahoo_data(tickers: list, start: datetime.date, end: datetime.date):
    start = start.strftime(format="%Y-%m-%d")
    end = end.strftime(format="%Y-%m-%d")

    tickers = [t.lower() for t in tickers]
    prices = yf.download(tickers=tickers, start=start, end=end).loc[:, 'Adj Close']
    prices.index = [x.date() for x in prices.index.to_list()]
    # todo: the following line is very slow.. maybe use other package/source
    # currencies = {ticker: yf.Ticker(ticker).info['currency'] for ticker in tickers}
    currencies = []
    return {'prices': prices, 'currencies': currencies}


def last_data_at_date(tickers: list, date: datetime.datetime.date):
    # todo: either write all data for all srocks to database or get time window and forwardfill
    pass


def ffill_yahoo_data(df: pd.DataFrame) -> pd.DataFrame:
    start = df.index[0]
    end = df.index[-1]

    daterange = [start + relativedelta(days=i) for i in range((end - start).days + 1)]
    new = pd.DataFrame(index=daterange)

    return pd.merge(new, df, left_index=True, right_index=True, how='left').ffill()


if __name__ == '__main__':
    get_yahoo_data(['msft', 'amzn', 'tsla'], start="2020-01-10", end="2020-01-25")
    int(0)

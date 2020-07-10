import yfinance as yf
import datetime


def get_yahoo_data(tickers: list, start: str, end: str):
    tickers = [t.lower() for t in tickers]
    prices = yf.download(tickers=tickers, start=start, end=end).loc[:, 'Adj Close']
    # todo: the following line is very slow.. maybe use other package/source
    currencies = {ticker: yf.Ticker(ticker).info['currency'] for ticker in tickers}
    return {'prices': prices, 'currencies': currencies}


def last_data_at_date(tickers: list, date: datetime.datetime.date):
    # todo: either write all data for all srocks to database or get time window and forwardfill
    pass



if __name__=='__main__':
    int(0)
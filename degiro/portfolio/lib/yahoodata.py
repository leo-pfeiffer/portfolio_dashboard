import yfinance as yf


def get_yahoo_data(tickers: list, start: str, end: str):
    tickers = [t.lower() for t in tickers]
    prices = yf.download(tickers=tickers, start=start, end=end).loc[:, 'Adj Close']
    # todo: the following line is very slow.. maybe use other package/source
    currencies = {ticker: yf.Ticker(ticker).info['currency'] for ticker in tickers}
    return {'prices': prices, 'currencies': currencies}

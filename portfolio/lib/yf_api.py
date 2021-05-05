from typing import Union

import yfinance as yf
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta


class YF:

    @staticmethod
    def _get_date_string(date: Union[str, datetime.datetime, datetime.date]):
        """
        Helper method that creates an appropriately formatted date string for the yfinance API.
        :param date: Date to format
        """
        if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
            return date.strftime(format="%Y-%m-%d")
        elif isinstance(date, str):
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
                return date
            except ValueError as ve:
                raise ve

    @staticmethod
    def get_prices(tickers: list, start: Union[str, datetime.datetime, datetime.date],
                   end: Union[str, datetime.datetime, datetime.date]) -> pd.DatetimeIndex:
        """
        Get prices for a list of tickers in a time range.
        :param tickers: tickers to get
        :param start: start date
        :param end: end date
        :returns: prices of the tickers in the time range
        """
        start = YF._get_date_string(start)
        end = YF._get_date_string(end)

        tickers = [t.lower() for t in tickers]
        prices = yf.download(tickers=tickers, start=start, end=end, progress=False).loc[:, 'Adj Close']
        prices.index = [x.date() for x in prices.index.to_list()]

        # Handle format when only one ticker is fetched
        if len(tickers) == 1:
            prices.name = tickers[0].upper()

        return prices

    @staticmethod
    def ffill_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Forward fill price data to deal with non business days and other gaps.
        """
        start = df.index[0]
        end = df.index[-1]

        date_range = [start + relativedelta(days=i) for i in range((end - start).days + 1)]
        new = pd.DataFrame(index=date_range)

        return pd.merge(new, df, left_index=True, right_index=True, how='left').ffill()


if __name__ == '__main__':
    YF.get_prices(['msft', 'amzn', 'tsla'], start="2020-01-10", end="2020-01-25")
    int(0)

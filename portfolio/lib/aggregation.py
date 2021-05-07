# Aggregate loaded data
import pandas as pd
from pandas.tseries.offsets import BDay
from django.db.models import F
import datetime

from portfolio.lib.utils import date_range_gen
from portfolio.models import Cashflow, Depot, Asset


def create_cumulative_cashflow() -> pd.Series:
    """
    Create a time series with the cumulative cashflows.
    :return: DataFrame containing the cumulative cashflows per date
    """

    # get cashflows from database
    cashflows = list(Cashflow.objects.values('date', 'cashflow').order_by('date'))

    # no cashflows
    if not len(cashflows):
        return pd.Series()

    # create data frames
    cashflows_frame = pd.DataFrame.from_records(cashflows, index='date')
    cum_sum_frame = pd.DataFrame(index=date_range_gen(cashflows[0]['date'], cashflows[-1]['date']))

    # merge to create full data frame across entire date range
    cum_sum_frame = pd.merge(cum_sum_frame, cashflows_frame, how='left', left_index=True, right_index=True)

    # aggregate
    cum_sum_frame = cum_sum_frame.cumsum()
    cum_sum_frame.ffill(inplace=True)

    return cum_sum_frame['cashflow']


def create_value_series() -> pd.Series:
    """
    Create a data frame containing the portfolio value over time.
    :return: Dataframe containing the value.
    """

    # get depot value per date
    value_per_date = list(Depot.objects.value_per_date())

    # no depot entries
    if not len(value_per_date):
        return pd.Series()

    # create data frames
    value_frame = pd.DataFrame.from_records(value_per_date, index='date')

    # forward fill entire data range to even out any gaps
    filled_frame = pd.DataFrame(index=date_range_gen(value_per_date[0]['date'], value_per_date[-1]['date']))
    filled_frame = pd.merge(filled_frame, value_frame, how='left', left_index=True, right_index=True)

    filled_frame.ffill(inplace=True)

    # return as series
    return filled_frame['total']


def create_performance_series() -> pd.Series:
    """
    Create a data frame containing the indexed portfolio performance over time.
    :return: Dataframe containing the performance.
    """

    # todo: cash position is neglected -> basically considered as loss -> FIX!
    # todo: on last days, performance blows up. The reason seems to be that that some entries in the Depot database are
    #  duplicated for that time.. I suspect the reason is in the ETL process somewhere where I messed up the date and
    #  accidentally reload some of the data.

    cum_cashflow = create_cumulative_cashflow()
    portfolio_value = create_value_series()

    # no entries yet
    if cum_cashflow.empty or portfolio_value.empty:
        return pd.Series()

    # merge frames and forward fill any gaps
    performance = pd.merge(portfolio_value, cum_cashflow, how='left', left_index=True, right_index=True).ffill()

    # calculate performance
    performance['return'] = performance['total'] / performance['cashflow']

    return performance['return']


def create_portfolio() -> pd.DataFrame:
    """
    Create data frame of current allocation.
    """
    previous_business_day = (datetime.date.today() - BDay(1)).date()
    portfolio = list(Depot.objects.get_portfolio_at_date(previous_business_day)\
        .annotate(
            symbol=F('symbol_date__symbol'),
            price=F('symbol_date__price__price'),
            size=F('pieces'),
            subtotal=F('pieces') * F('symbol_date__price__price'),
        ).values('symbol', 'size', 'price', 'subtotal'))

    # no portfolio existsL
    if len(portfolio) == 0:
        return pd.DataFrame()

    portfolio_frame = pd.DataFrame(portfolio)

    total_value = portfolio_frame.subtotal.sum()

    portfolio_frame['allocation'] = portfolio_frame['subtotal'] / total_value

    # add product information
    product_info = list(Asset.objects.filter(symbol__in=portfolio_frame.symbol.values)
                        .values('isin', 'name', 'symbol').distinct())

    portfolio_frame = pd.merge(portfolio_frame, pd.DataFrame(product_info), on='symbol', how='left').round(2)

    return portfolio_frame


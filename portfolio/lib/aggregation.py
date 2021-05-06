# Aggregate loaded data
import pandas as pd

from portfolio.lib.utils import date_range_gen
from portfolio.models import Cashflow, Depot


def create_cumulative_cashflow() -> pd.Series:
    """
    Create a time series with the cumulative cashflows.
    :return: DataFrame containing the cumulative cashflows per date
    """

    # get cashflows from database
    cashflows = list(Cashflow.objects.values('date', 'cashflow').order_by('date'))

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

    cum_cashflow = create_cumulative_cashflow()
    portfolio_value = create_value_series()

    # merge frames and forward fill any gaps
    performance = pd.merge(portfolio_value, cum_cashflow, how='left', left_index=True, right_index=True).ffill()

    # calculate performance
    performance['return'] = performance['total'] / performance['cashflow']

    return performance['return']

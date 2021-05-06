import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import F

from portfolio.lib.utils import date_range_gen
from portfolio.models import Depot, Cashflow


# todo ==== all the following stuff definitely needs to be structured better

def create_performance_time_series():
    """Create a dataframe containing the returns time series up to timestamp"""
    # calculate portfolio
    # included_positions = Depot.objects.filter(~Q(price__exact=0))
    included_positions = Depot.objects.all()
    portfolio_df = pd.DataFrame(list(included_positions.values()))
    portfolio_df['total'] = portfolio_df.pieces * portfolio_df.price

    portfolio_df = portfolio_df[portfolio_df.symbol != 'BITCOIN XBTE']

    null_prices = portfolio_df[portfolio_df.price == 0]
    if not null_prices.empty:
        first_zero_date = null_prices.sort_values('date').date.iloc[0]
        portfolio_df = portfolio_df[portfolio_df.date < first_zero_date]

    latest_date = portfolio_df.sort_values('date').iloc[-1].values[3]
    end_date = datetime.date.today() - relativedelta(days=1)
    ffill_dates = [*date_range_gen(latest_date + relativedelta(days=1), end_date)]

    saved_depot = portfolio_df[portfolio_df.date == latest_date].loc[:, ['id', 'symbol', 'pieces']]

    prices = Prices.objects.filter(date__in=[*ffill_dates]).all()
    prices_df = pd.DataFrame(list(prices.values()))
    prices_df = prices_df.loc[:, ['symbol', 'date', 'price']]

    for date in ffill_dates:
        depot_on_date = saved_depot.copy()
        depot_on_date['date'] = date
        depot_on_date = pd.merge(depot_on_date, prices_df, on=['symbol', 'date'])
        depot_on_date['total'] = depot_on_date.pieces * depot_on_date.price
        portfolio_df = portfolio_df.append(depot_on_date).reset_index(drop=True)

    performance_df = portfolio_df[['date', 'total']].groupby("date").sum()

    cashflow_df = pd.DataFrame(list(Cashflows.objects.all().values()))

    merged = pd.merge(performance_df, cashflow_df.loc[:, ['date', 'cumsum']],
                      left_index=True, right_on='date', how='left').reset_index(drop=True).ffill()
    merged['return'] = merged['total'] / merged['cumsum']

    returns = merged.loc[:, ['date', 'return']]
    returns.columns = ['date1', 'price1']

    timestamp = returns.date1.iloc[-1]

    return returns, timestamp


def refresh_cashflows():
    """
    Refresh cashflow and cummulated cashflows and upload to Cashflow model.
    """
    try:
        last_date = Cashflows.objects.latest('date').date
        last_cumsum = Cashflows.objects.get(date=last_date).cumsum
    except ObjectDoesNotExist:
        last_date = datetime.date(2020, 4, 1)
        last_cumsum = 0

    # handle no new data is available
    try:
        cashflow_df = D.get_cash_flows(last_date + relativedelta(days=1))
    except KeyError:
        return None

    if not cashflow_df.empty:
        cashflow_df['cumsum'] = cashflow_df.cashflow.cumsum()
        cashflow_df.iloc[0, 2] += last_cumsum

        upload_df = pd.DataFrame(index=date_range_gen(cashflow_df.iloc[0, 0], cashflow_df.iloc[-1, 0]))
        upload_df = upload_df.merge(cashflow_df, left_index=True, right_on='date', how="left").set_index("date").ffill()
        upload_df = upload_df.reset_index()

        Cashflow.objects.bulk_create([Cashflow(**vals) for vals in upload_df.to_dict('records')])



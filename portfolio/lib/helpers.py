import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta

from portfolio.lib.degiro_api import DegiroAPI
from portfolio.lib.mail import Mail
from portfolio.lib.performance_measures import returns, annualized_returns, std, sharpe, var, max_drawdown
from portfolio.lib.utils import date_range_gen
from portfolio.models import Depot, Transactions

from portfolio.lib.yf_api import YF


def measure_loop(performance: pd.Series) -> dict:
    """
    Loop through a range of performance measure calculations and return the result of all.
    :param performance: Time series the calculations should be based on
    """
    switcher = {
        1: returns,
        2: annualized_returns,
        3: std,
        4: sharpe,
        5: var,
        6: max_drawdown,
    }

    data = dict()
    for key in switcher.keys():
        measure = switcher.get(key)
        data = {**data, **measure(performance)}

    return data


# todo ==== all the following stuff definitely needs to be structured better

def initiate_portfolio():
    refresh_depot_data()
    update_price_database()
    df = daily_depot_prices()
    refresh_price_data(df)
    refresh_cashflows()


def generate_overview():
    df = generate_portfolio_data().reset_index().rename(columns={'index': 'Symbol'}).to_dict('records')
    return df


def refresh_depot_data():
    """
    Refresh depot data and update database.
    """

    def fill_non_transaction_dates():
        """
        On days without transactions use portfolio from previous day
        """
        first_date = Depot.objects.earliest('date').date
        last_date = Depot.objects.latest('date').date

        date_iterator = first_date

        while date_iterator <= last_date:

            if Depot.objects.filter(date__exact=date_iterator).count() == 0:
                prev = date_iterator - relativedelta(days=1)
                last_portfolio = list(Depot.objects.filter(date__exact=prev).values('symbol', 'pieces'))

                for asset in last_portfolio:
                    asset['date'] = date_iterator

                Depot.objects.bulk_create([Depot(**vals) for vals in last_portfolio])

            date_iterator = date_iterator + relativedelta(days=1)

    def assemble_portfolio(last_portfolio: dict, latest_date: datetime.date, transactions):
        """
        Create all new daily portfolios since last update
        """

        def upload_new_transactions(date, portfolio_at_date):
            """
            Upload new transactions to database
            """
            upload = [{'symbol': k, 'pieces': v, 'date': date} for k, v in portfolio_at_date.items()]
            Depot.objects.bulk_create([Depot(**vals) for vals in upload])

        if len(transactions) == 0:
            return None

        today = datetime.date.today()
        date_iterator = latest_date - relativedelta(days=1)

        portfolio_at_date = {x['symbol']: x['pieces'] for x in last_portfolio}

        while date_iterator <= today:
            date_iterator = date_iterator + relativedelta(days=1)
            print(date_iterator)
            daily_buys = [t for t in transactions if t['buysell'] == 'B' and t['date'] == date_iterator]

            daily_sells = [t for t in transactions if t['buysell'] == 'S' and t['date'] == date_iterator]

            if len(daily_buys) == 0 and len(daily_sells) == 0:
                continue

            daily_buys_red = {}
            daily_sells_red = {}

            if len(daily_buys) > 0:
                daily_buys_info = D.get_products_by_id(list(set([x['productId'] for x in daily_buys])))
                # todo: take out the following: Bad error handling
                if list(daily_buys_info[0].keys())[0] == 'errors':
                    continue

                daily_buys_symbol = [{k: v['symbol']} for k, v in
                                     zip(daily_buys_info[0].keys(), daily_buys_info[0].values())]

                daily_buys_symbol = {k: v for d in daily_buys_symbol for k, v in d.items()}

                daily_buys_red = [{k: v for k, v in x.items() if k in ['productId', 'quantity']} for x in daily_buys]

                for x in daily_buys_red:
                    x.update({'symbol': daily_buys_symbol[x['productId']]})
                    del x['productId']

                daily_buys_red = {x['symbol']: x['quantity'] for x in daily_buys_red}

            if len(daily_sells) > 0:
                daily_sells_info = D.get_products_by_id([x['productId'] for x in daily_sells])
                # todo: take out the following: Bad error handling
                if list(daily_sells_info[0].keys())[0] == 'errors':
                    continue

                daily_sells_symbol = [{k: v['symbol']} for k, v in
                                      zip(daily_sells_info[0].keys(), daily_sells_info[0].values())]

                daily_sells_symbol = {k: v for d in daily_sells_symbol for k, v in d.items()}

                daily_sells_red = [{k: v for k, v in x.items() if k in ['productId', 'quantity']} for x in daily_sells]

                for x in daily_sells_red:
                    x.update({'symbol': daily_sells_symbol[x['productId']]})
                    del x['productId']

                daily_sells_red = {x['symbol']: x['quantity'] for x in daily_sells_red}

            portfolio_at_date = dict(Counter(portfolio_at_date) + Counter(daily_buys_red) + Counter(daily_sells_red))

            upload_new_transactions(date=date_iterator, portfolio_at_date=portfolio_at_date)

            print('Successful upload')

    # Get the latest portfolio
    last_portfolio = Depot.objects.get_latest_portfolio().values('symbol', 'pieces')
    latest_date = Depot.objects.get_latest_date()

    # Get all transactions since the latest portfolio
    Degiro = DegiroAPI()
    Degiro.login()
    Degiro.get_config()
    transactions = Degiro.get_transactions_clean(from_date=latest_date, to_date=datetime.date.today())

    # exclude existing transactions
    transactions = [x for x in transactions if x['id'] not in
                    Transactions.objects.filter(id__in=transactions).values('id')]

    assemble_portfolio(last_portfolio, latest_date, transactions)

    # Upload new transactions
    Transactions.objects.bulk_create([Transactions(**t) for t in transactions])

    fill_non_transaction_dates()

    # todo: try whether the following works
    update_price_database()
    # refresh_price_data() -> This should eventually be done in the database and not in pandas as is the case now


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

    saved_depot = portfolio_df[portfolio_df.date == latest_date].loc[:,['id', 'symbol', 'pieces']]

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


def refresh_price_data(df):
    """
    Add daily price info to the depot table
    """
    updatable_objects = Depot.objects.filter(price__exact=0)

    keys = list(updatable_objects.values('symbol', 'date'))

    for key in keys:
        # get price from database
        try:
            price = Prices.objects.get(**key).price
        except ObjectDoesNotExist:
            price = 0

        # update price in depot
        position = Depot.objects.get(**key)
        position.price = price
        position.save()


def update_price_database():
    # todo: test whether this works when we *update* instead of gather entirely new data
    depot_symbols = [x['symbol'] for x in list(Depot.objects.all().values('symbol').distinct())]
    existing_symbols = [x['symbol'] for x in list(Prices.objects.all().values('symbol').distinct())]
    non_existing_symbols = [x for x in depot_symbols if x not in existing_symbols]

    update_necessary = False

    # handle existing symbols
    if len(Prices.objects.filter(symbol__in=existing_symbols).values()) > 0:
        update_necessary = True
        start_date = Prices.objects.filter(symbol__in=existing_symbols).latest('date').date + relativedelta(days=1)
        end_date = datetime.date.today()

    # handle non existing symbols
    if len(non_existing_symbols) > 0:
        update_necessary = True
        start_date = datetime.date(2020, 1, 1)
        end_date = datetime.date.today()

    if update_necessary:
        yahoo_df = YF.get_prices(non_existing_symbols, start=start_date, end=end_date)

        if yahoo_df.empty:
            print('Yahoo Finance didn\'t return anything.')
            return None

        ffilled_df = YF.ffill_yahoo_data(yahoo_df).reset_index()

        df_out = pd.melt(ffilled_df, id_vars='index')
        df_out.columns = ['date', 'symbol', 'price']
        if df_out['price'].isna().sum() > 0:
            dropped = list(df_out.iloc[df_out['price'].isna().values,]['symbol'].unique())
            df_out = df_out.dropna()
            print(f'Found NA values. Dropped {dropped}.')

        dict_out = df_out.to_dict('records')

        Prices.objects.bulk_create([Prices(**vals) for vals in dict_out])


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

        Cashflows.objects.bulk_create([Cashflows(**vals) for vals in upload_df.to_dict('records')])


def daily_depot_prices() -> pd.DataFrame:
    """
    Return a df with daily depot and respective prices
    """
    df_depot = pd.DataFrame(list(Depot.objects.all().values())).loc[:, ['symbol', 'pieces', 'date']]
    start_date = df_depot['date'].min()
    df_prices = pd.DataFrame(list(Prices.objects.filter(date__gte=start_date).values())).loc[:,
                ['symbol', 'date', 'price']]
    df = pd.merge(df_depot, df_prices, left_on=['date', 'symbol'], right_on=['date', 'symbol'], how='inner')

    return df


def send_report(report_path: str, **kwargs):
    receiver_mail = kwargs.get('receiver_mail', 'leopold.pfeiffer@gmx.de')
    subject = kwargs.get('subject', 'Your DegiroAPI Report')
    body = kwargs.get('body', 'Hello,\n\nPlease find attached your current DegiroAPI portfolio report.\n\nKind regards,'
                              '\nLeopold\n\n')
    Mail.send(receiver_mail, subject, body, report_path)


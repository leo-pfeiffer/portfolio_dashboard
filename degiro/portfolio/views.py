from django.template.loader import render_to_string, get_template
from django.views import generic
from django.http import HttpResponse
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from weasyprint import HTML

from bokeh.plotting import figure, output_file, show
from bokeh.io import export_png, export_svgs

from .lib.degiro_helpers import generate_portfolio_data, get_transactions, get_info_by_productId, get_cashflows
from .lib.helpers import daterange, send_email
from .lib.yahoodata import get_yahoo_data, ffill_yahoo_data
from .tables import PortfolioTable
from django_tables2 import RequestConfig
from .models import Depot, Transactions, Prices, Cashflows
import datetime
import tempfile
from dateutil.relativedelta import relativedelta
from collections import Counter
import numpy as np
import pandas as pd


class IndexView(generic.TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request):
        initiate_portfolio()
        return render(request, self.template_name)


def initiate_portfolio():
    refresh_depot_data()
    update_price_database()
    df = daily_depot_prices()
    refresh_price_data(df)
    refresh_cashflows()


def portfolio_allocation(request):
    df = generate_portfolio_data()
    data = [[x] for x in df['Allocation'].values.tolist()]
    labels = [[x] for x in df.index.tolist()]

    return render(request, 'portfolio/portfolio-allocation.html', {
        'labels': labels,
        'data': data,
    })


def portfolio_overview(request):
    df = generate_portfolio_data().reset_index().rename(columns={'index': 'Symbol'}).to_dict('records')
    out = PortfolioTable(df)
    RequestConfig(request).configure(out)
    return render(request, 'portfolio/portfolio-overview.html', {'table': out})


def create_report(request):

    financial_data = get_yahoo_data(['DOCU'], start=datetime.date(2020, 1, 1), end=datetime.date(2020, 7, 11))
    data = financial_data.to_frame().reset_index()
    data.columns = ['date1', 'price1']
    timestamp = datetime.date.today()

    # data, timestamp = create_performance_time_series()

    p = figure(y_axis_type="linear", x_axis_type='datetime',
               plot_height=400, plot_width=800)
    p.xaxis.axis_label = 'Date'
    p.yaxis.axis_label = 'Performance index'

    p.line(data.date1, data.price1, line_color="blue", line_width=3)
    p.toolbar.logo = None
    p.toolbar_location = None
    output_file("static/degiro/images/line_chart.html", title="Line Chart")
    export_png(p, filename="static/degiro/images/performance_graph.png")

    last_dt = Depot.objects.latest('date').date
    depot = Depot.objects.filter(date__exact=last_dt).values('symbol', 'pieces')

    # Rendered
    context = {'people': depot, 'timestamp': timestamp}
    html_template = render_to_string('portfolio/portfolio-create-report.html', context)
    html_object = HTML(string=html_template, base_url=request.build_absolute_uri())
    html_object.write_pdf("static/degiro/pdf/report.pdf")

    # send mail
    send_email('leopold.pfeiffer@gmx.de', 'Test Mail', 'This is a python test', "static/degiro/pdf/report.pdf")

    pdf_file = html_object.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="home_page.pdf"'
    return response


def create_performance_time_series():
    """Create a dataframe containing the returns time series up to timestamp"""
    # calculate portfolio
    # included_positions = Depot.objects.filter(~Q(price__exact=0))
    included_positions = Depot.objects.all()
    portfolio_df = pd.DataFrame(list(included_positions.values()))
    portfolio_df['total'] = portfolio_df.pieces * portfolio_df.price

    portfolio_df = portfolio_df[portfolio_df.symbol != 'BITCOIN XBTE']

    first_zero_date = portfolio_df[portfolio_df.price == 0].sort_values('date').date.iloc[0]

    portfolio_df = portfolio_df[portfolio_df.date < first_zero_date]

    performance_df = portfolio_df[['date', 'total']].groupby("date").sum()
    cashflow_df = pd.DataFrame(list(Cashflows.objects.all().values()))

    merged = pd.merge(performance_df, cashflow_df.loc[:, ['date', 'cumsum']], left_index=True, right_on='date')
    merged['return'] = merged['total']/merged['cumsum']

    returns = merged.loc[:, ['date', 'return']]
    returns.columns = ['date1', 'price1']

    timestamp = returns.date1.iloc[-1]

    return returns, timestamp


def portfolio_performance(request):
    """Portfolio performance view"""
    initiate_portfolio()

    # dummy data
    # financial_data = get_yahoo_data(['DOCU'], start=datetime.date(2020, 1, 1), end=datetime.date(2020, 7, 11))
    # prices = financial_data.to_frame().reset_index()
    # prices.columns = ['date1', 'price1']
    # data = prices.to_json(orient='records')
    # timestamp = datetime.date.today()

    returns, timestamp = create_performance_time_series()

    data = returns.to_json(orient='records')

    return render(request, 'portfolio/portfolio-performance.html', {
        'data': data,
        'timestamp': timestamp,
    })


def portfolio_depot(request):
    """portfolio depot view"""
    refresh_depot_data()
    return render(request, 'portfolio/portfolio-depot.html')


def refresh_depot_data():
    """
    Refresh depot data and update database.
    """

    def get_last_portfolio():
        try:
            latest_date = Depot.objects.latest('date').date
            return {'latest_date': latest_date,
                    'latest_portfolio': [x for x in Depot.objects.values().filter(date=latest_date)]}
        except ObjectDoesNotExist:
            return {'latest_date': datetime.date(2020, 1, 1), 'latest_portfolio': []}

    def exclude_existing_transactions(transactions):
        """
        exclude duplicated transactions (e.g. from same day)
        """
        existing_transactions = [x['id'] for x in list(Transactions.objects.all().values('id'))]

        return [x for x in transactions if x['id'] not in existing_transactions]

    def update_transactions(transactions):
        """
        Upload new transactions to db
        """
        Transactions.objects.bulk_create([Transactions(**vals) for vals in transactions])

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
                daily_buys_info = get_info_by_productId(list(set([x['productId'] for x in daily_buys])))
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
                daily_sells_info = get_info_by_productId([x['productId'] for x in daily_sells])
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

    last_portfolio_all = get_last_portfolio()
    last_portfolio = last_portfolio_all['latest_portfolio']
    last_portfolio = [{k: v for k, v in d.items() if k in ['symbol', 'pieces']} for d in last_portfolio]
    latest_date = last_portfolio_all['latest_date']

    transactions = get_transactions(latest_date)
    transactions = exclude_existing_transactions(transactions)
    assemble_portfolio(last_portfolio, latest_date, transactions)
    update_transactions(transactions)
    fill_non_transaction_dates()
    # todo: try whether the following works
    update_price_database()
    # refresh_price_data() -> This should eventually be done in the database and not in pandas as is the case now


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
        yahoo_df = get_yahoo_data(non_existing_symbols, start=start_date, end=end_date)

        if yahoo_df.empty:
            print('Yahoo Finance didn\'t return anything.')
            return None
        ffilled_df = ffill_yahoo_data(yahoo_df).reset_index()

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
        cashflow_df = get_cashflows(last_date + relativedelta(days=1))
    except KeyError:
        return None

    if not cashflow_df.empty:
        cashflow_df['cumsum'] = cashflow_df.cashflow.cumsum()
        cashflow_df.iloc[0, 2] += last_cumsum

        upload_df = pd.DataFrame(index=daterange(cashflow_df.iloc[0, 0], cashflow_df.iloc[-1, 0]))
        upload_df = upload_df.merge(cashflow_df, left_index=True, right_on='date', how="left").set_index("date").ffill()
        upload_df = upload_df.reset_index()

        Cashflows.objects.bulk_create([Cashflows(**vals) for vals in upload_df.to_dict('records')])


def daily_depot_prices() -> pd.DataFrame:
    """
    Return a df with daily depot and respective prices
    """
    df_depot = pd.DataFrame(list(Depot.objects.all().values())).loc[:, ['symbol', 'pieces', 'date']]
    start_date = df_depot['date'].min()
    df_prices = pd.DataFrame(list(Prices.objects.filter(date__gte=start_date).values())).loc[:, ['symbol', 'date', 'price']]
    df = pd.merge(df_depot, df_prices, left_on=['date', 'symbol'], right_on=['date', 'symbol'], how='inner')

    return df

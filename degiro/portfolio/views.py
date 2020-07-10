from django.views import generic
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from .lib.degiro_helpers import generate_portfolio_data, get_transactions, get_info_by_productId
from .lib.yahoodata import get_yahoo_data
from .tables import PortfolioTable
from django_tables2 import RequestConfig
from .models import Depot, Transactions
import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter
import numpy as np
import pandas as pd


class IndexView(generic.TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request):
        refresh_depot_data()
        return render(request, self.template_name)


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
                prev = date_iterator-relativedelta(days=1)
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
    # todo: for all assets for all dates: download yahoo price data and write to db


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


def portfolio_performance(request):
    refresh_depot_data()

    # dummy data
    financial_data = get_yahoo_data(['DOCU'], start="2020-01-01", end="2020-07-08")
    prices = financial_data['prices'].to_frame().reset_index()
    prices.columns = ['date1', 'price1']
    data = prices.to_json(orient='records')

    return render(request, 'portfolio/portfolio-performance.html', {
        'data': data
    })


def portfolio_depot(request):
    refresh_depot_data()
    return render(request, 'portfolio/portfolio-depot.html')
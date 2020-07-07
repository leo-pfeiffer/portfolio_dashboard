from django.views import generic
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from .lib.degiro_helpers import generate_portfolio_data, get_transactions, get_info_by_productId
from .tables import PortfolioTable
from django_tables2 import RequestConfig
from .models import Depot, Transactions
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd


class IndexView(generic.TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request):
        refresh_portfolio()
        return render(request, self.template_name)


def refresh_portfolio():
    """
    Refresh depot data and update database.
    """
    def get_last_portfolio():
        try:
            latest_date = Depot.objects.latest('date').date
            return {'latest_date': latest_date,
                    'symbols': list(Depot.objects.values_list('symbol').filter(date=latest_date).values())}
        except ObjectDoesNotExist:
            return {'latest_date': datetime.date(2020, 1, 1), 'symbols': []}

    def update_transactions(transactions):
        """
        Upload new transactions to db
        """
        Transactions.objects.bulk_create([Transactions(**vals) for vals in transactions])

    def assemble_portfolio(latest_symbols: list, latest_date: datetime.date, transactions):
        # todo: This doesn't work yet: Need to consider pieces in portfolio as well
        """
        Create all new daily portfolios since last update
        """
        existing_transactions = [x['id'] for x in list(Transactions.objects.all().values('id'))]

        # exclude duplicated transactions (e.g. from same day)
        transactions = [x for x in transactions if x['id'] not in existing_transactions]
        transactions_df = pd.DataFrame(transactions)
        today = datetime.date.today()
        date_iterator = latest_date
        portfolio_at_date = latest_symbols

        while date_iterator <= today:
            # todo: consider pieces
            daily_buys = transactions_df[(transactions_df.date == date_iterator) &
                                         (transactions_df.buysell == "B")].productId.values()

            daily_sells = transactions_df[(transactions_df.date == date_iterator) &
                                          (transactions_df.buysell == "S")].productId.values()

            daily_buys_info = get_info_by_productId(daily_buys)
            daily_sells_info = get_info_by_productId(daily_sells)

            daily_buys_symbol = [x['symbol'] for x in daily_buys_info]
            daily_sells_symbol = [x['symbol'] for x in daily_sells_info]

            portfolio_at_date = list(set(portfolio_at_date).union(daily_buys_symbol))
            portfolio_at_date = portfolio_at_date.remove(daily_sells_symbol)

            # todo: update model De

            date_iterator += relativedelta(days=1)

    last_portfolio = get_last_portfolio()
    last_symbols = last_portfolio['symbols']
    latest_date = last_portfolio['latest_date']
    transactions = get_transactions(latest_date)
    assemble_portfolio(last_symbols, latest_date, transactions)
    update_transactions(transactions)

    #product_ids = [x['productId'] for x in transactions]


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
    return render(request, 'portfolio/portfolio-performance.html')

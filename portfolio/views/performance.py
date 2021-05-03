from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from portfolio.lib.helpers import generate_overview, initiate_portfolio, create_performance_time_series
from portfolio.tables import PortfolioTable


class Performance(TemplateView):
    template_name = 'portfolio/performance.html'

    def get(self, request, *args, **kwargs):
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

        return render(request, 'portfolio/performance.html', {
            'data': data,
            'timestamp': timestamp,
        })
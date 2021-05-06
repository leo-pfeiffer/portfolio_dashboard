import datetime

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from portfolio.lib.aggregation import create_portfolio, create_performance_series


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request, **kwargs):

        portfolio = create_portfolio()

        performance_series = create_performance_series()

        # ytd performance
        start_of_year = performance_series.loc[datetime.date(datetime.date.today().year, 1, 1):][0]
        current = performance_series[-1]
        ytd_performance_percent = round(((current / start_of_year) - 1) * 100, 2)

        # convert portfolio to records
        portfolio_records = portfolio.to_dict('records')
        portfolio_value = round(portfolio.subtotal.sum(), 2)

        # allocation data
        portfolio_no_na = portfolio.dropna(subset=['allocation'])
        allocation_labels = portfolio_no_na.symbol.values.tolist()
        allocation_data = portfolio_no_na.allocation.values.tolist()

        # performance data
        performance = create_performance_series()
        performance_labels = performance.index.tolist()
        performance_data = [round((x-1)*100, 2) for x in performance.values.tolist()]

        return render(request, self.template_name, {
            'portfolio': portfolio_records,
            'portfolio_value': portfolio_value,
            'ytd_performance': ytd_performance_percent,
            'allocation_labels': allocation_labels,
            'allocation_data': allocation_data,
            'performance_labels': performance_labels,
            'performance_data': performance_data,

        })

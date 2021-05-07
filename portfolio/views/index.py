import datetime

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from portfolio.lib.aggregation import create_portfolio, create_performance_series
from portfolio.lib.performance_measures import PerformanceMeasures


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request, **kwargs):

        portfolio = create_portfolio()

        performance_series = create_performance_series()

        # ytd performance
        if not performance_series.empty:
            start_of_year = performance_series.loc[datetime.date(datetime.date.today().year, 1, 1):][0]
            current = performance_series[-1]
            ytd_performance_percent = round(((current / start_of_year) - 1) * 100, 2)

        else:
            ytd_performance_percent = 0

        # performance measures
        if not performance_series.empty:
            measure_data = PerformanceMeasures.measure_loop(performance_series)
            for key, value in measure_data.items():
                if key == 'sharpe':
                    measure_data[key] = round(value, 2)
                else:
                    measure_data[key] = '{:.2%}'.format(value)

            # performance data
            performance_labels = performance_series.index.tolist()
            performance_data = [round((x - 1) * 100, 2) for x in performance_series.values.tolist()]

        else:
            measure_data = None
            performance_labels = []
            performance_data = []

        measure_help = PerformanceMeasures.HELP_TEXT

        if not portfolio.empty:
            # convert portfolio to records
            portfolio_records = portfolio.to_dict('records')
            portfolio_value = round(portfolio.subtotal.sum(), 2)

            # allocation data
            portfolio_no_na = portfolio.dropna(subset=['allocation'])
            allocation_labels = portfolio_no_na.symbol.values.tolist()
            allocation_data = portfolio_no_na.allocation.values.tolist()

        else:
            portfolio_records = []
            portfolio_value = 0
            allocation_labels = []
            allocation_data = []

        return render(request, self.template_name, {
            'portfolio': portfolio_records,
            'portfolio_value': portfolio_value,
            'ytd_performance': ytd_performance_percent,
            'allocation_labels': allocation_labels,
            'allocation_data': allocation_data,
            'performance_labels': performance_labels,
            'performance_data': performance_data,
            'measure_data': measure_data,
            'measure_help': measure_help
        })

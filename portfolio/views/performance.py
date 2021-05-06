import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from portfolio.lib.aggregation import create_performance_series


class Performance(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/performance.html'

    def get(self, request, *args, **kwargs):
        """Portfolio performance view"""

        performance = create_performance_series()
        performance = performance.reset_index()
        performance.columns = ['date', 'value']

        records = performance.to_json(orient='records')

        timestamp = datetime.date.today()

        return render(request, 'portfolio/performance.html', {
            'data': records,
            'timestamp': timestamp,
        })
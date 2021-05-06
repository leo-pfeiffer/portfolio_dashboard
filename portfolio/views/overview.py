from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from portfolio.tables import PortfolioTable


class Overview(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/allocation.html'

    def get(self, request, *args, **kwargs):
        df = generate_overview()
        out = PortfolioTable(df)
        RequestConfig(request).configure(out)

        return render(request, self.template_name, {
            'table': out
        })
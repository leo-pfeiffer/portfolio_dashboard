from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from portfolio.lib.aggregation import create_portfolio


class Allocation(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/allocation.html'

    def get(self, request, *args, **kwargs):

        portfolio = create_portfolio()
        portfolio.dropna(subset=['allocation'], inplace=True)
        labels = portfolio.symbol.values.tolist()
        data = portfolio.allocation.values.tolist()

        return render(request, self.template_name, {
            'labels': labels,
            'data': data
        })
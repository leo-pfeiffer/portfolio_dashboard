from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from portfolio.lib.degiro_helpers import generate_portfolio_data


class Allocation(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/portfolio-allocation.html'

    def get(self, request, *args, **kwargs):
        df = generate_portfolio_data()
        data = [[x] for x in df['Allocation'].values.tolist()]
        labels = [[x] for x in df.index.tolist()]

        return render(request, self.template_name, {
            'labels': labels,
            'data': data
        })
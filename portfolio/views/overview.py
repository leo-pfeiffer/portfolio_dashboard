from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from portfolio.lib.aggregation import create_portfolio


class Overview(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/overview.html'

    def get(self, request, *args, **kwargs):
        portfolio = create_portfolio()
        portfolio = portfolio.to_dict('records')

        return render(request, self.template_name, {
            'portfolio': portfolio
        })
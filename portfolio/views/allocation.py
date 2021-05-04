from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from portfolio.lib.degiro_api import DegiroAPI


class Allocation(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/portfolio-allocation.html'

    def get(self, request, *args, **kwargs):

        # todo don't get this from the API!!! Save it in the data base once a day and then retrieve it from there
        Degiro = DegiroAPI()
        Degiro.login()
        Degiro.get_config()

        df = Degiro.get_portfolio_summary()

        data = [[x] for x in df['Allocation'].values.tolist()]
        labels = [[x] for x in df.index.tolist()]

        return render(request, self.template_name, {
            'labels': labels,
            'data': data
        })
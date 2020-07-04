from django.views import generic
from django.shortcuts import render
from .lib.portfolioanalysis import generate_portfolio_data
from .tables import PortfolioTable
from django_tables2 import RequestConfig
import numpy as np


class IndexView(generic.TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request):
        return render(request, self.template_name)


def portfolio_allocation(request):
    df = generate_portfolio_data()
    data = [[x] for x in df['Allocation'].values.tolist()]
    labels = [[x] for x in df.index.tolist()]

    return render(request, 'portfolio/portfolio-allocation.html', {
        'labels': labels,
        'data': data,
    })


def portfolio_allocation2(request):
    df = generate_portfolio_data().reset_index().rename(columns={'index': 'Symbol'}).to_dict('records')
    out = PortfolioTable(df)
    RequestConfig(request).configure(out)
    return render(request, 'portfolio/portfolio-overview.html', {'table': out})

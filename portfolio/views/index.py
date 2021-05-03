from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'portfolio/index.html'
    #
    # def get(self, request):
    #     # initiate_portfolio()
    #     return render(request, self.template_name)

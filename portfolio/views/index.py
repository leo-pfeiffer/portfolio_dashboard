from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/new-index.html'

    def get(self, request, **kwargs):
        return render(request, self.template_name, {
            'username': 'Heinrich Pfeiffer'
        })

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import TemplateView


class Depot(LoginRequiredMixin, TemplateView):
    template_name = 'portfolio/depot.html'

    def get(self, request, *args, **kwargs):
        # refresh_depot_data()
        return render(request, self.template_name)

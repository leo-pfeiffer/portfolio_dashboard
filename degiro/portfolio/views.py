from django.views import generic
from django.shortcuts import render

class IndexView(generic.TemplateView):
    template_name = 'portfolio/index.html'

    def get(self, request):
        return render(request, self.template_name)

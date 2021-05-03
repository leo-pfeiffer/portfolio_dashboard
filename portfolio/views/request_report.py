import os

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from degiro.settings import PDFS
from portfolio.forms import RequestReportForm
from portfolio.lib.helpers import send_report


class RequestReport(TemplateView):

    template_name = 'portfolio/index.html'

    def get(self, request, *args, **kwargs):
        form = RequestReportForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # create a form instance and populate it with data from the request:
        form = RequestReportForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            report_path = os.path.join(PDFS, 'report.pdf')
            send_report(receiver_mail=form.cleaned_data['email'],
                        report_path=report_path)

            return HttpResponseRedirect('#')

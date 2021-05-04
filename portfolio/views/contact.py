from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from project.settings import MAIL
from portfolio.forms import ContactForm

import datetime

from portfolio.lib.helpers import send_email


class ContactView(TemplateView):
    template_name = 'portfolio/contact.html'

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():

            receiver_email = MAIL['EMAIL']
            sender_email = form.cleaned_data['email']
            sender_name = form.cleaned_data['name']
            subject = form.cleaned_data['subject']
            content = form.cleaned_data['content']
            timestamp = datetime.datetime.strftime(datetime.datetime.now(), format='%Y-%m-%d %H:%M:%S')

            body = f'Neue Mail via Kontaktformular.' \
                   f'\nAbsender: {sender_name}.' \
                   f'\nE-Mail: {sender_email}' \
                   f'\nTimestamp: {timestamp}' \
                   f'\n\n--------------------\n\n' \
                   f'{content}'

            send_email(receiver_email=receiver_email, subject=subject, body=body)

            return HttpResponseRedirect('#')

    def get(self, request, *args, **kwargs):
        form = ContactForm();
        return render(request, self.template_name, {'form': form})

from django import forms


class RequestReportForm(forms.Form):
    email = forms.EmailField(label='E-mail address')
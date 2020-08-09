from django import forms


class RequestReportForm(forms.Form):
    email = forms.EmailField(label='E-mail Adresse')


class ContactForm(forms.Form):
    name = forms.CharField(required=True, label='Name')
    email = forms.EmailField(required=True, label='E-Mail Adresse')
    subject = forms.CharField(required=True, label='Betreff')
    content = forms.CharField(required=True, widget=forms.Textarea, label='Nachricht')
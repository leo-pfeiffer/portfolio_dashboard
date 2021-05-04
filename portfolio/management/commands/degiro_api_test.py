from django.core.management.base import BaseCommand

from portfolio.lib.degiro_api import DegiroAPI


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        degiro = DegiroAPI()
        degiro.login()
        degiro.get_config()

        x = 1
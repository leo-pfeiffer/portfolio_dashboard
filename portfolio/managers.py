import datetime
from django.db import models


class DepotManager(models.Manager):

    def get_latest_portfolio(self):
        """
        Return the latest portfolio.
        """
        if not self.exists():
            return self.none()

        return self.filter(date=self.latest('symbol_date__date').date)

    def get_portfolio_at_date(self, date: datetime.date):
        """
        Return the portfolio on a given date.
        """
        if not self.exists():
            return self.none()

        return self.filter(symbol_date__date=date)

    def get_latest_date(self):
        """
        Return the date of the latest portfolio.
        """
        if not self.exists():
            return None
        return self.latest('symbol_date__date').date


class DimensionSymbolDateManager(models.Manager):
    def get_existing(self, dates, symbols):
        if not self.exists():
            return self.none()

        return self.filter(
            date__gte=min(dates),
            date__lte=max(dates),
            symbol__in=symbols
        ).values_list('id', 'symbol', 'date')

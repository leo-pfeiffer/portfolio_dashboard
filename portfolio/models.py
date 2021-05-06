from django.db import models

from portfolio.managers import DepotManager, DimensionSymbolDateManager, CashflowManager


class DimensionSymbolDate(models.Model):
    symbol = models.CharField(max_length=100, verbose_name='Stock market symbol')
    date = models.DateField(verbose_name='Date')

    objects = DimensionSymbolDateManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['symbol', 'date'], name='unique_symbol_date')
        ]


class Depot(models.Model):
    pieces = models.FloatField(verbose_name='Number of pieces of the symbol')
    symbol_date = models.ForeignKey(DimensionSymbolDate, on_delete=models.CASCADE)

    objects = DepotManager()


class Asset(models.Model):
    isin = models.CharField(max_length=12, verbose_name='ISIN')
    symbol = models.CharField(max_length=100, verbose_name='Stock market symbol')
    name = models.TextField(verbose_name='Asset name')
    type = models.CharField(max_length=32, verbose_name='Asset type')
    currency = models.CharField(max_length=3, verbose_name='Asset currency')
    productId = models.CharField(max_length=32, verbose_name='Degiro product ID')


class Price(models.Model):
    price = models.FloatField(default=0, verbose_name='Price of the asset on the date')
    symbol_date = models.ForeignKey(DimensionSymbolDate, on_delete=models.CASCADE)


class Transaction(models.Model):
    id = models.CharField(max_length=64, primary_key=True, verbose_name='Transaction ID')
    productId = models.CharField(max_length=32, verbose_name='Degiro product ID of associated product')
    date = models.DateField(verbose_name='Date')
    buysell = models.CharField(max_length=1, verbose_name='Buy or Sell transaction')
    price = models.FloatField(default=None, blank=True, null=True, verbose_name='Price of the underlying asset')
    quantity = models.FloatField(default=None, blank=True, null=True, verbose_name='Quantity of the underlying asset')
    total = models.FloatField(default=None, blank=True, null=True, verbose_name='Total value of the transaction')


class Cashflow(models.Model):
    date = models.DateField(unique=True, verbose_name='Date')
    cashflow = models.FloatField(verbose_name='Value of the Cashflow')

    objects = CashflowManager()
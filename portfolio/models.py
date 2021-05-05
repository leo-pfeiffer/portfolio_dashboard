from django.db import models

from portfolio.managers import DepotManager, DimensionSymbolDateManager


# todo add descriptions and verbose names


class DimensionSymbolDate(models.Model):
    symbol = models.CharField(max_length=100)
    date = models.DateField()

    objects = DimensionSymbolDateManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['symbol', 'date'], name='unique_symbol_date')
        ]


class Depot(models.Model):
    pieces = models.FloatField()
    symbol_date = models.ForeignKey(DimensionSymbolDate, on_delete=models.CASCADE)

    objects = DepotManager()


class Assets(models.Model):
    isin = models.CharField(max_length=12)
    symbol = models.CharField(max_length=100)
    name = models.TextField()
    type = models.CharField(max_length=32)
    currency = models.CharField(max_length=3)
    productId = models.CharField(max_length=32)  # degiro productID


class Prices(models.Model):
    price = models.FloatField(default=0)
    symbol_date = models.ForeignKey(DimensionSymbolDate, on_delete=models.CASCADE)


class Transactions(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    productId = models.CharField(max_length=32)
    date = models.DateField()
    buysell = models.CharField(max_length=1)
    price = models.FloatField(default=None, blank=True, null=True)
    quantity = models.FloatField(default=None, blank=True, null=True)
    total = models.FloatField(default=None, blank=True, null=True)


class Cashflows(models.Model):
    date = models.DateField(unique=True)
    cashflow = models.FloatField()
    cumsum = models.FloatField()
from django.db import models


class Depot(models.Model):
    symbol = models.CharField(max_length=32)
    pieces = models.FloatField()
    date = models.DateField()
    price = models.FloatField(default=0)


class Assets(models.Model):
    isin = models.CharField(max_length=32)
    symbol = models.CharField(max_length=10)
    name = models.TextField()
    type = models.CharField(max_length=32)
    currency = models.CharField(max_length=3)
    productId = models.CharField(max_length=32)  # degiro productID


class Prices(models.Model):
    symbol = models.CharField(max_length=32)
    date = models.DateField()
    price = models.FloatField(default=0)


class Currencies(models.Model):
    currency = models.CharField(max_length=3)
    rate = models.FloatField(verbose_name='EUR/X Exchange Rate')
    date = models.DateField()


class Transactions(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    productId = models.CharField(max_length=32)
    date = models.DateField()
    buysell = models.CharField(max_length=1)
    price = models.FloatField(default=None, blank=True, null=True)
    quantity = models.FloatField(default=None, blank=True, null=True)
    total = models.FloatField(default=None, blank=True, null=True)
    orderTypeId = models.IntegerField(default=None, blank=True, null=True)
    counterParty = models.CharField(max_length=64, default=None, blank=True, null=True)
    transfered = models.BooleanField(default=None, blank=True, null=True)
    fxRate = models.FloatField(default=None, blank=True, null=True)
    totalInBaseCurrency = models.FloatField(default=None, blank=True, null=True)
    feeInBaseCurrency = models.FloatField(default=None, blank=True, null=True)
    totalPlusFeeInBaseCurrency = models.FloatField(default=None, blank=True, null=True)
    transactionTypeId = models.IntegerField(default=None, blank=True, null=True)

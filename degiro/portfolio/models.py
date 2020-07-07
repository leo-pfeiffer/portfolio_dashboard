from django.db import models


class Depot(models.Model):
    symbol = models.CharField(max_length=32)
    date = models.DateField()


class Assets(models.Model):
    isin = models.CharField(max_length=32)
    symbol = models.CharField(max_length=10)
    name = models.TextField()
    type = models.CharField(max_length=32)
    currency = models.CharField(max_length=3)
    productId = models.CharField(max_length=32)  # degiro product ID


class Prices(models.Model):
    symbol = models.CharField(max_length=32)
    date = models.DateField()
    price = models.FloatField()


class Currencies(models.Model):
    currency = models.CharField(max_length=3)
    rate = models.FloatField(verbose_name='EUR/X Exchange Rate')
    date = models.DateField()

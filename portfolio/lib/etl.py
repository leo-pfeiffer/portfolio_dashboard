# Start an ETL process that gets the data from the external sources and puts it into the database.
# This should be the only place we poll the API directly. The application should get all its data from
# the database.
from typing import Dict

from pandas.tseries.offsets import BDay
import datetime

from portfolio.lib.degiro_api import DegiroAPI
from portfolio.models import Depot, Transactions


class Extraction:

    def __init__(self):
        self._degiro = DegiroAPI()
        self._transactions = list()
        self._product_info = dict()
        self._price_date = list()

        from_date = Depot.objects.get_latest_date() - BDay(1)
        self._from_date = from_date if from_date else datetime.datetime(2020, 1, 1).date()

    @property
    def data(self) -> Dict:
        # make sure we actually have all the data extracted
        assert len(self._transactions) > 0
        assert len(self._product_info) > 0
        assert len(self._price_date) > 0

        return {
            'transactions': self._transactions,
            'product_info': self._product_info,
            'price_data': self._price_date
        }

    def _config(self):
        """
        Configure the DegiroAPI (login and get config).
        """
        self._degiro.login()
        self._degiro.get_config()

    def _extract_transactions(self):
        to_date = datetime.date.today()
        transactions = self._degiro.get_transactions(self._from_date, to_date)

        # exclude existing transactions (in case of small overlap)
        self._transactions = [x for x in transactions if x['id'] not in
                              Transactions.objects.filter(id__in=transactions).values('id')]

    def _extract_product_info(self):
        """"
        Extract the product info for all products included in the new transactions.
        """
        # Make sure _extract_transactions is called first
        assert len(self._transactions) != 0

        product_ids = list(set([str(x['productId']) for x in self._transactions]))
        self._product_info = self._degiro.get_products_by_id(product_ids)

    def _extract_price_data(self):
        """
        Extract the price data for the time frame of the new transactions
        """

    def run(self):
        """
        Run the extraction.
        """
        self._config()
        self._extract_transactions()
        self._extract_product_info()
        self._extract_price_data()


class Transformation:
    # Transform the raw data into the required format
    def run(self):
        pass


class Loading:
    # Load transformed data into database
    def run(self):
        pass


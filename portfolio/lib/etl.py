import re
from collections import Counter
from typing import Dict, List, Any

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.db.models import Q
import datetime

from portfolio.lib.degiro_api import DegiroAPI
from portfolio.lib.yf_api import YF
from portfolio.models import Depot, Transactions, Assets, Prices, DimensionSymbolDate
from django.db.models import F


class Extraction:

    def __init__(self):
        self._degiro = DegiroAPI()
        self._transactions = list()
        self._product_info = dict()
        self._prices = list()

        from_date = Depot.objects.get_latest_date()
        self._from_date = from_date if from_date else datetime.datetime(2020, 1, 1).date()

    @property
    def data(self) -> Dict:

        return {
            'transactions': self._transactions,
            'product_info': self._product_info,
            'price_data': self._prices,
            'from_date': self._from_date
        }

    def _config(self):
        """
        Configure the DegiroAPI (login and get config).
        """
        self._degiro.login()
        self._degiro.get_config()

    def _exit(self):
        """
        Logout of the Degiro account.
        """
        self._degiro.logout()

    def _extract_transactions(self):
        """
        Extract the transactions from the degiro API.
        """
        print('_extract_transactions')
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
        print('_extract_product_info')

        product_ids = list(set([str(x['productId']) for x in self._transactions]))
        self._product_info = self._degiro.get_products_by_id(product_ids)

    def _extract_price_data(self):
        """
        Extract the price data for the time frame of the new transactions.
        """
        # symbols included in new transactions
        print('_extract_product_info')
        transaction_symbols = list(set([x['symbol'] for x in self._product_info.values()]))

        # symbols included in last portfolio
        portfolio_symbols = list(Depot.objects.get_portfolio_at_date(self._from_date).filter(
            ~Q(symbol_date__symbol__in=transaction_symbols)
        ).distinct('symbol_date__symbol').values_list('symbol_date__symbol', flat=True))

        # all symbols for which to get price data
        symbols = [*portfolio_symbols, *transaction_symbols]

        self._prices = YF.get_prices(symbols, start=self._from_date, end=datetime.date.today())

    def run(self):
        """
        Run the extraction process.
        """
        self._config()
        self._extract_transactions()
        self._extract_product_info()
        self._extract_price_data()
        self._exit()


class Transformation:

    def __init__(self, extraction_data: Dict):
        """
        :param extraction_data: data received from the extraction step. Must be a
            dictionary with keys 'transactions', 'product_info', 'price_data', 'from_date'.
        """

        try:
            assert 'transactions' in extraction_data.keys()
            assert 'product_info' in extraction_data.keys()
            assert 'price_data' in extraction_data.keys()
            assert 'from_date' in extraction_data.keys()
        except AssertionError as ae:
            print('Invalid extraction_data received.')
            raise ae

        self._extracted = extraction_data
        self._transactions = []
        self._product_info = {}
        self._price_data = {}
        self._portfolios = []
        self._symbol_date_combs = []

    @property
    def data(self):

        return {
            'transactions': self._transactions,
            'product_info': self._product_info,
            'price_data': self._price_data,
            'portfolios': self._portfolios,
            'symbol_date_combs': self._symbol_date_combs
        }

    def _transform_transactions(self):
        """
        Transform the extracted transactions.
        """

        print('_transform_transactions')
        transactions = self._extracted['transactions']

        transactions_clean = []
        # fix data types
        for transaction in transactions:

            regexed_date = re.compile(r'\d{4}-\d{2}-\d{2}').findall(transaction['date'])[0]

            transactions_clean.append({
                'id': str(transaction['id']),
                'productId': str(transaction['productId']),
                'date': datetime.datetime.strptime(regexed_date, '%Y-%m-%d').date(),
                'buysell': transaction['buysell'],
                'price': float(transaction['price']),
                'quantity': float(transaction['quantity']),
                'total': float(transaction['total']),
            })

        self._transactions = transactions_clean

    def _transform_product_info(self):
        """
        Transform the extracted product info.
        """

        print('_transform_product_info')
        product_info = self._extracted['product_info']
        product_info_clean = {}

        # extract only required data and fix data type
        for product in product_info.keys():

            product_info_clean[product] = {}
            product_info_clean[product]['productId'] = str(product_info[product]['id'])
            product_info_clean[product]['isin'] = product_info[product]['isin']
            product_info_clean[product]['symbol'] = product_info[product]['symbol']
            product_info_clean[product]['name'] = product_info[product]['name']
            product_info_clean[product]['type'] = product_info[product]['productTypeId']
            product_info_clean[product]['currency'] = product_info[product]['currency']

        self._product_info = product_info_clean

    def _build_portfolio(self):
        """
        Build the portfolio based on the latest available portfolio adding and removing
        positions based on the transactions.
        """

        print('_transform_product_info')

        # store daily portfolios
        portfolios = []

        # initialise values
        from_date = self._extracted['from_date']
        date_iterator = from_date

        latest_portfolio = Depot.objects.get_portfolio_at_date(from_date)\
            .annotate(symbol=F('symbol_date__symbol'))\
            .values('symbol', 'pieces')

        portfolio_at_date = {x['symbol']: x['pieces'] for x in latest_portfolio}

        same_day_start = date_iterator == datetime.date.today()

        # Iteratively build the portfolio
        while date_iterator <= datetime.date.today() and not same_day_start:

            # Extract buy and sell transactions of current date
            daily_transactions = [t for t in self._transactions
                                  if t['buysell'] in ['S', 'B'] and t['date'] == date_iterator]

            # On days without transactions, portfolio stays the same
            if len(daily_transactions) == 0:
                portfolios.append({'date': date_iterator, 'portfolio': portfolio_at_date})
                date_iterator += relativedelta(days=1)
                continue

            # get quantities per symbol
            daily_qtys = {}
            for transaction in daily_transactions:
                symbol = self._product_info[transaction['productId']]['symbol']
                quantity = transaction['quantity']

                # works for both buys and sells as for sells the quantity is negative
                if symbol in daily_qtys.keys():

                    # if no quantities left, don't include symbol
                    if -daily_qtys[symbol] != quantity:
                        daily_qtys[symbol] += quantity

                else:
                    daily_qtys[symbol] = quantity

            # update the total quantities in the portfolio
            portfolio_at_date = dict(Counter(portfolio_at_date) + Counter(daily_qtys))

            # save portfolio of current date
            portfolios.append({'date': date_iterator, 'portfolio': portfolio_at_date})

            date_iterator += relativedelta(days=1)

        # todo this can be made nicer
        # unnest portfolios and compile symbol date combinations
        symbol_date_combs = []

        unnested_portfolios: List[Dict[str, Any]] = []
        for portfolio in portfolios:
            for symbol in portfolio['portfolio'].keys():
                unnested_portfolios.append({
                    'date': portfolio['date'],
                    'symbol': symbol,
                    'pieces': portfolio['portfolio'][symbol]
                })

                # store the current symbol-date combination
                symbol_date_combs.append((symbol, portfolio['date']))

        self._portfolios = unnested_portfolios
        self._symbol_date_combs = list({*self._symbol_date_combs, *symbol_date_combs})

    def _transform_symbol_date_combs(self):
        """
        Transform the newly created symbol-date combinations.
        """
        print('_transform_symbol_date_combs')

        # dates only
        dates = [x[1] for x in self._symbol_date_combs]

        # get combinations already in the table
        existing = DimensionSymbolDate.objects.filter(date__in=dates).values_list('symbol', 'date')

        # filter new combinations and format
        self._symbol_date_combs = [{'symbol': comb[0], 'date': comb[1]} for comb in self._symbol_date_combs
                                   if comb not in existing]

    def _transform_price_data(self):
        """
        Transform the extracted price data.
        """

        print('_transform_price_data')

        price_data = self._extracted['price_data']

        # forward fill non-business days etc.
        price_data = YF.ffill_price_data(price_data).reset_index()

        # convert into long format
        molten = pd.melt(price_data, id_vars='index')
        molten.columns = ['date', 'symbol', 'price']
        molten.dropna(subset=['price'], inplace=True)

        # store price data in record format
        self._price_data = molten.to_dict('records')

        # add the symbol date combinations of the price data
        combs = [tuple(x) for x in molten.loc[:, ['symbol', 'date']].to_dict('split')['data']]

        self._symbol_date_combs = list({*self._symbol_date_combs, *combs})

    def run(self):
        """
        Run the transformation process.
        """
        self._transform_transactions()
        self._transform_product_info()
        self._build_portfolio()
        self._transform_price_data()
        self._transform_symbol_date_combs()


class Loading:

    def __init__(self, transformation_data):
        """
        :param transformation_data: data received from the transformation step. Must be a
            dictionary with keys 'transactions', 'product_info', 'price_data', 'portfolios'.
        """

        try:
            assert 'transactions' in transformation_data.keys()
            assert 'product_info' in transformation_data.keys()
            assert 'price_data' in transformation_data.keys()
            assert 'portfolios' in transformation_data.keys()
            assert 'symbol_date_combs' in transformation_data.keys()
        except AssertionError as ae:
            print('Invalid transformation_data received.')
            raise ae

        self._transformation_data = transformation_data

    def _load_transactions(self):
        """
        Load the transactions into the Transactions table.
        """
        print('_load_transactions')
        transaction_objects = [Transactions(**t) for t in self._transformation_data['transactions']]
        Transactions.objects.bulk_create(transaction_objects)

    def _load_product_info(self):
        """
        Load the product info into the Assets table.
        """
        print('_load_product_info')
        asset_objects = [Assets(**info[1]) for info in self._transformation_data['product_info'].items()]
        Assets.objects.bulk_create(asset_objects)

    def _load_symbol_date_combs(self):
        """
        Load the symbol-date-combinations into the DimensionSymbolDate table.
        """
        print('_load_symbol_date_combs')
        symbol_date_objects = [DimensionSymbolDate(**comb) for comb in self._transformation_data['symbol_date_combs']]
        DimensionSymbolDate.objects.bulk_create(symbol_date_objects)

    @staticmethod
    def _symbol_date_prep(data, retained_column):
        """
        Add the appropriate symbol_date ID to the provided data in order to make upload to Depot and Prices model
        possible (due to FK to DimensionSymbolDate).
        :param data: the data set to add the id to (should be in record form)
        :param retained_column: the other column to retain in the data set in addition to symbol_date_id
        """

        dates = [x['date'] for x in data]
        symbols = list(set([x['symbol'] for x in data]))

        existing = pd.DataFrame(DimensionSymbolDate.objects.get_existing(dates, symbols),
                                columns=['symbol_date', 'symbol', 'date'])

        data_df = pd.DataFrame(data)

        merged = pd.merge(data_df, existing, how='left')[[retained_column, 'symbol_date']]
        merged.columns = [retained_column, 'symbol_date_id']
        records = merged.to_dict('records')

        return records

    def _load_price_data(self):
        """
        Load the price data into the Prices table.
        """
        print('_load_price_data')

        records = self._symbol_date_prep(self._transformation_data['price_data'], 'price')

        price_objects = [Prices(**p) for p in records]
        Prices.objects.bulk_create(price_objects)

    def _load_portfolios(self):
        """
        Load the portfolios into the Depot table.
        """
        print('_load_portfolios')

        records = self._symbol_date_prep(self._transformation_data['portfolios'], 'pieces')

        depot_objects = [Depot(**d) for d in records]
        Depot.objects.bulk_create(depot_objects)

    def run(self):
        """
        Run the loading process.
        """
        self._load_transactions()
        self._load_product_info()
        self._load_symbol_date_combs()
        self._load_price_data()
        self._load_portfolios()

import re
from typing import Dict, List, Union

import requests
import json
import getpass
import datetime
from collections import defaultdict

from project.settings import DEGIRO


class DegiroAPI:
    def __init__(self):
        self.user = dict()
        self.data = None
        self.sess = None
        self.sess_id = None

    def login(self, with2fa: bool = False) -> None:
        """
        Login to the Degiro account.
        :param with2fa: Set to true, if 2FA is necessary for login.
        """

        self.sess = requests.Session()

        # Login
        url = 'https://trader.degiro.nl/login/secure/login'
        payload = {
            'username': DEGIRO['USERNAME'],
            'password': DEGIRO['PASSWORD'],
            'isPassCodeReset': False,
            'isRedirectToMobile': False
        }
        header = {'content-type': 'application/json'}

        if with2fa:
            payload['oneTimePassword'] = getpass.getpass("2FA Token: ")
            url += '/totp'

        r = self.sess.post(url, headers=header, data=json.dumps(payload))

        # Get session id
        self.sess_id = r.headers['Set-Cookie']
        self.sess_id = self.sess_id.split(';')[0]
        self.sess_id = self.sess_id.split('=')[1]

    # This contain loads of user data, main interest here is the 'intAccount' -> also contains personal data
    def get_config(self) -> int:
        """
        Get configuration data about the user. Some of this data is required for other methods.
        :return: HTTP Request Status code
        """
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sess_id}

        r = self.sess.get(url, params=payload)
        if r.status_code != 200:
            return r.status_code

        data = r.json()
        self.user['intAccount'] = data['data']['intAccount']
        self.user['username'] = data['data']['username']
        self.user['email'] = data['data']['email']
        self.user['firstName'] = data['data']['firstContact']['firstName']
        self.user['lastName'] = data['data']['firstContact']['lastName']
        self.user['dateOfBirth'] = data['data']['firstContact']['dateOfBirth']
        self.user['streetAddress'] = data['data']['address']['streetAddress']
        self.user['streetAddressNumber'] = data['data']['address']['streetAddressNumber']
        self.user['zip'] = data['data']['address']['zip']
        self.user['city'] = data['data']['address']['city']
        self.user['bic'] = data['data']['bankAccount']['bic']
        self.user['iban'] = data['data']['bankAccount']['iban']

        return r.status_code

    # This gets a lot of data, orders, news, portfolio, cash funds etc.
    def get_data(self) -> int:
        """
        Get lots of data (orders, news, portfolio, cash funds etc).
        :returns: HTTP status code
        """
        if len(self.user) == 0:
            self.get_config()
        url = 'https://trader.degiro.nl/trading/secure/v5/update/'
        url += str(self.user['intAccount']) + ';'
        url += 'jsessionid=' + self.sess_id
        payload = {
            'portfolio': 0,
            'totalPortfolio': 0,
            'orders': 0,
            'historicalOrders': 0,
            'transactions': 0,
            'alerts': 0,
            'cashFunds': 0,
            'intAccount': self.user['intAccount'],
            'sessionId': self.sess_id
        }

        r = self.sess.get(url, params=payload)

        if r.status_code == 200:
            self.data = r.json()

        return r.status_code

    def get_cash_funds(self) -> Dict:
        """
        Extract the cash funds from self.data.
        :returns: Dict containing the cash funds in different currencies.
        """
        if self.data is None:
            self.get_data()

        cash_funds = dict()

        for cf in self.data['cashFunds']['value']:
            entry = dict()
            for y in cf['value']:
                # Useful if the currency code is the key to the dict
                if y['name'] == 'currencyCode':
                    key = y['value']
                    continue
                entry[y['name']] = y['value']
            cash_funds[key] = entry

        return cash_funds

    def get_portfolio_summary(self) -> Dict:
        """
        Returns a summary of the portfolio.
        :returns: Portfolio summary
        """
        # todo this maybe shouldn't be in the API
        pf = self.get_portfolio()
        cf = self.get_cash_funds()
        tot = 0
        for eq in pf['PRODUCT'].values():
            tot += eq['value']

        pf_summary = dict()
        pf_summary['equity'] = tot
        pf_summary['cash'] = cf['EUR']['value']
        return pf_summary

    def get_portfolio(self) -> Dict:
        """
        Extracts portfolio from self.data and enriches it with additional information from Degiro
        :returns: Portfolio data
        """
        if self.data is None:
            self.get_data()

        portfolio = []
        for row in self.data['portfolio']['value']:
            entry = dict()
            for y in row['value']:
                k = y['name']
                v = None
                if 'value' in y:
                    v = y['value']
                entry[k] = v
            # Also historic equities are returned, let's omit them
            if entry['size'] != 0:
                portfolio.append(entry)

        # Restructure portfolio and add extra data
        portf_n = defaultdict(dict)
        # Restructuring
        for r in portfolio:
            pos_type = r['positionType']
            pid = r['id']  # Product ID
            del (r['positionType'])
            del (r['id'])
            portf_n[pos_type][pid] = r

        # Adding extra data
        url = 'https://trader.degiro.nl/product_search/secure/v5/products/info'
        params = {
            'intAccount': str(self.user['intAccount']),
            'sessionId': self.sess_id
        }
        header = {'content-type': 'application/json'}
        pid_list = list(portf_n['PRODUCT'].keys())
        r = self.sess.post(url, headers=header, params=params, data=json.dumps(pid_list))

        if r.status_code == 200:

            for k, v in r.json()['data'].items():
                del (v['id'])
                # Some bonds tend to have a non-unit size
                portf_n['PRODUCT'][k]['size'] *= v['contractSize']
                portf_n['PRODUCT'][k].update(v)

        return portf_n

    def get_account_movements(self, from_date: Union[str, datetime.datetime, datetime.date],
                              to_date: Union[str, datetime.datetime, datetime.date]) -> List[Dict]:
        """
        Get all account movements between fromDate and toDate.
        :param from_date: Date (string of format dd/mm/yyyy)
        :param to_date: Date (string of format dd/mm/yyyy)
        :return: List of dictionaries containing todo
        """
        from_date = self._get_date_string(from_date)
        to_date = self._get_date_string(to_date)

        url = 'https://trader.degiro.nl/reporting/secure/v4/accountoverview'
        payload = {
            'fromDate': from_date,
            'toDate': to_date,
            'intAccount': self.user['intAccount'],
            'sessionId': self.sess_id
        }

        r = self.sess.get(url, params=payload)

        if r.status_code != 200:
            return list()

        data = r.json()
        movs = []
        for rmov in data['data']['cashMovements']:
            mov = dict()
            # Reformat timezone part: +01:00 -> +0100
            date = ''.join(rmov['date'].rsplit(':', 1))
            date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
            mov['date'] = date
            if 'change' in rmov:
                mov['change'] = rmov['change']
            mov['currency'] = rmov['currency']
            mov['description'] = rmov['description']
            mov['type'] = rmov['type']
            if 'orderId' in rmov:
                mov['orderId'] = rmov['orderId']
            if 'productId' in rmov:
                mov['productId'] = rmov['productId']
            movs.append(mov)
        return movs

    def get_transactions(self, from_date: Union[str, datetime.datetime, datetime.date],
                         to_date: Union[str, datetime.datetime, datetime.date]) -> List[Dict]:
        """
        Get historical transactions between fromDate and toDate.
        :param from_date: Date (string of format dd/mm/yyyy)
        :param to_date: Date (string of format dd/mm/yyyy)
        :return: List of dictionaries containing
        """
        from_date = self._get_date_string(from_date)
        to_date = self._get_date_string(to_date)
        url = 'https://trader.degiro.nl/reporting/secure/v4/transactions'
        payload = {'fromDate': from_date,
                   'toDate': to_date,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sess_id}

        r = self.sess.get(url, params=payload)
        if r.status_code != 200:
            return list()

        data = r.json()['data']
        return data

    def get_transactions_clean(self, from_date: Union[str, datetime.datetime, datetime.date],
                               to_date: Union[str, datetime.datetime, datetime.date]):

        """
        Wrapper around self.get_transactions that cleans the data before returning it
        """

        transactions = self.get_transactions(from_date, to_date)

        for dic in transactions:
            regexed_date = re.compile(r'\d{4}-\d{2}-\d{2}').findall(dic['date'])[0]
            dic['date'] = datetime.datetime.strptime(regexed_date, '%Y-%m-%d').date()
            dic['productId'] = str(dic['productId'])
            dic['id'] = str(dic['id'])

        return transactions

    # Returns product info
    #  ids is a list of product ID (from DegiroAPI)
    def get_product_by_id(self, ids: List[str]) -> Dict:
        """
        Returns product info for all product Ids provided in the list.
        :param ids: List of product IDs
        :returns: Product info
        """
        url = "https://trader.degiro.nl/product_search/secure/v5/products/info"
        header = {'content-type': 'application/json'}
        params = {'intAccount': str(self.user['intAccount']), 'sessionId': self.sess_id}
        r = self.sess.post(url, headers=header, params=params, data=json.dumps([str(id) for id in ids]))

        if r.status_code != 200:
            return dict()

        try:
            data = r.json()['data']
            return data
        except KeyError:
            print('\tKeyError: No data retrieved.')
            return r.json()

    @staticmethod
    def _get_date_string(date):
        if isinstance(date, datetime.date) or isinstance(date, datetime.datetime):
            return date.strftime(format="%d/%m/%Y")
        elif isinstance(date, str):
            try:
                datetime.datetime.strptime(date, '%d/%m/%Y')
                return date
            except ValueError as ve:
                raise ve


if __name__ == '__main__':
    deg = DegiroAPI()
    deg.login(with2fa=False)

    deg.get_config()
    for i in ['15885941', '14616228', '14616228', '15885941', '15964254']:
        deg.get_product_by_id([i])

    int(0)
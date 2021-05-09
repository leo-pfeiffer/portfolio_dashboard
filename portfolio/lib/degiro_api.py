from typing import Dict, List, Union

import requests
import json
import getpass
import datetime

from project.settings import DEGIRO

import logging
import traceback

logger = logging.getLogger('db')


class DegiroAPI:
    def __init__(self):
        self.user = dict()
        self.data = None
        self.sess = None
        self.sess_id = None

    def login(self, twoFactorAuth: bool = False) -> None:
        """
        Login the user into their Degiro account.
        :param twoFactorAuth: Set to true, if 2FA is required for logging in.
        :raises: RequestException: if HTTP request fails
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

        # Make user enter 2FA Token if required
        if twoFactorAuth:
            payload['oneTimePassword'] = getpass.getpass("Enter 2FA Token: ")
            url += '/totp'

        try:
            r = self.sess.post(url, headers=header, data=json.dumps(payload))
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        # Process session ID
        self.sess_id = r.headers['Set-Cookie']
        self.sess_id = self.sess_id.split(';')[0]
        self.sess_id = self.sess_id.split('=')[1]

    def logout(self) -> None:
        """
        Logout the user from the degiro account.
        :raises: RequestException: if HTTP request fails
        """

        url = f'https://trader.degiro.nl/trading/secure/logout;jsessionid={self.sess_id}'

        try:
            self.sess.get(url)
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        # Reset user data
        self.data = None
        self.sess = None
        self.sess_id = None

    def get_config(self) -> None:
        """
        Get configuration data about the user. Method must be called before other account specific requests
        are made, since `intAccount` is used for the identification of the user's account in HTTP requests.
        :raises: RequestException: if HTTP request fails
        """

        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sess_id}

        try:
            r = self.sess.get(url, params=payload)
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        data = r.json()
        self.user['intAccount'] = data['data']['intAccount']
        self.user['username'] = data['data']['username']
        self.user['email'] = data['data']['email']
        self.user['firstName'] = data['data']['firstContact']['firstName']
        self.user['lastName'] = data['data']['firstContact']['lastName']
        self.user['streetAddress'] = data['data']['address']['streetAddress']
        self.user['streetAddressNumber'] = data['data']['address']['streetAddressNumber']
        self.user['city'] = data['data']['address']['city']
        self.user['zip'] = data['data']['address']['zip']
        self.user['dateOfBirth'] = data['data']['firstContact']['dateOfBirth']
        self.user['bic'] = data['data']['bankAccount']['bic']
        self.user['iban'] = data['data']['bankAccount']['iban']

    def get_data(self) -> None:
        """
        Fetches several data points from the API. In particular, it retrieves:
        - orders
        - historicalOrders
        - transactions
        - portfolio
        - totalPortfolio
        - alerts
        - cashFunds

        :raises: RequestException: if HTTP request fails
        """

        # Make sure get_config is called first if not done already
        if len(self.user) == 0:
            self.get_config()

        url = f"https://trader.degiro.nl/trading/secure/v5/update/{self.user['intAccount']};jsessionid={self.sess_id}"

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

        try:
            r = self.sess.get(url, params=payload)
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        self.data = r.json()

    def get_account_movements(self, from_date: Union[str, datetime.datetime, datetime.date],
                              to_date: Union[str, datetime.datetime, datetime.date]) -> List[Dict]:
        """
        Get all account movements between fromDate and toDate.
        :param from_date: Date (string of format dd/mm/yyyy)
        :param to_date: Date (string of format dd/mm/yyyy)
        :raises: RequestException: if HTTP request fails
        :return: List of dictionaries representing account movements. Movement type can be identified
          by the 'type' value in each dictionary.
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

        try:
            r = self.sess.get(url, params=payload)
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        data = r.json()

        if 'cashMovements' not in data['data']:
            return []

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
        :raises: RequestException: if HTTP request fails
        :return: List of dictionaries containing
        """
        from_date = self._get_date_string(from_date)
        to_date = self._get_date_string(to_date)
        url = 'https://trader.degiro.nl/reporting/secure/v4/transactions'
        payload = {'fromDate': from_date,
                   'toDate': to_date,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sess_id}

        try:
            r = self.sess.get(url, params=payload)
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        data = r.json()['data']
        return data

    def get_product_by_id(self, ids: List[str]) -> Dict:
        """
        Returns product info for all product Ids provided in the list.
        :param ids: List of product IDs
        :raises:
            RequestException: if HTTP request fails
            KeyError: if response does not contain any data
        :returns: Product info
        """
        url = "https://trader.degiro.nl/product_search/secure/v5/products/info"
        header = {'content-type': 'application/json'}
        params = {'intAccount': str(self.user['intAccount']), 'sessionId': self.sess_id}

        try:
            r = self.sess.post(url, headers=header, params=params, data=json.dumps([str(_id) for _id in ids]))
        except requests.exceptions.RequestException as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

        try:
            data = r.json()['data']
            return data

        # Data not retrieved
        except KeyError as e:
            logger.exception('RequestException: {} //////  Traceback: {}'.format(e, traceback.format_exc()))
            raise e

    def get_products_by_id(self, product_ids) -> Dict:
        """
        Wrapper around self.get_product_by_id that allows batch requests of up to 10 products at a time.
        :param product_ids: Unique list of product_ids
        :returns: Product info
        """

        chunks = [product_ids[i * 10:(i + 1) * 10] for i in range((len(product_ids) + 9) // 10)]

        data_out = {}

        for chunk in chunks:
            data_out = {**data_out, **self.get_product_by_id(chunk)}

        return data_out

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

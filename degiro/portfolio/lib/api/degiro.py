import requests
import json
import getpass
from datetime import datetime, date
from collections import defaultdict
from settings import paths # if used outside of django
# from .settings import paths  # if used with django


class Degiro:
    def __init__(self):
        self.user = dict()
        self.data = None
        self.sess = None
        self.sessid = None

    def login(self, conf_path=None, with2fa: bool = False):

        if (conf_path is None) | (conf_path is False) | ((type(conf_path) is not bool) & (type(conf_path) is not str)):
            conf = dict(username=input("Username: "), password=getpass.getpass())

        elif (type(conf_path) is bool) & (conf_path is True):
            conf_path = paths.SETTINGS + '/config.json'
            conf = json.load(open(conf_path))

        elif type(conf_path) is str:
            try:
                conf = json.load(open(conf_path))
            except FileNotFoundError:
                print("File not found. Please enter credentials manually.")
                conf = dict(username=input("Username: "), password=getpass.getpass())

        self.sess = requests.Session()

        # Login
        url = 'https://trader.degiro.nl/login/secure/login'
        payload = {'username': conf['username'],
                   'password': conf['password'],
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}
        header = {'content-type': 'application/json'}

        if with2fa:
            payload['oneTimePassword'] = getpass.getpass("2FA Token: ")
            url += '/totp'

        r = self.sess.post(url, headers=header, data=json.dumps(payload))

        # Get session id
        self.sessid = r.headers['Set-Cookie']
        self.sessid = self.sessid.split(';')[0]
        self.sessid = self.sessid.split('=')[1]

    # This contain loads of user data, main interest here is the 'intAccount' -> also contains personal data
    def getConfig(self):
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get config')
        print('\tStatus code: {}'.format(r.status_code))

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

    # This gets a lot of data, orders, news, portfolio, cash funds etc.
    def getData(self):
        if len(self.user) == 0:
            self.getConfig()
        url = 'https://trader.degiro.nl/trading/secure/v5/update/'
        url += str(self.user['intAccount']) + ';'
        url += 'jsessionid=' + self.sessid
        payload = {'portfolio': 0,
                   'totalPortfolio': 0,
                   'orders': 0,
                   'historicalOrders': 0,
                   'transactions': 0,
                   'alerts': 0,
                   'cashFunds': 0,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get data')
        print('\tStatus code: {}'.format(r.status_code))

        self.data = r.json()

    # Get the cash funds
    def getCashFunds(self):
        if self.data is None:
            self.getData()
        cashFunds = dict()
        for cf in self.data['cashFunds']['value']:
            entry = dict()
            for y in cf['value']:
                # Useful if the currency code is the key to the dict
                if y['name'] == 'currencyCode':
                    key = y['value']
                    continue
                entry[y['name']] = y['value']
            cashFunds[key] = entry
        return cashFunds

    # Only returns a summary of the portfolio
    def getPortfolioSummary(self):
        pf = self.getPortfolio()
        cf = self.getCashFunds()
        tot = 0
        for eq in pf['PRODUCT'].values():
            tot += eq['value']

        pfSummary = dict()
        pfSummary['equity'] = tot
        pfSummary['cash'] = cf['EUR']['value']
        return pfSummary

    # Returns the entire portfolio
    def getPortfolio(self):
        if self.data is None:
            self.getData()
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
        params = {'intAccount': str(self.user['intAccount']),
                  'sessionId': self.sessid}
        header = {'content-type': 'application/json'}
        pid_list = list(portf_n['PRODUCT'].keys())
        r = self.sess.post(url, headers=header, params=params, data=json.dumps(pid_list))
        print('\tGetting extra data')
        print('\t\tStatus code: {}'.format(r.status_code))

        for k, v in r.json()['data'].items():
            del (v['id'])
            # Some bonds tend to have a non-unit size
            portf_n['PRODUCT'][k]['size'] *= v['contractSize']
            portf_n['PRODUCT'][k].update(v)

        return portf_n

    # Returns all account transactions
    #  fromDate and toDate are strings in the format: dd/mm/yyyy
    def getAccountOverview(self, fromDate, toDate):
        url = 'https://trader.degiro.nl/reporting/secure/v4/accountoverview'
        payload = {'fromDate': fromDate,
                   'toDate': toDate,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get account overview')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()
        movs = []
        for rmov in data['data']['cashMovements']:
            mov = dict()
            # Reformat timezone part: +01:00 -> +0100
            date = ''.join(rmov['date'].rsplit(':', 1))
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z')
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

    # Returns historical transactions
    #  fromDate and toDate are strings in the format: dd/mm/yyyy
    def getTransactions(self, fromDate, toDate):
        """Can only get chunks of size 13 ?"""
        url = 'https://trader.degiro.nl/reporting/secure/v4/transactions'
        payload = {'fromDate': fromDate,
                   'toDate': toDate,
                   'intAccount': self.user['intAccount'],
                   'sessionId': self.sessid}

        r = self.sess.get(url, params=payload)
        print('Get Transactions overview')
        print('\tStatus code: {}'.format(r.status_code))

        data = r.json()['data']
        return data

    # Returns product info 
    #  ids is a list of product ID (from Degiro)
    def getProductByIds(self, ids):
        url = "https://trader.degiro.nl/product_search/secure/v5/products/info"
        header = {'content-type': 'application/json'}
        params = {'intAccount': str(self.user['intAccount']), 'sessionId': self.sessid}
        r = self.sess.post(url, headers=header, params=params, data=json.dumps([str(id) for id in ids]))

        print(f'Get Products info for {ids}')
        print('\tStatus code: {}'.format(r.status_code))

        try:
            data = r.json()['data']
            return data
        except KeyError:
            print('\tKeyError: No data retrieved.')
            return r.json()


if __name__ == '__main__':
    deg = Degiro()
    deg.login(conf_path=True, with2fa=False)

    # create portfolio dataframe:
    # df = pd.DataFrame(dict['PRODUCT'])
    # df.columns = df.loc['isin',:].values

    # deg.getConfig()
    # data = deg.getTransactions(fromDate=date(2020, 6, 1).strftime(format="%d/%m/%Y"),
    #                            toDate=date.today().strftime(format="%d/%m/%Y"))
    # symbols = [x['productId'] for x in data]
    # symbols_chunks = [symbols[i * 10:(i+1) * 10] for i in range((len(symbols) + 9) // 10)]
    #
    # product_ids = []
    # for chunk in symbols_chunks:
    #     dict_out = deg.getProductByIds(chunk)
    #     product_ids.append([x['symbol'] for x in dict_out])
    #
    # product = deg.getProductByIds(symbols)
    deg.getConfig()
    for i in ['15885941', '14616228', '14616228', '15885941', '15964254']:
        print(i)
        deg.getProductByIds(i)

    int(0)

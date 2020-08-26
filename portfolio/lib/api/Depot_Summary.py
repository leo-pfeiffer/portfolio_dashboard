from degiro import Degiro
import pandas as pd
la = Degiro()
la.login(with2fa=False, conf_path=True)
la.getConfig()
pfs = la.getPortfolioSummary()
portfolio = la.getPortfolio()
total = pfs['equity']

# Prints a pretty table of your equities and their allocation.
print('{:<20}\tsize\tvalue\tsubtot\t\talloc'.format('Product'))
for row in portfolio['PRODUCT'].values():
    subtot = row['size']*row['price']
    alloc = (subtot/total)*100  # Asset allocation (%)
    print('{:<20}\t{:5.1f}\t{:6.2f}\t{:7.2f}\t\t{:2.1f}%'.format(row['name'], row['size'], row['price'], subtot, alloc))
print('Total: {:.2f}'.format(total))

symbols = [x['symbol'] for x in portfolio['PRODUCT'].values()]
size = [x['size'] for x in portfolio['PRODUCT'].values()]
price = [x['price'] for x in portfolio['PRODUCT'].values()]
subtot = [x['size']*x['price'] for x in portfolio['PRODUCT'].values()]
alloc = [x/total for x in subtot]

df = pd.DataFrame([size, price, subtot, alloc]).T
df.index = symbols
df.columns = ['Size', 'Price', 'Subtotal', 'Allocation']
int(0)

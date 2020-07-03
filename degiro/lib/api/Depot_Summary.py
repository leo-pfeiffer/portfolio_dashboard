from degiro import degiro

la = degiro()
la.login(with2fa=False)
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

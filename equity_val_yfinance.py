# https://github.com/farhadab/sec-edgar-financials

import yfinance as yf
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import asyncio
from pyppeteer import launch
import numpy as np
import requests
from bs4 import BeautifulSoup
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
# import equity_val_edgar as evedgar

stock = "WMG"

ticker = yf.Ticker(stock)
info = ticker.info
industry = info.get('industry')
industryKey = info.get('industryKey')
exchange = info.get('exchange')
# exchange = evedgar.financialdata['dei:SecurityExchangeName']['#text'] # Use fuzzywuzzy to find most similar document name to SecurityExchangeName

history = ticker.history(period="3y")
closing_prices = history['Close']
returns = closing_prices.pct_change()
variance_returns = np.var(returns.dropna().values)

fiscal_year = {'income_statements' : ticker.financials,
               'balance_sheets' : ticker.balance_sheet,
               'cash_flows' : ticker.cashflow}

quarterly = {'income_statements' : ticker.quarterly_financials,
               'balance_sheets' : ticker.quarterly_balance_sheet,
               'cash_flows' : ticker.quarterly_cashflow}

print ('\nFiscal Year')
print('______________\n')
print(fiscal_year['income_statements'])
print('')
print(fiscal_year['balance_sheets'])
print('')
print(fiscal_year['cash_flows'])
print('')

print ('\nQuarterly')
print('______________\n')
print('\nIncome Statements')
print(quarterly['income_statements'])
print('\nBalance Sheets')
print(quarterly['balance_sheets'])
print('\nCash Flows')
print(quarterly['cash_flows'])
print('')

revenues = ''
operating_income = ''
bv_equity = ''
bv_debt = ''
operating_lease = True
cash_and_cross_holdings = ''
non_operating_assets = ''
minority_interests = ''
shares_outstanding = '' 
current_stock_price = ''
effective_tax_rate = ''
marginal_tax_rate = ''
cagr_4yr = ''
target_pretax_operating_margin = ''
sales_to_capital_ratio = ''
risk_free_rate = '' # find this by understanding which countries the business operates in as well as these countries' country risks. #us-gaap/SegmentReportingDisclosureTextBlock
initial_cost_of_capital = ''
employee_options = {
    'outstanding' : '',
    'avg_strike_price' : '',
    'avg_maturity' : '',
    'std_dev_stock_price' : ''
                    }

# us-gaap:RevenueFromContractWithCustomerTextBlock.html
# us-gaap:ScheduleOfDebtInstrumentsTextBlock.html
# SegmentReportingDisclosureTextBlock.html
# us-gaap:DisaggregationOfRevenueTableTextBlock

print('\nBalance Sheets')
print(quarterly['balance_sheets'].index)
print('\nIncome Statements')
print(quarterly['income_statements'].index)
print('\nCash Flows')
print(quarterly['cash_flows'].index)
print()

# print(quarterly['income_statements'].loc['Total Revenue'])

# Use fuzzy wuzzy to match line items to line items
# quarterly_input_data = {
#     'industry' : industry,
#     'total_revenue' : quarterly['income_statements'].loc['Total Revenue'],
#     'operating_income' : quarterly['income_statements'].loc['Operating Income'],
#     'bv_equity' : quarterly['balance_sheets'].loc['Stockholders Equity'],
#     'bv_debt' : quarterly['balance_sheets'].loc['Total Debt'], # Total Debt for security. More often than not, net debt is not listed.
#     'operating_lease_commitments' : 'yes',
#     'cash_and_cross_holdings' : (), # might need to use SEC data
#     'non_operating_assets' : None,
#     'minority_interests' : None,
#     'shares_outstanding' : None,
#     'current_stock_price' : None,
#     'effective_tax_rate' : None,
#     'marginal_tax_rate' : None,
#     'cagr_5yr' : None,
#     'target_pretax_operating_margin' : None,
#     'sales_to_capital_ratio' : None,
#     'risk_free_rate' : None,
#     'initial_cost_of_capital' : None,
#     'employee_options' : {
#         'status' : False,
#         'options_outstanding' : None,
#         'avg_strike_price' : None,
#         'avg_maturity' : None
#         },
#     'stock_price_std_dev' : None
#     }

# print(quarterly_input_data['total_revenue'])
# https://www.alphavantage.co/documentation/

# april presentation of AswathGPT
# Volatility and Risk Institute — AI conference with Vasant Dhar

print(info)

print(exchange)

us_exchange_codes = {
    'NYQ' : ['NYSE', '^NYA'],
    'NMS' : ['NASDAQ Global Market Select', '^IXIC'],
    'NGM' : ['NASDAQ Global Market', '^IXIC'],
    'NCM' : ['NASDAQ Capital Market', '^IXIC'],
    'ASE' : ['NYSE American', '^XAX'], #NYSE American
} # https://www.sec.gov/files/company_tickers_exchange.json

market_index = str(us_exchange_codes[exchange][1])
market_ticker = yf.Ticker(market_index)
market_info = market_ticker.info

market_history = market_ticker.history(period="3y")
market_closing_prices = market_history['Close']
market_history['Returns'] = market_history['Close'].pct_change().dropna()
market_returns = market_closing_prices.pct_change().dropna()

covariance = np.cov(market_returns.dropna().values, returns.dropna().values)[0, 1]

levered_beta = covariance/variance_returns

print("Beta: " + str(levered_beta))

# best way to do this is to get the 

# https://github.com/ranaroussi/yfinance Smart cache



# To do:
# 1. Input data retrieval
#    a. Use fuzzy wuzzy to match yfinance line items to the input data we want
#    b. Make a data frame of all the financial data you need
#    c. Retrieve financial data from EDGAR and input it into the data frame
# 2. 
# 3. 
def get_bond_data():
    bonds_url = 'https://www.worldgovernmentbonds.com/'
    bd_resp = requests.get(bonds_url)
    soup = BeautifulSoup(bd_resp.content, 'html.parser')
    bond_table = soup.find('table', {'class' : 'homeBondTable sortable w3-table money pd44 -f14'})
    bond_file = open('/Users/maxbushala/Downloads/bond_data.txt', 'w')
    bond_file.write(str(bond_table.prettify()))
    bond_file.close()
    bond_data = []
    for row in bond_table.find_all('tr'):
        row_data = []
        for cell in row.find_all('td'):
            row_data.append(cell.text)
        bond_data.append(row_data)
    bd_df = pd.DataFrame(bond_data).replace(r'\n|\t','',regex=True).replace('None', pd.NA)
    bd_df.drop(bd_df.columns[0],axis=1, inplace=True)
    bd_df = bd_df.drop([0,1])
    bd_df = bd_df[:-1]
    bd_df.columns = ['Country', 'S&P Rating', '10yr Bond Yield', 'Empty', 'Bank Rate', 'Spread vs Bund', 'Spread vs T-Note', 'Spread vs Bank Rate']
    bd_df = bd_df.replace(r"^ +| +$", r"", regex=True)
    bd_df['10yr Bond Yield'] = bd_df['10yr Bond Yield'].str.rstrip('%').astype('float')/100
    bd_df.drop('Empty', axis=1, inplace = True)
    return bd_df

bond_data = get_bond_data()

bond_data.style

# print(bond_data.iloc[0]['10yr Bond Yield'])

def print_bond_yields():
    print("10yr Bond Yield:")
    for i in range(len(bond_data)):
        print(f"{bond_data.iloc[i]['Country']}: {bond_data.iloc[i]['10yr Bond Yield']}")
    return None

def display_graphs():
    plt.figure(figsize=(12,8))

    # Plot the closing prices
    plt.subplot(2,2,1)  # Set the figure size for better readability
    closing_prices.plot(title=f"{str(stock)} Closing Prices Over the Last 3 Years")
    plt.ylabel('Closing Price')
    plt.grid(True)

    # Plot the closing prices
    plt.subplot(2,2,2)  # Set the figure size for better readability
    market_closing_prices.plot(title=f"{market_index} Closing Prices Over the Last 3 Years")
    plt.ylabel('Closing Price')
    plt.grid(True)

    # Plot the closing prices
    plt.subplot(2,2,3)  # Set the figure size for better readability
    returns.plot(title=f"{str(stock)} Returns Over the Last 3 Years")
    plt.ylabel('Return')
    plt.grid(True)

    # Plot the closing prices
    plt.subplot(2,2,4)  # Set the figure size for better readability
    market_returns.plot(title=f"{market_index} Returns Over the Last 3 Years")
    plt.ylabel('Return')
    plt.grid(True)

    plt.tight_layout()
    plt.show()
    return None

# print(bond_data)

# display_graphs()

us_bond_yield = bond_data.loc[bond_data['Country'] == 'United States', '10yr Bond Yield'].values[0]

def default_spread():
    bond_data['Spread'] = bond_data['10yr Bond Yield'] - us_bond_yield
    return bond_data

spread_table = default_spread()[['Country', '10yr Bond Yield', 'Spread']]

print(spread_table)
# https://www.spglobal.com/ratings/en/research/articles/190807-sovereign-ratings-list-11099434

# '/Users/maxbushala/Documents/Screenshots/Screenshot 2024-03-10 at 4.11.04 AM.png'

# https://pages.stern.nyu.edu/~adamodar/pdfiles/cfovhds/Riskfree&spread.pdf

# https://pages.stern.nyu.edu/~adamodar/podcasts/valspr22/session5slides.pdf

def expected_market_return():
    erm = np.average(market_history['Returns'].dropna())
    return erm

erm = expected_market_return()

us_mature_erp = erm - us_bond_yield

print(us_mature_erp)


# look at ValUGQuiz1aSpr24soln
# next step is to get all the revenues by country, calculate the weights of each country's revenues
# country risk premium = default spread * (equity volatility/bond volatility)
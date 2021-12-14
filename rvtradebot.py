import numpy as np
import pandas as pd
import xlsxwriter
import requests
import math
from scipy import stats
from statistics import mean

stocks = pd.read_csv('E:\CODING\TradeBot Project\sp_500_stocks.csv')
from secrets import IEX_CLOUD_API_TOKEN

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
symbol_groups=list(chunks(stocks['Ticker'],100))
symbol_strings=[]
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

rv_columns = [
    'Ticker',
    'Price',
    'Number of Shares to Buy', 
    'Price-to-Earnings Ratio',
    'PE Percentile',
    'Price-to-Book Ratio',
    'PB Percentile',
    'Price-to-Sales Ratio',
    'PS Percentile',
    'EV/EBITDA',
    'EV/EBITDA Percentile',
    'EV/GP',
    'EV/GP Percentile',
    'RV Score'
]

rv_dataframe = pd.DataFrame(columns = rv_columns)
for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
    data=requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(","):
    #symbol='AAL'
        pe_ratio = data[symbol]['quote']['peRatio']
        # P/B Ratio
        pb_ratio = data[symbol]['advanced-stats']['priceToBook']
        #P/S Ratio
        ps_ratio = data[symbol]['advanced-stats']['priceToSales']
        # EV/EBITDA
        enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
        ebitda = data[symbol]['advanced-stats']['EBITDA']
        try:
            ev_to_ebitda = enterprise_value/ebitda
        except TypeError:
            ev_to_ebitda = np.nan    
        # EV/GP
        gross_profit = data[symbol]['advanced-stats']['grossProfit']
        try:
            ev_to_gross_profit = enterprise_value/gross_profit
        except TypeError:
            ev_to_gross_profit=np.nan

        rv_dataframe=rv_dataframe.append(
        pd.Series(      
        [
            symbol,
            data[symbol]['quote']['latestPrice'],
            'N/A',
            pe_ratio,
            'n/a',
            pb_ratio,
            'n/a',
            ps_ratio,
            'n/a',
            ev_to_ebitda,
            'n/a',
            ev_to_gross_profit,
            'n/a', 
            'n/a'
        ],
        index=rv_columns),
        ignore_index=True
        )
for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio','Price-to-Sales Ratio',  'EV/EBITDA','EV/GP']:
    rv_dataframe.fillna(rv_dataframe[column].mean(), inplace = True)

metrics={ 
    'Price-to-Earnings Ratio' : 'PE Percentile',
    'Price-to-Book Ratio' : 'PB Percentile',
    'Price-to-Sales Ratio' : 'PS Percentile',
    'EV/EBITDA' : 'EV/EBITDA Percentile',
    'EV/GP' : 'EV/GP Percentile'
    }

for metric in metrics.keys():
    for row in rv_dataframe.index:
        rv_dataframe.loc[row, metrics[metric]]=stats.percentileofscore(rv_dataframe[metric], rv_dataframe.loc[row,metric])

for row in rv_dataframe.index:
    percentiles=[]
    for metric in metrics.values():
        percentiles.append(rv_dataframe.loc[row, metric]) 
    rv_dataframe.loc[row, 'RV Score']=mean(percentiles)

rv_dataframe.sort_values(by='RV Score', inplace=True)
rv_dataframe=rv_dataframe[:50]
rv_dataframe.reset_index(drop=True, inplace = True)
#print(rv_dataframe)

def portfolio_input():
    global portfolio_size
    portfolio_size=input("Please enter the value of your portfolio: ")
    try:
        float(portfolio_size)
    except ValueError:
        print("Sorry,Please enter your portfolio size in digits! ")
        portfolio_size=input("Please enter the value of your portfolio: ")

portfolio_input()
position_size=float(portfolio_size)/len(rv_dataframe.index)
for row in rv_dataframe.index:
    rv_dataframe.loc[row, 'Number of Shares to Buy']=math.floor(position_size/rv_dataframe.loc[row,'Price']) 
#print(rv_dataframe)

writer = pd.ExcelWriter('value_strategy.xlsx', engine='xlsxwriter')
rv_dataframe.to_excel(writer, sheet_name='Value Strategy', index = False)
writer.save()





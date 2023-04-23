from datetime import date, timedelta
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoLatestTradeRequest, StockLatestTradeRequest, StockLatestBarRequest, StockTradesRequest
from alpaca.data.enums import DataFeed
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Calendar
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
from datetime import datetime, timezone, time, timedelta, date
import pytz
from rich import print
import os
from icecream import install, ic
install()
import os
# print('Get current working directory : ', os.getcwd())
# print('File name :    ', os.path.basename(__file__))
# print('Directory Name:     ', os.path.dirname(__file__))

#práce s datumy

zone_NY = pytz.timezone('America/New_York')

symbol = "BAC"
client = TradingClient(API_KEY, SECRET_KEY, raw_data=False)
datetime_object_from = datetime(2023, 3, 16, 17, 51, 38, tzinfo=timezone.utc)
datetime_object_to = datetime(2023, 3, 22, 17, 52, 39, tzinfo=timezone.utc)
calendar_request = GetCalendarRequest(start=datetime_object_from,end=datetime_object_to)
cal_dates = client.get_calendar(calendar_request)
#curr_dir =  os.path.dirname(__file__)

#backtesting a obecne prace startegie s dnem
#zatim podporime pouze main session

#backtest
#- market open trade - Q 
#- market close trade - M

#minimalni jednotka pro CACHE je 1 den - a to jen marketopen to marketclose (extended hours not supported yet)
for day in cal_dates:
    print("Processing DAY", day.date)
    print(day.date)
    print(day.open)
    print(day.close)

    #get file name
    daily_file = str(symbol) + '-' + str(int(day.open.timestamp())) + '-' + str(int(day.close.timestamp())) + '.cache'
    print(daily_file)


    if os.path.exists(daily_file):
        pass
        ##denní file existuje
        #loadujeme ze souboru
        #pokud je start_time < trade < end_time
            #odesíláme do queue
            #jinak pass
    else:
        ##"cache not exists")
        #denni file není - loadujeme den z Alpacy
        #ukládáme do cache s daily_file jako název
            #pokud jde o dnešní den a nebyl konec trhu tak cache neukládáme
        if datetime.now() < day.close:
            print("not saving the cache, market still open today")
            #ic(datetime.now())
            #ic(day.close)
        else:
            pass
            #save to daily cache file curr_dir+'/'+daily_file

        #pokud je    start_time < trade < end_time
            #odesíláme do queue
            #jinak ne

    print("Processing DAY END",day.date)

# start_date = date(2008, 8, 15) 
# end_date = date(2008, 9, 15)    # perhaps date.now()
# ##get number of days between days
# delta = end_date - start_date   # returns timedelta

# for i in range(delta.days + 1):
#     day = start_date + timedelta(days=i)
#     print(day)

#     #pro kazde datum volame get cala - jestli byl trader date
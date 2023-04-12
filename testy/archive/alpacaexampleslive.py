# použití websocket loaderu v samostatném threadu
# v dalsim threadu pak input a cteni globalniho dataframu
# a stopnutí websocket loopu

#import clients
from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.data.enums import DataFeed
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE
from datetime import datetime
import pandas as pd
import threading


# pripadne parametry pro request
# parametry = {
#   "brand": "Ford",
#   "model": "Mustang",
#   "year": 1964
# }

sloupce=["timestamp","price","size","condition"]
sloupce_q=["timestamp","ask_size","ask_price","bid_price","bid_ask"]

# deklarace globalniho df s timeindexem
gdf = pd.DataFrame(columns=sloupce, index=pd.to_datetime([]))
gdf_q = pd.DataFrame(columns=sloupce_q, index=pd.to_datetime([]))


# # pro komunikaci mezi thready budeme pouzivat globalni variable
# # pro zamezeni race condition pouzijeme mutual lock (mutex)
# create a lock
# lock = threading.Lock()
# with lock:
# 	# add to the variable
# 	variable = variable + 10
# # release the lock automatically

prev_timestamp = "new"
batch = []
batch_q = []
seconds_list = []
parametry = {}
now = datetime.now() # current date and time aware of timezones
now = now.astimezone()

# client musi byt globalni, aby ho druhy thread dokazal stopnout
#client = StockDataStream(API_KEY, SECRET_KEY, raw_data=False, websocket_params=parametry, feed=DataFeed.SIP)
client = StockDataStream(API_KEY, SECRET_KEY, raw_data=True, websocket_params=parametry, feed=DataFeed.SIP)



## thread pro cteni websocketu a plneni glob.dataframu
# pozdeji prepsat do samostatne Class WSReader
def ws_reader():
    print("vstup do threadu ws reader")

    #handler pro ws trader data
    async def data_handler(data):
        global gdf
        global batch
        #record_list = (data.timestamp, data.open,data.high,data.low,data.close)
        #batch.append(record_list)
        print(data)

        # kazdou davku pak zapiseme do datasetu
        if len(batch) == MAX_BATCH_SIZE:
            ## z aktualniho listu batch udelame DataFrame
            new_df = pd.DataFrame.from_records(data=batch, columns = sloupce)

            ## tento dataframe pridame ke globalnimu
            gdf = pd.concat([gdf,new_df], axis=0, ignore_index=True)
            batch = []
            #print(gdf)

    #handler pro ws quote data
    async def data_handler_q(data):
        global gdf_q
        global batch_q
        global prev_timestamp
        global seconds_list
        record_list = (data.timestamp, data.ask_size,data.ask_price,data.bid_price,data.bid_size)

        batch_q.append(record_list)
        #print(data.ask_size,data.ask_price,data.bid_price,data.bid_size)
        #print("sestaveni je",sestaveni, "\\n batch ma ", len(batch), "clenu")
        print(batch_q)

        ##max a min hodnota z druhych hodnot listu
        def max_value(inputlist):
            return max([sublist[1] for sublist in inputlist])
        def min_value(inputlist):
            return min([sublist[1] for sublist in inputlist])
        def sum_value(inputlist):
            for sublist in inputlist: print(sublist[-1])
            return sum([sublist[-1] for sublist in inputlist])

        #pokud jde o stejnou vterinu nebo o prvni zaznam, pridame do pole
        if (prev_timestamp=="new") or (data.timestamp.second==prev_timestamp.second):
            print("stejna vterina")
            seconds_list.append([data.timestamp, data.ask_price, data.ask_size])
            #print("po appendu",seconds_list)
        else:
            print("nova vterina")
            # dopocitame ohlc
            print("max", max_value(seconds_list), "min ", min_value(seconds_list), "sum", sum_value(seconds_list), "open", seconds_list[0][1], "close", seconds_list[-1][1])
            print("-"*40)
            seconds_list = []
            seconds_list.append([data.timestamp, data.ask_price, data.ask_size])
            print(seconds_list)
            #vypisu z listu

        print("akt.cas",data.timestamp,"minuly cas", prev_timestamp)    

        prev_timestamp = data.timestamp

        # kazdou davku pak zapiseme do datasetu
        if len(batch_q) == MAX_BATCH_SIZE:
            ## z aktualniho listu batch udelame DataFrame
            new_df = pd.DataFrame.from_records(data=batch_q, columns = sloupce_q)

            ## tento dataframe pridame ke globalnimu
            gdf_q = pd.concat([gdf_q,new_df], axis=0, ignore_index=True)
            batch_q = []
            #print(gdf)t

    #client.subscribe_quotes(data_handler, "BAC")
    #client.subscribe_trades(data_handler, "BAC")
    #client.subscribe_updated_bars(data_handler, "BAC")

    ## taddy to ceka a bezi
    print("spoustim run")
    client.run()
    print("run skoncil")


def user_prompt():
    print("Tady je druhy thread, kde muzu delat co chci, pripadne ovladat ws loader")
    while True:
        delej = input("Vypsat dataframe: [t-trades;q-quotes;e-exit]")
        if delej == "t": print(gdf)
        elif delej =="q": print(gdf_q.tail(20))
        elif delej =="e": break
    print("bye")
    client.stop()

def main():
    # definujeme thready
    t1 = threading.Thread(target=ws_reader)
    #t2 = threading.Thread(target=user_prompt)

    #spustime thready
    t1.start()#, t2.start()

    # Wait threads to complete
    t1.join()#, t2.join()

if __name__ == "__main__":
    main()


    # tbd jeste si vyzkouset, zda to bez threadu nepujde takto s asynciem
    # if __name__ == '__main__':
    # logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
    #                     level=logging.INFO)

    # logging.log(logging.INFO, 'Starting up...')
    # try:
    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(main())
    #     loop.close()
    # except KeyboardInterrupt:
    #     pass
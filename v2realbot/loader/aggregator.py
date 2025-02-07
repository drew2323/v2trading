"""
    Aggregator mdoule containing main aggregator logic for TRADES, BARS and CBAR
"""
from v2realbot.enums.enums import RecordType, StartBarAlign
from datetime import datetime, timedelta
from v2realbot.utils.utils import parse_alpaca_timestamp, ltp, Queue,is_open_hours,zoneNY, zoneUTC
from queue import Queue
from rich import print
from v2realbot.enums.enums import Mode
import threading
from copy import deepcopy
from msgpack import unpackb
import os
from v2realbot.config import AGG_CACHE
import dill
import gzip
import v2realbot.utils.config_handler as cfh

class TradeAggregator:
    lock = threading.Lock()   
    def __init__(self,
                 rectype: RecordType = RecordType.BAR,
                 resolution: int = 5,
                 minsize: int = 100,
                 update_ltp: bool = False,
                 align: StartBarAlign = StartBarAlign.ROUND,
                 mintick: int = 0,
                 exthours: bool = False,
                 excludes: list = cfh.config_handler.get_val('AGG_EXCLUDED_TRADES'),
                 skip_cache: bool = False):
        """
        UPDATED VERSION - vrací více záznamů

        Create trade agregator. Instance accepts trades one by one and process them and returns output type
            Trade - return trade one by one (no change)
            Bar - return finished bar in given resolution
            CBar - returns continuous bar, finished bar is marked by confirmed status
        Args:
            resolution (number): Resolution of bar in seconds
            update_ltp (bool): Whether to update global variable with price (usually only one instance does that)
            align: Defines alignement of first bar. ROUND - according to resolution( 5,10,15 - for 5s resolution), RANDOM - according to timestamp of first trade
            mintick: Applies for CBAR. Minimální mezera po potvrzeni baru a aktualizaci dalsiho nepotvrzeneho (např. pro 15s, muzeme chtit prvni tick po 5s). po teto dobe realtime.
        """
        self.rectype: RecordType = rectype
        self.resolution = resolution
        self.minsize = minsize
        self.update_ltp = update_ltp
        self.exthours = exthours
        self.excludes = excludes
        self.skip_cache = skip_cache

        if resolution > 0 and mintick >= resolution:
            print("Mintick musi byt mensi nez resolution")
            raise Exception

        self.mintick = mintick
        #class variables = starters
        self.iterace  = 1
        self.lasttimestamp = 0
        #inicalizace pro prvni agregaci
        self.newBar = dict(high=0, low=999999, volume = 0, trades = 0, confirmed = 0, vwap = 0, close=0, index = 1, updated = 0)
        self.openedBar = None
        self.lastConfirmedTime = 0
        self.bar_start = 0
        self.curr_bar_volume = None
        self.current_bar_open = None

        self.align = align
        self.tm: datetime = None
        self.firstpass = True
        self.vwaphelper = 0
        self.returnBar = {}
        self.lastBarConfirmed = False
        self.lastConfirmedBar = None
        self.lasthigh = None
        self.lastlow = None
        #min trade size
        self.minsize = minsize
    
        #instance variable to hold last trade price
        self.last_price = 0
        self.barindex = 1
        self.diff_price = True
        self.preconfBar = {}
        self.trades_too_close = False
        self.cached_object = None
        self.cache_output_enabled = False
        self.cache_from = None
        self.cache_to = None

    async def ingest_trade(self, indata, symbol):
        """
        Aggregator logic for trade record
        Args:
            indata (dict): online or offline record
        """
        data = unpackb(indata)

        #last item signal
        if data == "last": return [data]

        #print(data)
        ##implementing fitlers - zatim natvrdo a jen tyto: size: 1, cond in [O,C,4] opening,closed a derivately priced,
        ## 22.3. - dal jsem pryc i contingency trades [' ', '7', 'V'] - nasel jsem obchod o 30c mimo
        ## dán pryč P - prior reference time + 25centu mimo, {'t': '2023-04-12T19:45:08.63257344Z', 'x': 'D', 'p': 28.68, 's': 1000, 'c': [' ', 'P'], 'i': 71693108525109, 'z': 'A'},
        ## Q - jsou v pohode, oteviraci trady, ale O jsou jejich duplikaty
        ## přidán W - average price trade, U - Extended hours - sold out of sequence, Z - Sold(Out of sequence)
        try:
            for i in data['c']:
                if i in self.excludes: return []
        except KeyError:
            pass

        #EXPERIMENT zkusime vyhodit vsechny pod 50 #puv if int(data['s']) == 1: return []
        #zatim nechavame - výsledek je naprosto stejný jako v tradingview
        if int(data['s']) < self.minsize: return []
        #{'t': 1678982075.242897, 'x': 'D', 'p': 29.1333, 's': 18000, 'c': [' ', '7', 'V'], 'i': 79372107591749, 'z': 'A', 'u': 'incorrect'}
        if 'u' in data: return []

        #pokud projde TRADE s cenou 0.33% rozdilna oproti predchozi, pak vyhazujeme v ramci cisteni dat (cca 10ticku na 30USD)
        pct_off = 0.33
        ##ic(ltp.price)
        ##ic(ltp.price[symbol])
        
        try:
            ltp.price[symbol]
        except KeyError:
            ltp.price[symbol]=data['p']

        #DOCASNE VYPNUTO - VYMYSLET JINAK
        #if float(data['p']) > float(ltp.price[symbol]) + (float(data['p'])/100*pct_off) or float(data['p']) < float(ltp.price[symbol])-(float(data['p'])/100*pct_off):
            #print("ZLO", data,ltp.price[symbol])
            #nechavame zlo zatim projit
            ##return []
            # with open("cache/wrongtrades.txt", 'a') as fp:
            #     fp.write(str(data) + 'predchozi:'+str(ltp.price[symbol])+'\n')        

        #timestampy jsou v UTC
        #TIMESTAMP format is different for online and offline trade streams
        #offline trade
        #{'t': '2023-02-17T14:30:00.16111744Z', 'x': 'J', 'p': 35.14, 's': 20, 'c': [' ', 'F', 'I'], 'i': 52983525027938, 'z': 'A'}
        #websocket trade
        #{'T': 't', 'S': 'MSFT', 'i': 372, 'x': 'V', 'p': 264.58, 's': 25, 'c': ['@', 'I'], 'z': 'C', 't': Timestamp(seconds=1678973696, nanoseconds=67312449), 'r': Timestamp(seconds=1678973696, nanoseconds=72865209)}
        #parse alpaca timestamp

        # tzn. na offline mohu pouzit >>> datetime.fromisoformat(d).timestamp() 1676644200.161117
        #orizne sice nanosekundy ale to nevadi
        #print("tady", self.mode, data['t'])
        # if self.mode == Mode.BT:
        #     data['t'] = datetime.fromisoformat(str(data['t'])).timestamp()
        # else:
        data['t'] = parse_alpaca_timestamp(data['t'])

        if not is_open_hours(datetime.fromtimestamp(data['t'], tz=zoneUTC)) and self.exthours is False:
            #print("AGG: trade not in open hours skipping", datetime.fromtimestamp(data['t']).astimezone(zoneNY))
            return []

        #tady bude vzdycky posledni cena a posledni cas
        if self.update_ltp:
            ltp.price[symbol] = data['p']
            ltp.time[symbol] = data['t']

        #if data['p'] < self.last_price - 0.02: print("zlo:",data)

        if self.rectype == RecordType.TRADE: return [data]

        #print("agr přišel trade", datetime.fromtimestamp(data['t']),data)

        #OPIC pokud bude vadit, ze prvni bar neni kompletni - pak zapnout tuto opicarnu
        #kddyz jde o prvni iteraci a pozadujeme align, cekame na kulaty cas (pro 5s 0,5,10..)
        # if self.lasttimestamp ==0 and self.align:
        #     if self.firstpass:
        #         self.tm = datetime.fromtimestamp(data['t'])
        #         self.tm += timedelta(seconds=self.resolution)
        #         self.tm = self.tm - timedelta(seconds=self.tm.second % self.resolution,microseconds=self.tm.microsecond)
        #         self.firstpass = False
        #     print("trade: ",datetime.fromtimestamp(data['t']))
        #     print("required",self.tm)
        #     if self.tm > datetime.fromtimestamp(data['t']):
        #         return
        #     else: pass

        # if self.rectype in (RecordType.BAR, RecordType.CBAR):
        #     return await self.calculate_time_bar(data, symbol)
        
        # if self.rectype == RecordType.CBARVOLUME:
        #     return await self.calculate_volume_bar(data, symbol)
        
        # if self.rectype == RecordType.CBARVOLUME:
        #     return await self.calculate_volume_bar(data, symbol)
        
        # if self.rectype == RecordType.CBARRENKO:
        #     return await self.calculate_renko_bar(data, symbol)

        match self.rectype:
            case RecordType.BAR | RecordType.CBAR:
                return await self.calculate_time_bar(data, symbol)

            case RecordType.CBARVOLUME:
                return await self.calculate_volume_bar(data, symbol)

            case RecordType.CBARDOLLAR:
                return await self.calculate_dollar_bar(data, symbol)

            case RecordType.CBARRENKO:
                return await self.calculate_renko_bar(data, symbol)

    async def get_next_bar_open_time(self,next_trade_time: float) -> float:
        """Returns next_bar_open_time based on the last bar open time, frequency and next trade time"""
        last_bar_open_time=self.bar_start
        frequency=self.resolution
        # Calculate the difference between next_trade_time and last_bar_open_time in seconds (with float precision)
        time_diff = next_trade_time - last_bar_open_time

        # Find the largest multiple of frequency within the difference
        largest_multiple = (time_diff // frequency) * frequency

        # Calculate the timestamp of the last multiple
        next_bar_open_time = last_bar_open_time + largest_multiple
        return next_bar_open_time
    
    async def calculate_time_bar(self, data, symbol):
        #print("barstart",datetime.fromtimestamp(self.bar_start))
        #print("oriznute data z tradu", datetime.fromtimestamp(int(data['t'])))
        #print("resolution",self.resolution)
        if  int(data['t']) - self.bar_start < self.resolution:
            issamebar = True
        else:
            issamebar = False
            ##flush předchozí bar a incializace (krom prvni iterace)
            if self.lasttimestamp ==0: pass
            else:
                self.newBar['confirmed'] = 1
                self.newBar['vwap'] = self.vwaphelper / self.newBar['volume']
                
                
                #HACK pro update casu, který confirm triggeroval
                #u CBARu v confirmnutem muze byt 
                # 1) no trades (pak potvrzujeme predchozi)
                # 2) trades with same price , ktere zaroven timto flushujeme (v tomto pripade je cas updatu cas predchoziho tradu)

                # variantu vyse pozname podle nastavene self.diff_price = True (mame trady a i ulozeny cas)
                if self.rectype == RecordType.CBAR:
                    #UPDATE ať confirmace nenese zadna data, vsechny zmenena data jsou vyflusnute predtim
                    #pokud byly nejake trady
                    if self.diff_price is False:
                        #self.newBar['updated'] = self.lasttimestamp
                       
                        #TODO tady bychom nejdriv vyflushnuly nekonfirmovany bar s trady
                        #a nasladne poslali prazdny confirmacni bar
                        self.preconfBar = deepcopy(self.newBar)
                        self.preconfBar['updated'] = self.lasttimestamp
                        self.preconfBar['confirmed'] = 0
                        #pridat do promenne

                    #else:
                    #NASTY HACK pro GUI
                    #zkousime potvrzeni baru dat o chlup mensi cas nez cas noveho baru, ktery jde hned za nim
                    #gui neumi zobrazit duplicity a v RT grafu nejde upravovat zpetne
                    #zarovname na cas  baru podle timeframu(např. 5, 10, 15 ...) (ROUND)

                    #MUSIME VRATIT ZPET - ten upraveny cas způsobuje spatne plneni v BT, kdyz tento bar triggeruje nakup
                    # if self.align:
                    #     t = datetime.fromtimestamp(data['t'])
                    #     t = t - timedelta(seconds=t.second % self.resolution,microseconds=t.microsecond)
                    # #nebo pouzijeme datum tradu zaokrouhlene na vteriny (RANDOM)
                    # else:
                    #     #ulozime si jeho timestamp (odtum pocitame resolution)
                    #     t = datetime.fromtimestamp(int(data['t']))

                    # #self.newBar['updated'] = float(data['t']) - 0.001
                    # self.newBar['updated'] = datetime.timestamp(t) - 0.000001
                    self.newBar['updated'] = data['t']
                #PRO standardní BAR nechavame puvodni
                else:
                    self.newBar['updated'] = data['t']
                #ulozime datum akt.tradu pro mintick
                self.lastBarConfirmed = True
                #ukládám si předchozí (confirmed)bar k vrácení
                self.returnBar = self.newBar
                #print(self.returnBar)

                #inicializuji pro nový bar
                self.vwaphelper = 0

                # return self.newBar
                ##flush CONFIRMED bar to queue
                #self.q.put(self.newBar)
                ##TODO pridat prubezne odesilani pokud je pozadovano
                self.barindex +=1
                self.newBar =  {
                    "close": 0,
                    "high": 0,
                    "low": 99999999,
                    "volume": 0,
                    "trades": 0,
                    "hlcc4": 0,
                    "confirmed": 0,
                    "updated": 0,
                    "vwap": 0,
                    "index": self.barindex
                    }
            
        #je cena stejna od predchoziho tradu? pro nepotvrzeny cbar vracime jen pri zmene ceny  
        if self.last_price == data['p']:
            self.diff_price = False
        else:
            self.diff_price = True    
        self.last_price = data['p'] 

        if float(data['t']) - float(self.lasttimestamp) < cfh.config_handler.get_val('GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN'):
            self.trades_too_close = True
        else:
            self.trades_too_close = False

        #spočteme vwap - potřebujeme předchozí hodnoty 
        self.vwaphelper += (data['p'] * data['s'])
        self.newBar['updated'] = data['t']
        self.newBar['close'] = data['p']
        self.newBar['high'] = max(self.newBar['high'],data['p'])
        self.newBar['low'] = min(self.newBar['low'],data['p'])
        self.newBar['volume'] = self.newBar['volume'] + data['s']
        self.newBar['trades'] = self.newBar['trades'] + 1
        #pohrat si s timto round
        self.newBar['hlcc4'] = round((self.newBar['high']+self.newBar['low']+self.newBar['close']+self.newBar['close'])/4,3)

        #predchozi bar byl v jine vterine, tzn. ukladame do noveho (aktualniho) pocatecni hodnoty
        #NEW BAR POPULATION
        if (issamebar == False):
            #zaciname novy bar

            self.newBar['open'] = data['p']
            
            #SET NEW BAR OPEN TIME
            #set first bar when ROUDN
            if self.align == StartBarAlign.ROUND and self.bar_start == 0:
                t = datetime.fromtimestamp(data['t'], tz=zoneUTC)
                t = t - timedelta(seconds=t.second % self.resolution,microseconds=t.microsecond)
                self.bar_start = datetime.timestamp(t)
            #set first bar when RANDOM - current trade time (just seconds)
            elif self.align == StartBarAlign.RANDOM and self.bar_start == 0:
                t = datetime.fromtimestamp(int(data['t']), tz=zoneUTC)
                self.bar_start = int(data['t'])
            #for next iterations always align with the last bar               
            else:
                #align open bar time to the nearest multiple of resolution according to the last bar open and current trade time and freq
                self.bar_start = await self.get_next_bar_open_time(next_trade_time=data['t'])

                #ulozime si jeho timestamp (odtum pocitame resolution)
                t = datetime.fromtimestamp(self.bar_start, tz=zoneUTC)

            self.newBar['time'] = t 
            self.newBar['resolution'] = self.resolution
            self.newBar['confirmed'] = 0


        #uložíme do předchozí hodnoty (poznáme tak open a close)
        self.lasttimestamp = data['t']
        self.iterace += 1
        # print(self.iterace, data)

        #je tu maly bug pro CBAR - kdy prvni trade, který potvrzuje predchozi bar
        #odesle potvrzeni predchoziho baru a nikoliv open stávajícího, ten posle až druhý trade
        #což asi nevadí
        #OPRAVENO 


        #pokud je pripraveny, vracíme předchozí confirmed bar PLUS NOVY, který ho triggeroval. pokud bylo
        # pred confirmem nejake trady beze zmeny ceny flushujeme je take (preconfBar)
        #predchozi bar muze obsahovat zmenena data
        if len(self.returnBar) > 0:
            return_set = []
            #pridame preconfirm bar pokud je
            if len(self.preconfBar)>0:
                return_set.append(self.preconfBar)
                self.preconfBar = {}
            #pridame confirmation bar
            return_set.append(self.returnBar)
            #self.tmp = self.returnBar
            self.returnBar = []
            #doplnime prubezny vwap
            self.newBar['vwap'] = self.vwaphelper / self.newBar['volume']
            return_set.append(self.newBar)
            #TODO pridat sem podporu pro mintick jako nize, tzn. pokud je v ochrannem okne, tak novy bar nevracet
            #zatim je novy bar odesilan nehlede na mintick
            #return_set = [self.tmp, self.newBar]

            return return_set

        #pro cont bar posilame ihned (TBD vwap a min bar tick value)
        if self.rectype == RecordType.CBAR:

            #pokud je mintick nastavený a předchozí bar byl potvrzený
            if self.mintick != 0 and self.lastBarConfirmed:
               #d zacatku noveho baru musi ubehnout x sekund nez posilame updazte
                #pocatek noveho baru + Xs  musi byt vetsi nez aktualni trade              
                if (self.newBar['time'] + timedelta(seconds=self.mintick)) > datetime.fromtimestamp(data['t'], tz=zoneUTC):
                    #print("waiting for mintick")
                    return []
                else:
                    self.lastBarConfirmed = False
            
            #doplnime prubezny vwap
            self.newBar['vwap'] = self.vwaphelper / self.newBar['volume']
            #print(self.newBar)

            #pro (nepotvrzeny) cbar vracime jen pri zmene ceny

            #nevracime pokud predchozi timestamp a novy od sebe nema alespon 1 ms (vyhneme se kulometum)
            #127788.123000 127788.124000 (rozdil 0.001)


            #zkousime pustit i stejnou cenu(potrebujeme kvuli MYSELLU), ale blokoval kulomet,tzn. trady mensi nez GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN (1ms)
            #if self.diff_price is True:

            #pripadne jeste vratit jako subpodminkiu
            if self.trades_too_close is False:
                return [self.newBar]
            else:
                return []
        else:
            return []

    async def calculate_volume_bar(self, data, symbol):
        """"
        Agreguje VOLUME BARS -
        hlavni promenne 
        - self.openedBar (dict) = stavová obsahují aktivní nepotvrzený bar
        - confirmedBars (list) = nestavová obsahuje confirmnute bary, které budou na konci funkceflushnuty
        """""
        #volume_bucket = 10000 #daily MA volume z emackova na 30 deleno 50ti - dat do configu
        volume_bucket = self.resolution
        #potvrzene pripravene k vraceni
        confirmedBars = []
        #potvrdi existujici a nastavi k vraceni
        def confirm_existing():
            self.openedBar['confirmed'] = 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            self.vwaphelper = 0

            #ulozime zacatek potvrzeneho baru
            #self.lastBarConfirmed = self.openedBar['time']

            self.openedBar['updated'] = data['t']
            confirmedBars.append(deepcopy(self.openedBar))
            self.openedBar = None
            #TBD po každém potvrzení zvýšíme čas o nanosekundu (pro zobrazení v gui)
            #data['t'] = data['t'] + 0.000001
            
        #init unconfirmed - velikost bucketu kontrolovana predtim
        def initialize_unconfirmed(size):
                #inicializuji pro nový bar
                self.vwaphelper += (data['p'] * size)
                self.barindex +=1
                self.openedBar =  {
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": size,
                    "trades": 1,
                    "hlcc4": data['p'],
                    "confirmed": 0,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution":volume_bucket
                    }

        def update_unconfirmed(size):
            #spočteme vwap - potřebujeme předchozí hodnoty 
            self.vwaphelper += (data['p'] * size)
            self.openedBar['updated'] = data['t']
            self.openedBar['close'] = data['p']
            self.openedBar['high'] = max(self.openedBar['high'],data['p'])
            self.openedBar['low'] = min(self.openedBar['low'],data['p'])
            self.openedBar['volume'] = self.openedBar['volume'] + size
            self.openedBar['trades'] = self.openedBar['trades'] + 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            #pohrat si s timto round
            self.openedBar['hlcc4'] = round((self.openedBar['high']+self.openedBar['low']+self.openedBar['close']+self.openedBar['close'])/4,3)

        #init new - confirmed
        def initialize_confirmed(size):
                #ulozime zacatek potvrzeneho baru
                #self.lastBarConfirmed = datetime.fromtimestamp(data['t'])
                self.barindex +=1
                confirmedBars.append({
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": size,
                    "trades": 1,
                    "hlcc4":data['p'],
                    "confirmed": 1,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution":volume_bucket
                    })
      
        #existuje stávající bar a vejdeme se do nej
        if self.openedBar is not None and int(data['s']) + self.openedBar['volume'] < volume_bucket:
            #vejdeme se do stávajícího baru (tzn. neprekracujeme bucket)
            update_unconfirmed(int(data['s']))
            #updatujeme stávající nepotvrzeny bar
        #nevejdem se do nej nebo neexistuje predchozi bar
        else:
            #1)existuje predchozi bar - doplnime zbytkem do valikosti bucketu a nastavime confirmed
            if self.openedBar is not None:
                
                #doplnime je zbytkem
                bucket_left = volume_bucket - self.openedBar['volume']
                # - update and confirm bar
                update_unconfirmed(bucket_left)
                confirm_existing()
                
                #zbytek mnozství jde do dalsiho zpracovani
                data['s'] = int(data['s']) - bucket_left
                #nastavime cas o nanosekundu vyssi
                data['t'] = round((data['t']) + 0.000001,6)

            #2 vytvarime novy bar (bary) a vejdeme se do nej
            if int(data['s']) < volume_bucket:
                #vytvarime novy nepotvrzeny bar
                initialize_unconfirmed(int(data['s']))
            #nevejdeme se do nej - pak vytvarime 1 až N dalsich baru (posledni nepotvrzený)           
            else:
            # >>> for i in range(0, 550, 500):
            # ...     print(i)
            # ... 
            # 0
            # 500

                #vytvarime plne potvrzene buckety (kolik se jich plne vejde)
                for size in range(volume_bucket, int(data['s']), volume_bucket):
                    initialize_confirmed(volume_bucket)
                    #nastavime cas o nanosekundu vyssi
                    data['t'] = round((data['t']) + 0.000001,6)
                    #create complete full bucket with same prices and size
                    #naplnit do return pole
                
                #pokud je zbytek vytvorime z nej nepotvrzeny bar
                zbytek = int(data['s']) % volume_bucket
                
                #ze zbytku vytvorime nepotvrzeny bar
                if zbytek > 0:
                    initialize_unconfirmed(zbytek)
                    #create new open bar with size zbytek s otevrenym

        #je cena stejna od predchoziho tradu? pro nepotvrzeny cbar vracime jen pri zmene ceny  
        if self.last_price == data['p']:
            self.diff_price = False
        else:
            self.diff_price = True    
        self.last_price = data['p'] 

        if float(data['t']) - float(self.lasttimestamp) < cfh.config_handler.get_val('GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN'):
            self.trades_too_close = True
        else:
            self.trades_too_close = False

        #uložíme do předchozí hodnoty (poznáme tak open a close)
        self.lasttimestamp = data['t']
        self.iterace += 1
        # print(self.iterace, data)

        #pokud mame confirm bary, tak FLUSHNEME confirm a i případný open (zrejme se pak nejaky vytvoril)
        if len(confirmedBars) > 0:
            return_set = confirmedBars + ([self.openedBar] if self.openedBar is not None else [])
            confirmedBars = []
            return return_set

        #nemame confirm, FLUSHUJEME CBARVOLUME open - neresime zmenu ceny, ale neposilame kulomet (pokud nam nevytvari conf. bar)
        if self.openedBar is not None and self.rectype == RecordType.CBARVOLUME:
            
             #zkousime pustit i stejnou cenu(potrebujeme kvuli MYSELLU), ale blokoval kulomet,tzn. trady mensi nez GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN (1ms)
            #if self.diff_price is True:
            if self.trades_too_close is False:
                return [self.openedBar]
            else:
                return []
        else:
            return []

    #WIP - revidovant kod a otestovat
    async def calculate_dollar_bar(self, data, symbol):
        """"
        Agreguje DOLLAR BARS -
        hlavni promenne 
        - self.openedBar (dict) = stavová obsahují aktivní nepotvrzený bar
        - confirmedBars (list) = nestavová obsahuje confirmnute bary, které budou na konci funkceflushnuty
        """""
        #volume_bucket = 10000 #daily MA volume z emackova na 30 deleno 50ti - dat do configu
        dollar_bucket = self.resolution
        #potvrzene pripravene k vraceni
        confirmedBars = []
        #potvrdi existujici a nastavi k vraceni
        def confirm_existing():
            self.openedBar['confirmed'] = 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            self.vwaphelper = 0

            #ulozime zacatek potvrzeneho baru
            #self.lastBarConfirmed = self.openedBar['time']

            self.openedBar['updated'] = data['t']
            confirmedBars.append(deepcopy(self.openedBar))
            self.openedBar = None
            #TBD po každém potvrzení zvýšíme čas o nanosekundu (pro zobrazení v gui)
            #data['t'] = data['t'] + 0.000001
            
        #init unconfirmed - velikost bucketu kontrolovana predtim
        def initialize_unconfirmed(size):
                #inicializuji pro nový bar
                self.vwaphelper += (data['p'] * size)
                self.barindex +=1
                self.openedBar =  {
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": size,
                    "trades": 1,
                    "hlcc4": data['p'],
                    "confirmed": 0,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution":dollar_bucket
                    }

        def update_unconfirmed(size):
            #spočteme vwap - potřebujeme předchozí hodnoty 
            self.vwaphelper += (data['p'] * size)
            self.openedBar['updated'] = data['t']
            self.openedBar['close'] = data['p']
            self.openedBar['high'] = max(self.openedBar['high'],data['p'])
            self.openedBar['low'] = min(self.openedBar['low'],data['p'])
            self.openedBar['volume'] = self.openedBar['volume'] + size
            self.openedBar['trades'] = self.openedBar['trades'] + 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            #pohrat si s timto round
            self.openedBar['hlcc4'] = round((self.openedBar['high']+self.openedBar['low']+self.openedBar['close']+self.openedBar['close'])/4,3)

        #init new - confirmed
        def initialize_confirmed(size):
                #ulozime zacatek potvrzeneho baru
                #self.lastBarConfirmed = datetime.fromtimestamp(data['t'])
                self.barindex +=1
                confirmedBars.append({
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": size,
                    "trades": 1,
                    "hlcc4":data['p'],
                    "confirmed": 1,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution": dollar_bucket
                    })
      
        #current trade dollar value
        trade_dollar_val = int(data['s'])*float(data['p'])

        #existuje stávající bar a vejdeme se do nej
        if self.openedBar is not None and trade_dollar_val + self.openedBar['volume']*self.openedBar['close'] < dollar_bucket:
            #vejdeme se do stávajícího baru (tzn. neprekracujeme bucket)
            update_unconfirmed(int(data['s']))
            #updatujeme stávající nepotvrzeny bar
        #nevejdem se do nej nebo neexistuje predchozi bar
        else:
            #1)existuje predchozi bar - doplnime zbytkem do valikosti bucketu a nastavime confirmed
            if self.openedBar is not None:
                
                #doplnime je zbytkem (v bucket left-je zbyvajici volume)
                opened_bar_dollar_val = self.openedBar['volume']*self.openedBar['close']
                bucket_left = int((dollar_bucket - opened_bar_dollar_val)/float(data['p']))
                # - update and confirm bar
                update_unconfirmed(bucket_left)
                confirm_existing()
                
                #zbytek mnozství jde do dalsiho zpracovani
                data['s'] = int(data['s']) - bucket_left
                #nastavime cas o nanosekundu vyssi
                data['t'] = round((data['t']) + 0.000001,6)

            #2 vytvarime novy bar (bary) a vejdeme se do nej
            if int(data['s'])*float(data['p']) < dollar_bucket:
                #vytvarime novy nepotvrzeny bar
                initialize_unconfirmed(int(data['s']))
            #nevejdeme se do nej - pak vytvarime 1 až N dalsich baru (posledni nepotvrzený)           
            else:
            # >>> for i in range(0, 550, 500):
            # ...     print(i)
            # ... 
            # 0
            # 500

                #vytvarime plne potvrzene buckety (kolik se jich plne vejde)
                for size in range(int(dollar_bucket/float(data['p'])), int(data['s']), int(dollar_bucket/float(data['p']))):
                    initialize_confirmed(dollar_bucket/float(data['p']))
                    #nastavime cas o nanosekundu vyssi
                    data['t'] = round((data['t']) + 0.000001,6)
                    #create complete full bucket with same prices and size
                    #naplnit do return pole
                
                #pokud je zbytek vytvorime z nej nepotvrzeny bar
                zbytek = int(data['s'])*float(data['p']) % dollar_bucket
                
                #ze zbytku vytvorime nepotvrzeny bar
                if zbytek > 0:
                    #prevedeme zpatky na volume
                    zbytek = int(zbytek/float(data['p']))
                    initialize_unconfirmed(zbytek)
                    #create new open bar with size zbytek s otevrenym

        #je cena stejna od predchoziho tradu? pro nepotvrzeny cbar vracime jen pri zmene ceny  
        if self.last_price == data['p']:
            self.diff_price = False
        else:
            self.diff_price = True    
        self.last_price = data['p'] 

        if float(data['t']) - float(self.lasttimestamp) < cfh.config_handler.get_val('GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN'):
            self.trades_too_close = True
        else:
            self.trades_too_close = False

        #uložíme do předchozí hodnoty (poznáme tak open a close)
        self.lasttimestamp = data['t']
        self.iterace += 1
        # print(self.iterace, data)

        #pokud mame confirm bary, tak FLUSHNEME confirm a i případný open (zrejme se pak nejaky vytvoril)
        if len(confirmedBars) > 0:
            return_set = confirmedBars + ([self.openedBar] if self.openedBar is not None else [])
            confirmedBars = []
            return return_set

        #nemame confirm, FLUSHUJEME CBARVOLUME open - neresime zmenu ceny, ale neposilame kulomet (pokud nam nevytvari conf. bar)
        if self.openedBar is not None and self.rectype == RecordType.CBARDOLLAR:
            
             #zkousime pustit i stejnou cenu(potrebujeme kvuli MYSELLU), ale blokoval kulomet,tzn. trady mensi nez GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN (1ms)
            #if self.diff_price is True:
            if self.trades_too_close is False:
                return [self.openedBar]
            else:
                return []
        else:
            return []


    async def calculate_renko_bar(self, data, symbol):
        """"
        Agreguje RENKO BARS - dle brick size
        hlavni promenne 
        - self.openedBar (dict) = stavová obsahují aktivní nepotvrzený bar
        - confirmedBars (list) = nestavová obsahuje confirmnute bary, které budou na konci funkceflushnuty
        
        Omezeni: vzhledek tomu, že strategie v CBARu potřebuje realný průběh tick by tick a skutečné Renko bary znamenají
        vyřazování určitých průběhů cenu, tak je realizováno Renko bary s high and low a následným updatem open ceny před confirmací.
        
        open a close bude tedy v potvrzeném baru správně, high-low bude ukazovat na celkový pohyb cen v rámci baru.
         
        Ve strategii je třeba počítat s tím, že open v nepotvrzeném baru není finální.
        """""

        if self.resolution < 0:  # Treat as percentage
            reference_price = self.lastConfirmedBar['close'] if self.lastConfirmedBar is not None else float(data['p'])
            brick_size = abs(self.resolution) * reference_price / 100.0
        else:  # Treat as absolute value pocet ticku
            brick_size = self.resolution

        #pocet ticku např. 10ticků, případně pak na procenta
        #brick_size = self.resolution
        #potvrzene pripravene k vraceni
        confirmedBars = []
        #potvrdi existujici a nastavi k vraceni
        def confirm_existing():
            self.openedBar['confirmed'] = 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            self.vwaphelper = 0

            self.openedBar['updated'] = data['t']
            obar_copy = deepcopy(self.openedBar)
            confirmedBars.append(obar_copy)
            self.lastConfirmedBar = obar_copy
            self.openedBar = None
            #TBD po každém potvrzení zvýšíme čas o nanosekundu (pro zobrazení v gui)
            #data['t'] = data['t'] + 0.000001
            
        #init unconfirmed - velikost bucketu kontrolovana predtim
        def initialize_unconfirmed():
                #inicializuji pro nový bar
                self.vwaphelper += (data['p'] * int(data['s']))
                self.barindex +=1
                self.openedBar =  {
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": int(data['s']),
                    "trades": 1,
                    "hlcc4": data['p'],
                    "confirmed": 0,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution":self.resolution
                    }

        def update_unconfirmed(open = None):

            if open is not None:
                self.openedBar['open'] = open
            #spočteme vwap - potřebujeme předchozí hodnoty 
            self.vwaphelper += (data['p'] * int(data['s']))
            self.openedBar['updated'] = data['t']
            self.openedBar['close'] = data['p']
            self.openedBar['high'] = max(self.openedBar['high'],data['p'])
            self.openedBar['low'] = min(self.openedBar['low'],data['p'])
            self.openedBar['volume'] = self.openedBar['volume'] + int(data['s'])
            self.openedBar['trades'] = self.openedBar['trades'] + 1
            self.openedBar['vwap'] = self.vwaphelper / self.openedBar['volume']
            #pohrat si s timto round
            self.openedBar['hlcc4'] = round((self.openedBar['high']+self.openedBar['low']+self.openedBar['close']+self.openedBar['close'])/4,3)

        #init new - confirmed
        def initialize_confirmed(size):
                self.barindex +=1
                cf_bar = {
                    "close": data['p'],
                    "high": data['p'],
                    "low": data['p'],
                    "open": data['p'],
                    "volume": size,
                    "trades": 1,
                    "hlcc4":data['p'],
                    "confirmed": 1,
                    "time": datetime.fromtimestamp(data['t'], tz=zoneUTC),
                    "updated": data['t'],
                    "vwap": data['p'],
                    "index": self.barindex,
                    "resolution":self.resolution
                    }
                self.lastConfirmedBar = cf_bar
                confirmedBars.append(cf_bar)

        #nastaveni top a low boundary comparatorů bud podle h/l predchoziho potvrzeneho baru
        if self.lastConfirmedBar is not None:
            top_boundary = max(self.lastConfirmedBar["open"], self.lastConfirmedBar["close"])
            low_boundary = min(self.lastConfirmedBar["open"], self.lastConfirmedBar["close"])
        #nebo openu, pokud mame jen nepotvrzeny
        elif self.openedBar is not None:
            top_boundary = self.openedBar["open"]
            low_boundary = self.openedBar["open"]

        if self.openedBar is None:
            initialize_unconfirmed()
        #pct variant: brick_size = self.brick_percentage * self.open_price / 100.0
        elif data['p'] >= top_boundary + brick_size:  # Check if the price has moved by the brick size
            #confirm nese novou cenu, muzou tam byt skryte trady se stejnou cenou nebo kulomet o ktere bychom prisli
            #jinymi slovy prekonací tick renkobaru patří do starého baru
            #novy bar je vytvoren az dalsim tickem, snad to nebude vadit

            #updatujeme open, kam patri
            update_unconfirmed(open=top_boundary)
            confirm_existing()
        elif data['p'] <= low_boundary - brick_size:
            update_unconfirmed(open=low_boundary)
            confirm_existing()            
        else:
            #update stávající
            update_unconfirmed()
   
        #je cena stejna od predchoziho tradu? pro nepotvrzeny cbar vracime jen pri zmene ceny  
        if self.last_price == data['p']:
            self.diff_price = False
        else:
            self.diff_price = True    
        self.last_price = data['p'] 

        if float(data['t']) - float(self.lasttimestamp) < cfh.config_handler.get_val('GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN'):
            self.trades_too_close = True
        else:
            self.trades_too_close = False

        #uložíme do předchozí hodnoty (poznáme tak open a close)
        self.lasttimestamp = data['t']
        self.iterace += 1
        # print(self.iterace, data)

        #pokud mame confirm bary, tak FLUSHNEME confirm a i případný open (zrejme se pak nejaky vytvoril)
        if len(confirmedBars) > 0:
            return_set = confirmedBars + ([self.openedBar] if self.openedBar is not None else [])
            confirmedBars = []
            return return_set

        #nemame confirm, FLUSHUJEME CBARVOLUME open - neresime zmenu ceny, ale neposilame kulomet (pokud nam nevytvari conf. bar)
        if self.openedBar is not None and self.rectype == RecordType.CBARRENKO:
            
             #zkousime pustit i stejnou cenu(potrebujeme kvuli MYSELLU), ale blokoval kulomet,tzn. trady mensi nez GROUP_TRADES_WITH_TIMESTAMP_LESS_THAN (1ms)
            #if self.diff_price is True:
            if self.trades_too_close is False:
                return [self.openedBar]
            else:
                return []
        else:
            return []

    def populate_file_name(self, date_from: datetime, date_to: datetime, exthours=None):
        #nazev obsahuje i child class
        #a take excludes result = ''.join(self.excludes.sort())
        self.exthours = self.exthours if exthours is None else exthours
        self.excludes.sort()  # Sorts the list in place
        excludes_str = ''.join(map(str, self.excludes))  # Joins the sorted elements after converting them to strings
        cache_file = self.__class__.__name__ + '-' + self.symbol + '-' + str(int(date_from.timestamp())) + '-' + str(int(date_to.timestamp())) + '-' + str(self.rectype) + "-" + str(self.resolution) + "-" + str(self.minsize) + "-" + str(self.align) + '-' + str(self.mintick) + str(self.exthours) + excludes_str + '.cache.gz'
        file_path = AGG_CACHE / cache_file
        #print(file_path)
        return file_path

    #returns cached objects for given period
    def get_cache(self, date_from: datetime, date_to: datetime, exthours=None):
        """
        exthours is exthours override, until issue #260 is implemented and global param for exthours
         now Offline ws loader will override exthours param of all streams if one has exthours = True
        """
        file_path = self.populate_file_name(date_from, date_to, exthours)
        if self.skip_cache is False and file_path.exists():
            ##daily aggregated file exists
            with TradeAggregator.lock:
                with gzip.open (file_path, 'rb') as fp:
                    cachedobject = dill.load(fp)
                    print("AGG CACHE loaded ", file_path)

            if isinstance(cachedobject, Queue):
                num = cachedobject.qsize()
            else:
                num = len(cachedobject)
            
            print("cached items",num)      
            return cachedobject, file_path
        else:
            return None, None
        
    #cachujeme jen na exlicitni zapnuti a jen pro BT
    def enable_cache_output(self, date_from: datetime, date_to: datetime, exthours=None):
        self.exthours = exthours if exthours is not None else self.exthours
        self.cache_output_enabled = True
        self.cache_from = date_from
        self.cache_to = date_to

    #lozi storovany cache object self.cache_object do cache
    async def store_cached_object(self):
        if self.cache_output_enabled is False or self.cached_object is None or self.cache_from is None or self.cache_to is None:
            print("cache not enabled or missing data")
            return None
        
        if isinstance(self.cached_object, Queue):
            num = self.cached_object.qsize()
        else:
            num = len(self.cached_object)
        
        file_path = self.populate_file_name(self.cache_from, self.cache_to)
        with TradeAggregator.lock:
            with gzip.open(file_path, 'wb') as fp:
                dill.dump(self.cached_object, fp)
        print(f"AGG CACHE stored ({num}) :{file_path}")
        print(f"DATES from:{self.cache_from.strftime('%d.%m.%Y %H:%M')} to:{self.cache_to.strftime('%d.%m.%Y %H:%M')}")

        #reset values
        self.cached_object = None
        self.cache_output_enabled = False
        self.cache_from = None
        self.cache_to = None

    def send_cache_to_output(self, cachedobject):
        #this has to be overriden by each child
        pass

class TradeAggregator2Queue(TradeAggregator):
    """
    Child of TradeAggregator - sends items to given queue
    In the future others will be added - TradeAggToTxT etc.
    """
    def __init__(self, symbol: str, queue: Queue, rectype: RecordType = RecordType.BAR, resolution: int = 5, minsize: int = 100, update_ltp: bool = False, align: StartBarAlign = StartBarAlign.ROUND, mintick: int = 0, exthours: bool = False, excludes: list = cfh.config_handler.get_val('AGG_EXCLUDED_TRADES'), skip_cache: bool = False):
        super().__init__(rectype=rectype, resolution=resolution, minsize=minsize, update_ltp=update_ltp, align=align, mintick=mintick, exthours=exthours, excludes=excludes, skip_cache=skip_cache)
        self.queue = queue
        self.symbol = symbol
        self.cached_object = Queue()

    # #accepts loaded queue and sents it to given output
    # async def ingest_cached(self, cached_queue):
    #     for element in cached_queue:
    #         self.queue.put(element)

    #prime presunuti celeho ulozeneho objektu queue
    def send_cache_to_output(self, cachedobject):
        self.queue.queue = cachedobject.queue

    #ingest tradu do agregatoru a odeslani do vystupu
    async def ingest_trade(self, data):
            #print("ingest ve threadu:",current_thread().name)
            res = await super().ingest_trade(data, self.symbol)

            #if len(res) > 0:
            for obj in res:
                #print(res)
                #pri rychlem plneni vetsiho dictionary se prepisovali - vyreseno kopií
                if isinstance(obj, dict):
                    copy = obj.copy()
                else:
                    copy = obj

                ##populate secondary resolution if required
                #print("inserted to queue")
                self.queue.put(copy)

                if self.cache_output_enabled:
                    self.cached_object.put(copy)
                    if copy == 'last':
                        await self.store_cached_object()

            res = []
            #print("po insertu",res)

class TradeAggregator2List(TradeAggregator):
    """"
    stores records to the list
    """
    def __init__(self, symbol: str, btdata: list, rectype: RecordType = RecordType.BAR, resolution: int = 5, minsize: int = 100, update_ltp: bool = False, align: StartBarAlign = StartBarAlign.ROUND, mintick: int = 0, exthours: bool = False, excludes: list = cfh.config_handler.get_val('AGG_EXCLUDED_TRADES'), skip_cache: bool = False):
        super().__init__(rectype=rectype, resolution=resolution, minsize=minsize, update_ltp=update_ltp, align=align, mintick=mintick, exthours=exthours, excludes=excludes, skip_cache=skip_cache)
        self.btdata = btdata
        self.symbol = symbol
        self.cached_object = []
        # self.debugfile = DATA_DIR + "/BACprices.txt"
        # if os.path.exists(self.debugfile):
        #     os.remove(self.debugfile)

    #prime presunuti celeho ulozeneho objektu queue
    def send_cache_to_output(self, cachedobject):
        self.btdata.extend(cachedobject)
        #TODO teoreticky to muzeme vzdy brat z primarniho objektu jako funkce nize - promyslet

    # #accepts loaded queue and sents it to given output
    # async def ingest_cached(self, cached_queue):
    #     for element in cached_queue:
    #         self.btdata.append((element['t'],element['p']))

    async def ingest_trade(self, data):
            #print("ted vstoupil do tradeagg2list ingestu")
            res1 = await super().ingest_trade(data, self.symbol)
            #print("ted je po zpracovani", res1)
            for obj in res1:
                #pri rychlem plneni vetsiho dictionary se prepisovali - vyreseno kopií
                if isinstance(obj, dict):
                    copy = obj.copy()
                else:
                    copy = obj

                if self.cache_output_enabled:
                    if copy == 'last':
                        await self.store_cached_object()
                    else:
                        self.cached_object.append((copy['t'],copy['p']))

                if obj == 'last': return []
                self.btdata.append((copy['t'],copy['p']))
                # with open(self.debugfile, "a") as output:
                #     output.write(str(copy['t']) + ' ' + str(datetime.fromtimestamp(copy['t']).astimezone(zoneNY)) + ' ' + str(copy['p']) + '\n')
            res1 = []
                #print("po insertu",res)




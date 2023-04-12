from enums import RecordType, StartBarAlign, Mode, Order
from datetime import datetime, timedelta
from utils import parse_alpaca_timestamp, ltp, AttributeDict

from alpaca.data.enums import DataFeed
import queue
from indicators import ema
from rich import print
from random import randrange
from queue import Queue
from alpaca.trading.stream import TradingStream
from alpaca.trading.enums import OrderSide, OrderStatus
from strategy.base import Strategy, StrategyState
"""
StrategyTypeLimit - Třída pro specifický typ strategie.
Např. práce s BARy(ukládá historii) a obsahuje specifický handling
notifikací (vytváření prodejní limitky)

rectype support: BAR, CBAR (stores history)

obsahuje specifický handling pro automatické vytváření limitky

obsahuje rozšířené buy, sell funkce (předsunuté před interface)
"""
class StrategyTypeLimit(Strategy):
    def __init__(self, symbol: str, paper, next: callable, init: callable, stratvars: dict = None) -> None:
        super().__init__(symbol, paper, next, init, stratvars)
        bars = {'high': [], 
                            'low': [],
                            'volume': [],
                            'close': [],
                            'hlcc4': [],
                            'open': [],
                            'time': [],
                            'trades':[],
                            'resolution':[],
                            'confirmed': [],
                            'vwap': [],
                            'index': []}
        
        self.state = StrategyState(variables=stratvars,bars=bars,oe=self.interface)
        self.first = 1
        self.looprectype = RecordType.BAR
        self.nextnew = 1

    ## overriden strategy loop function to store history
    # logika je jina pro BAR a CBAR - dopracovat dynamickou podporu streamtypu + queues
    # zatim odliseno takto: prvni bar -unconfirmed=CBAR -confirmed=BAR

    
    ##TODO pridat automatické plnení state.positions a state.avgp

    def strat_loop(self):
            #do budoucna rozlisit mezi typy event - trade nebo bar
            bar = self.q1.get()

            #podle prvni iterace pripadne overridnem looprectype
            if self.first==1 and bar['confirmed'] == 0:
                self.looprectype = RecordType.CBAR
                print("jde o CBARs")
                self.first = 0

            if self.looprectype == RecordType.BAR:
                self.append_bar(self.state.bars,bar)
            
            elif self.looprectype == RecordType.CBAR:
                #novy vzdy pridame
                if self.nextnew:
                    self.append_bar(self.state.bars,bar)
                    self.nextnew = 0
                #nasledujici updatneme, po potvrzeni, nasleduje nvoy bar
                else:
                    if bar['confirmed'] == 0:
                        self.replace_prev_bar(self.state.bars,bar)
                    #confirmed
                    else:
                        self.replace_prev_bar(self.state.bars,bar)
                        self.nextnew = 1

            self.next(bar, self.state)

    #předsazená order logika relevantní pro strategii
    def buy(self, size: int = 1, repeat: bool = False):
        # some code before
        self.interface.buy(size = size, repeat = repeat)
        # some code after

    #specifika pro notif callback
    async def orderUpdateSell(self, data):

        ##SELL and FILLED or CANCELLED
        order: Order = data.order
        if order.status == OrderStatus.FILLED or order.status == OrderStatus.CANCELED:
            print("NOTIF: incoming SELL:", order.status)
            #reset pos a avg
            self.avgp, self.poz = self.pos()
            self.limitka = 0
            
    #specifika pro notif callback
    async def orderUpdateBuy(self, data):
        order: Order = data.order
        if order.side == OrderSide.BUY and (order.status == OrderStatus.FILLED or order.status == OrderStatus.PARTIALLY_FILLED):
            print("NOTIF: incoming BUY and FILLED")
            #ukladame posledni nakupni cenu do lastbuy
            self.lastbuy = order.filled_avg_price
            
            #existuje limitka delam replace
            if self.limitka != 0:
                self.avgp, self.poz = self.pos()
                cena: float = 0
                #TUNING - kdyz z nejakeho duvodu je poz = 0 (predbehnuto v rush hour) tak limitka je taky, zrusena tzn. rusime si ji i u sebe
                if int(self.poz) == 0:
                    print("synchro - pozice byla 0 - nastavujeme limitku na 0")
                    self.limitka = 0
                    return 0,0
                else:
                    #OPT tady vyladit
                    cena = round(float(self.avgp) + float(self.stratvars["profit"]),2)
                    print("limitka existuje nahrazujeme - avg cena",self.avgp,"nastavujeme cenu",cena)
                    try:
                        self.limitka = await self.repl(cena,self.limitka,self.poz)

                    except APIError as e:
                        #stejne parametry - stava se pri rychle obratce, nevadi
                        if e.code == 42210000: return 0,0
                        else:
                            print("Neslo nahradit profitku. Problem",str(e))
                            raise Exception(e)

            #limitka neni
            else:
                
                # vyjimka, kdyz limitka neni, ale je vic objednavek (napriklad po crashi) - vytvorime limitku na celkove mnozstvi 
                
                #TODO toto jen docasne nejspis pryc
                #OPTIMALIZOVAT - aby pred limitkou se nemusela volat, mozna dat cely tento blok pryc
                #a nechat vytvorit limitku pouze pro domnelou prvni a pak nasledujici to vsechno srovnat
                self.avgp, self.poz = self.pos()
                
                #mohlo se stat, ze se uz do prichodu notifikace prodala
                if int(self.poz) == 0: return

                print("selfpoz kdyz limitka neni", self.poz)
                if int(self.poz) > int(order.qty):
                    
                    avgcena = self.avgp
                    mnozstvi = self.poz
                else:
                    avgcena = float(order.filled_avg_price)
                    mnozstvi = order.filled_qty
                #nevolame pos, melo by byt 0, bereme avg_price z orderu
                #pokud bude avg_price 32.236
                #OPT 
                cena = round(float(avgcena) + float(self.stratvars["profit"]),2)
                print("limitka neni vytvarime, a to za cenu",cena,"mnozstvi",mnozstvi)
                print("aktuzalni ltp",ltp.price[self.symbol])

                try:
                    self.limitka = await self.sell(cena, mnozstvi)
                    print("vytvorena limitka", self.limitka)
                except Exception as e:
                    print("Neslo vytvorit profitku. Problem",str(e))
                    raise Exception(e)
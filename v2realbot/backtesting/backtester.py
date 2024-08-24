#import os,sys
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
    Backtester component, allows to:

    pro lepší trasovatelnost máme následující razítka
    open orders
        - submitted_at
    trades
        - submitted_at
        - filled_at

    execute_orders_and_callbacks(time)
        - called before iteration
        - execute open orders before "time" and calls notification callbacks

    market buy
    limit buy
    market sell
    limit sell
    cancel order by id
    replace order by id
    get positions

    STATUSES supported:
     -  FILLED (including callbacks)

    not supported: NEW, ACCEPTED, CANCELED (currently no callback action will be backtestable on those)
        - případné nad těmito lze dát do synchronní části (api vrací rovnou zda objednávka neexistuje, pokud existuje tak předpokládáme vyplnění)
    
    supports standard validations and blocking of share and cash upon order submit
    supports only GTC order validity
    no partial fills
    RETURN
    1 - ok
    0 - ok, noaction
    - 1 - error

"""
from uuid import UUID, uuid4
from alpaca.trading.enums import OrderSide, OrderStatus, TradeEvent, OrderType
from v2realbot.common.model import TradeUpdate, Order, Account
from rich import print as printanyway
import threading
import asyncio
from v2realbot.config import DATA_DIR
from v2realbot.utils.utils import AttributeDict, ltp, zoneNY, trunc, count_decimals, print
from v2realbot.utils.tlog import tlog
from v2realbot.enums.enums import FillCondition
from datetime import datetime, timedelta
import pandas as pd
#import matplotlib.pyplot as plt
#import seaborn; seaborn.set()
#import mplfinance as mpf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from bisect import bisect_left
from v2realbot.utils.dash_save_html import make_static
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash import dcc, html, dash_table, Dash
import v2realbot.utils.config_handler as cfh
from typing import Set
""""
LATENCY DELAYS
.000 trigger - last_trade_time (.4246266)
+.020 vstup do strategie a BUY (.444606)
+.023 submitted (.469198)
+.008    filled (.476695552)
+.023   fill not(.499888)
"""
lock = threading.Lock

#todo nejspis dat do classes, aby se mohlo backtestovat paralelne
#ted je globalni promena last_time_now a self.account a cash
class Backtester:
    """
    Initializes a new instance of the Backtester class.
    Args:
        symbol (str): The symbol of the security being backtested.
        accounts (set): A set of accounts to use for backtesting.
        order_fill_callback (callable): A callback function to handle order fills.
        btdata (list): A list of backtesting data.
        bp_from (datetime): The start date of the backtesting period.
        bp_to (datetime): The end date of the backtesting period.
        cash (float, optional): The initial cash balance. Defaults to 100000.
    Returns:
        None
    """
    def __init__(self, symbol: str, accounts: Set, order_fill_callback: callable, btdata: list, bp_from: datetime, bp_to: datetime, cash: float = 100000):
        #this TIME value determines true time for submit, replace, cancel order should happen (allowing past)
        #it is set by every iteration of BT or before fill callback - allowing past events to happen
        self.time = None
        self.symbol = symbol
        self.order_fill_callback = order_fill_callback
        self.btdata = btdata
        self.backtest_start = None
        self.backtest_end = None
        self.accounts = accounts
        self.cash_init = cash
        #backtesting period
        self.bp_from = bp_from
        self.bp_to = bp_to
        self.cash = cash
        self.cash_reserved_for_shorting = 0
        self.trades = []
        self.internal_account = { account.name:{self.symbol: [0, 0]} for account in accounts }
        # { "ACCOUNT1": {}"BAC": [avgp, size]}, .... }
        self.open_orders =[] #open orders shared for all accounts, account being an attribute

        # self.open_orders = [Order(id=uuid4(),
        #                         submitted_at = datetime(2023, 3, 17, 9, 30, 0, 0, tzinfo=zoneNY),
        #                         symbol = "BAC",
        #                         qty = 1,
        #                         status = OrderStatus.ACCEPTED,
        #                         order_type = OrderType.LIMIT,
        #                         side = OrderSide.BUY,
        #                         limit_price=22.4),
        #                     Order(id=uuid4(),
        #                         submitted_at = datetime(2023, 3, 17, 9, 30, 00, 0, tzinfo=zoneNY),
        #                         symbol = "BAC",
        #                         qty = 1,
        #                         order_type = OrderType.MARKET,
        #                         status = OrderStatus.ACCEPTED,
        #                         side = OrderSide.BUY)]
    
    #
  

    def execute_orders_and_callbacks(self, intime: float):
        """""
        Voláno ze strategie před každou iterací s časem T.
        Provede exekuci otevřených objednávek, které by se v reálu vyplnili do tohoto času.
        Pro vyplněné posílá fill notifikaci a volá callback s časem FILLu.

        - current time - state.time
        - actual prices - self.btdata
        - callback after order fill - self.order_fill_callback
        - set time for order fill callback - self.time
        """""

        print(10*"*",intime,"Exec OPEN ORDERS ",len(self.open_orders)," time", datetime.fromtimestamp(intime).astimezone(zoneNY),10*"*")
        # print("cash before", cash)
        # print("BT: executing pending orders")
        # print("list before execution", self.open_orders)

        if len(self.open_orders) == 0:
            #ic("no pend orders")
            return 0

        changes = 0

        #iterating while removing items - have to use todel list
        todel = []
        #with lock:
        """
        Pripravime si pracovni list
        btdata obsahuje vsechny aktualni timestampy tradu a jejich cenu.
        1) pracujeme vzdy OD zacatku listu DO indexu odpovidajici aktualnimu casu
        2) zjistime si index a pak iterujeme nad nim
        3) po skonceni pak tento pracovni kus umazeme
        """

        """
        Assumes myList is sorted. Returns first biggeer value to the number.
        """
        index_end = bisect_left(self.btdata, (intime,))

        # #find index of state.time in btdata - nahrazeno BISECT
        # for index_end in range(len(self.btdata)):
        #     #print(btdata[i][0])
        #     #print(i)
        #     if self.btdata[index_end][0] >= intime:
        #         break

        #pracovni list
        #ic("work_range 0:index_end")
        #ic(index_end)
        work_range = self.btdata[0:index_end]
        #ic(len(work_range))
        #print("index_end", i)
        #print("oriznuto",self.btdata[0:i+1])

        for order in self.open_orders:
            #pokud je vyplneny symbol, tak jedeme jen tyto, jinak vsechny
            print(order.account.name, order.id, datetime.timestamp(order.submitted_at), order.symbol, order.side, order.order_type, order.qty, order.limit_price, order.submitted_at)
            if order.canceled_at:
                #ic("deleting canceled order",order.id)
                todel.append(order)
            elif not self.symbol or order.symbol == self.symbol:
                #pricteme mininimalni latency od submittu k fillu
                if order.submitted_at.timestamp() + cfh.config_handler.get_val('BT_DELAYS','sub_to_fill') > float(intime):
                    print(f"too soon for {order.id}")
                #try to execute
                else:
                    #try to execute specific order
                    a = self._execute_order(o = order, intime=intime, work_range=work_range)
                    if a == 1:
                        #ic("EXECUTED")
                        todel.append(order)
                        changes = 1
                    else:
                        print(f"NOT EXECUTED {a}")
                        #ic("NOT EXECUTED",a)
        ##ic("istodel",todel)
        #vymazu z pending orderu vschny zprocesovane nebo ty na výmaz
        for i in todel:
            self.open_orders.remove(i)
        todel = {}

        #tady udelat pripadny ořez self.btdata - priste zaciname od zacatku
        ##ic("before delete", len(self.btdata))

        #TEST zkusime to nemazat, jak ovlivni performance
        #Mazeme, jinak je to hruza
        #nechavame na konci trady, které muzeme potrebovat pro consekutivni pravidlo
        #osetrujeme, kdy je malo tradu a oriznuti by slo do zaporu
        del_to_index = index_end-2-cfh.config_handler.get_val('BT_FILL_CONS_TRADES_REQUIRED')
        del_to_index = del_to_index if del_to_index > 0 else 0
        del self.btdata[0:del_to_index]
        ##ic("after delete",len(self.btdata[0:index_end]))
    
        if changes: return 1
        else: return 0 
            # print("pending orders after execution", self.open_orders)
            # print("trades after execution", trades)
            # print("self.account after execution", self.account)
            # print("cash after", cash)

    def _execute_order(self, o: Order, intime: float, work_range):
        """tries to execute order 

        o - specific Order
        time - intime
        work_range - aktualni slice of btdata pro tuto iteraci [(timestamp,price)] """

        fill_time = None
        fill_price = None
        order_min_fill_time = o.submitted_at.timestamp() + cfh.config_handler.get_val('BT_DELAYS','sub_to_fill')
        #ic(order_min_fill_time)
        #ic(len(work_range))

        if o.order_type == OrderType.LIMIT:
            if o.side == OrderSide.BUY:
                #counter for consecutive trades
                consec_cnt = 0
                for index, i in enumerate(work_range):
                #print(i)
                ##najde prvni nejvetsi čas vetsi nez minfill a majici odpovídající cenu
                ## pro LIMITku nejspíš přidat BT_DELAY.LIMIT_OFFSET, aby se nevyplnilo hned jako prvni s touto cenou
                ## offest by se pocital od nize nalezeneho casu, zvetsil by ho o LIMIT_OFFSET a zjistil, zda by
                ##v novem case doslo take k plneni a tam ho vyplnil. Uvidime az jestli bude aktualni prilis optimisticke.
                ## TBD zjistit na LIVE jaky je tento offset

                    #TODO pridat pokud je EXECUTION_DEBUG zalogování okolnich tradu (5 z kazde strany) od toho, který triggeroval plnění
                    #TODO pridat jako dalsi nastavovaci atribut pocet tradu po ktere musi byt cena zde (aby to nevyplnil knot high)

                    #NASTVENI PODMINEK PLNENI
                    fast_fill_condition = i[1] <= o.limit_price
                    slow_fill_condition = i[1] < o.limit_price
                    fill_cond_buy_limit = cfh.config_handler.get_val('BT_FILL_CONDITION_BUY_LIMIT')
                    if fill_cond_buy_limit == FillCondition.FAST:
                        fill_condition = fast_fill_condition
                    elif fill_cond_buy_limit == FillCondition.SLOW:
                        fill_condition = slow_fill_condition
                    else:
                        print("unknow fill condition")
                        return -1

                    if float(i[0]) > float(order_min_fill_time+cfh.config_handler.get_val('BT_DELAYS','limit_order_offset')) and fill_condition:
                        consec_cnt += 1
                        if consec_cnt == cfh.config_handler.get_val('BT_FILL_CONS_TRADES_REQUIRED'):

                            #(1679081919.381649, 27.88)
                            #ic(i)
                            fill_time = i[0]
                            
                            #v BT nikdy nekoupime za lepsi cenu nez LIMIT price (TBD mozna zmenit na parametr)
                            fill_price = o.limit_price
                            #fill_price = i[1]

                            print("FILL LIMIT BUY at", fill_time, datetime.fromtimestamp(fill_time).astimezone(zoneNY), "at",i[1])
                            if cfh.config_handler.get_val('BT_FILL_LOG_SURROUNDING_TRADES') != 0:
                                #TODO loguru
                                print("FILL SURR TRADES: before",work_range[index-cfh.config_handler.get_val('BT_FILL_LOG_SURROUNDING_TRADES'):index])
                                print("FILL SURR TRADES: fill and after",work_range[index:index+cfh.config_handler.get_val('BT_FILL_LOG_SURROUNDING_TRADES')])
                            break
                    else:
                        consec_cnt = 0
            else:
                consec_cnt = 0
                for index, i in enumerate(work_range):
                #print(i)
                    #NASTVENI PODMINEK PLNENI
                    fast_fill_condition = i[1] >= o.limit_price
                    slow_fill_condition = i[1] > o.limit_price
                    fill_conf_sell_cfg = cfh.config_handler.get_val('BT_FILL_CONDITION_SELL_LIMIT')
                    if fill_conf_sell_cfg == FillCondition.FAST:
                        fill_condition = fast_fill_condition
                    elif fill_conf_sell_cfg == FillCondition.SLOW:
                        fill_condition = slow_fill_condition
                    else:
                        print("unknown fill condition")
                        return -1

                    if float(i[0]) > float(order_min_fill_time+cfh.config_handler.get_val('BT_DELAYS','limit_order_offset')) and fill_condition:
                        consec_cnt += 1
                        if consec_cnt == cfh.config_handler.get_val('BT_FILL_CONS_TRADES_REQUIRED'):
                            #(1679081919.381649, 27.88)
                            #ic(i)
                            fill_time = i[0]

                            #support pomaleho plneni
                            #v BT nikdy neprodame za lepsi cenu nez LIMIT price (TBD mozna zmenit na parametr)
                            fill_price = o.limit_price


                            #fill_price = i[1]
                            print("FILL LIMIT SELL at", fill_time, datetime.fromtimestamp(fill_time).astimezone(zoneNY), "at",i[1])
                            surr_trades_cfg = cfh.config_handler.get_val('BT_FILL_LOG_SURROUNDING_TRADES')
                            if surr_trades_cfg != 0:
                                #TODO loguru
                                print("FILL SELL SURR TRADES: before",work_range[index-surr_trades_cfg:index])
                                print("FILL SELL SURR TRADES: fill and after",work_range[index:index+surr_trades_cfg])
                            break
                    else:
                        consec_cnt = 0
        
        elif o.order_type == OrderType.MARKET:
            for i in work_range:
                #print(i)
                #najde prvni nejvetsi čas vetsi nez minfill
                if i[0] > float(order_min_fill_time):
                    #(1679081919.381649, 27.88)
                    #ic(i)
                    fill_time = i[0]
                    fill_price = i[1]
                    #přičteme MARKET PREMIUM z konfigurace (je v pct nebo abs) (do budoucna mozna rozdilne pro BUY/SELL a nebo mozna z konfigurace pro dany titul)
                    cfg_premium = cfh.config_handler.get_val('BT_FILL_PRICE_MARKET_ORDER_PREMIUM')
                    if cfg_premium < 0: #configured as percentage
                        premium = abs(cfg_premium) * fill_price / 100.0
                    else: #configured as absolute value
                        premium = cfg_premium           
                    if o.side == OrderSide.BUY:
                        fill_price = fill_price + premium
                    elif o.side == OrderSide.SELL:
                        fill_price = fill_price - premium
                    
                    print("FILL ",o.side,"MARKET at", fill_time, datetime.fromtimestamp(fill_time).astimezone(zoneNY), "cena", i[1])
                    break
        else:
            print("unknown order type")
            return -1
        
        if not fill_time:
            print("not FILLED")
            return 0
        else:

            #order FILLED - update trades and account and cash
            o.filled_at = datetime.fromtimestamp(float(fill_time))
            o.filled_qty = o.qty
            o.filled_avg_price = float(fill_price)
            o.status = OrderStatus.FILLED

            #ic(o.filled_at, o.filled_avg_price)

            a = self.update_internal_account(o = o)
            if a < 0:
                tlog("update_account ERROR")
                return -1

            trade = TradeUpdate(account=o.account,
                                order = o,
                                event = TradeEvent.FILL,
                                execution_id = str(uuid4()),
                                timestamp = datetime.fromtimestamp(fill_time),
                                position_qty= self.internal_account[o.account.name][o.symbol][0],
                                price=float(fill_price),
                                qty = o.qty,
                                value = float(o.qty*fill_price),
                                cash = self.cash,
                                pos_avg_price = self.internal_account[o.account.name][o.symbol][1])
            
            self.trades.append(trade)

            # do notification with callbacks
            #print("pred appendem",self.open_orders)
            self._do_notification_with_callbacks(tradeupdate=trade, time=float(fill_time))
            #print("po appendu",self.open_orders)
            #ohandlovat nejak chyby? v LIVE je to asynchronni a takze neni ohandlovano, takze jen print
            return 1

    def _do_notification_with_callbacks(self, tradeupdate: TradeUpdate, time: float):
    
        #do callbacku je třeba zpropagovat filltime čas (včetně latency pro notifikaci), aby se pripadne akce v callbacku udály s tímto časem
        self.time = time + float(cfh.config_handler.get_val('BT_DELAYS','fill_to_not'))
        print("current bt.time",self.time)
        #print("FILL NOTIFICATION: ", tradeupdate)
        res = asyncio.run(self.order_fill_callback(tradeupdate, tradeupdate.account))
        return 0

    def update_internal_account(self, o: Order):
        #updatujeme self.account
        #pokud neexistuje klic v accountu vytvorime si ho
        if o.symbol not in self.internal_account[o.account.name]:
            # { "BAC": [size, avgp] }
            self.internal_account[o.account.name][o.symbol] = [0,0]

        if o.side == OrderSide.BUY:
            #[size, avgp]
            newsize = (self.internal_account[o.account.name][o.symbol][0] + o.qty)
            #JPLNE UZAVRENI SHORT  (avgp 0)
            if newsize == 0: newavgp = 0
            #CASTECNE UZAVRENI SHORT (avgp puvodni)
            elif newsize < 0: newavgp = self.internal_account[o.account.name][o.symbol][1]
            #JDE O LONG (avgp nove)
            else:
                newavgp = ((self.internal_account[o.account.name][o.symbol][0] * self.internal_account[o.account.name][o.symbol][1]) + (o.qty * o.filled_avg_price)) / (self.internal_account[o.account.name][o.symbol][0] + o.qty)
            
            self.internal_account[o.account.name][o.symbol] = [newsize, newavgp]
            self.cash = self.cash - (o.qty * o.filled_avg_price)
            return 1
        #sell
        elif o.side == OrderSide.SELL:
            newsize = self.internal_account[o.account.name][o.symbol][0]-o.qty
            #UPLNE UZAVRENI LONGU (avgp 0)
            if newsize == 0: newavgp = 0
            #CASTECNE UZAVRENI LONGU (avgp puvodni)
            elif newsize > 0: newavgp = self.internal_account[o.account.name][o.symbol][1]
            #jde o SHORT (avgp nove)
            else:
                #pokud je predchozi 0 - tzn. jde o prvni short
                if self.internal_account[o.account.name][o.symbol][1] == 0:
                    newavgp = o.filled_avg_price
                else:
                    newavgp = ((abs(self.internal_account[o.account.name][o.symbol][0]) * self.internal_account[o.account.name][o.symbol][1]) + (o.qty * o.filled_avg_price)) / (abs(self.internal_account[o.account.name][o.symbol][0]) + o.qty)

            self.internal_account[o.account.name][o.symbol] = [newsize, newavgp]

            #pokud jde o prodej longu(nova pozice je>=0) upravujeme cash
            if self.internal_account[o.account.name][o.symbol][0] >= 0:
                self.cash = float(self.cash + (o.qty * o.filled_avg_price))
                print("uprava cashe, jde o prodej longu")
            else:
                self.cash = float(self.cash + (o.qty * o.filled_avg_price))
                #self.cash_reserved_for_shorting += float(o.qty * o.filled_avg_price)
                print("jde o short, upravujeme cash zatim stejne")    
            return 1
        else:
            print("neznaama side", o.side)
            return -1

    """""
    BACKEND PRO API
    
    TODO - možná toto předělat a brát si čas z bt.time - upravit také v BacktestInterface
    BUG: 
    """""

    def get_last_price(self, time: float, symbol: str = None):
        """""
        returns equity price in timestamp. Assumes myList is sorted. Returns first lower value to the number.
        optimalized as bisect left
        """""
        pos = bisect_left(self.btdata, (time,))
        #ic("vracime last price")
        #ic(time)
        if pos == 0:
            #ic(self.btdata[0][1])
            return self.btdata[0][1]
        afterTime, afterPrice = self.btdata[pos-1]
        #ic(afterPrice)
        return afterPrice


        #not optimalized:
        # for i in range(len(self.btdata)):
        #     #print(btdata[i][0])
        #     #print(i)
        #     if self.btdata[i][0] >= time:
        #         break
        # #ic(time, self.btdata[i-1][1])
        # #ic("get last price")
        # return self.btdata[i-1][1]

    def submit_order(self, time: float, symbol: str, side: OrderSide, size: int, order_type: OrderType, account: Account, price: float = None):
        """submit order
        - zakladni validace
        - vloží do self.open_orders s daným časem
        - vrátí orderID

        status NEW se nenotifikuje

        TBD dotahovani aktualni ceny podle backtesteru
        """
        print("BT: submit order entry")

        if not time or time < 0:
            printanyway("time musi byt vyplneny")
            return -1

        if not size or int(size) < 0:
            printanyway("size musi byt vetsi nez 0")
            return -1

        if (order_type != OrderType.MARKET) and (order_type != OrderType.LIMIT):
            tlog("ordertype market and limit supported only", order_type)
            return -1

        if not side == OrderSide.BUY and not side == OrderSide.SELL:
            printanyway("side buy/sell required")
            return -1
        
        if order_type == OrderType.LIMIT and count_decimals(price) > 2:
            printanyway("only 2 decimals supported", price)
            return -1
    
        #pokud neexistuje klic v accountu vytvorime si ho
        if symbol not in self.internal_account[account.name]:
            # { "BAC": [size, avgp] }
            self.internal_account[account.name][symbol] = [0,0]

        #check for available quantity
        if side == OrderSide.SELL:
            reserved = 0
            reserved_price = 0
            #with lock:
            for o in self.open_orders:
                if o.side == OrderSide.SELL and o.symbol == symbol and o.canceled_at is None and o.account==account:
                    reserved += o.qty
                    cena = o.limit_price if o.limit_price else self.get_last_price(time, o.symbol)
                    reserved_price += o.qty * cena
                print("blokovano v open orders pro sell qty: ", reserved, "celkem:", reserved_price)
            
            actual_minus_reserved = int(self.internal_account[account.name][symbol][0]) - reserved 
            if actual_minus_reserved > 0 and actual_minus_reserved - int(size) < 0:
                printanyway("not enough shares available to sell or shorting while long position",self.internal_account[account.name][symbol][0],"reserved",reserved,"available",int(self.internal_account[account.name][symbol][0]) - reserved,"selling",size)
                return -1
            
            #if is shorting - check available cash to short
            if actual_minus_reserved <= 0:
                cena = price if price else self.get_last_price(time, self.symbol)
                if (self.cash - reserved_price - float(int(size)*float(cena))) < 0:
                    printanyway("ERROR: not enough cash for shorting. cash",self.cash,"reserved",reserved,"available",self.cash-reserved,"needed",float(int(size)*float(cena)))
                    return -1               

        #check for available cash
        if side == OrderSide.BUY:
            reserved_qty = 0
            reserved_price = 0
            #with lock:
            for o in self.open_orders:
                if o.side == OrderSide.BUY and o.canceled_at is None and o.account==account:
                    cena = o.limit_price if o.limit_price else self.get_last_price(time, o.symbol)
                    reserved_price += o.qty * cena
                    reserved_qty += o.qty
                    print("blokovano v open orders for buy: qty, price", reserved_qty, reserved_price)

            actual_plus_reserved_qty = int(self.internal_account[account.name][symbol][0]) + reserved_qty
            
            #jde o uzavreni shortu
            if actual_plus_reserved_qty < 0 and (actual_plus_reserved_qty + int(size)) > 0:
                printanyway("nejprve je treba uzavrit short pozici pro buy res_qty, size", actual_plus_reserved_qty, size)
                return -1

            #jde o standardni long, kontroluju cash
            if actual_plus_reserved_qty >= 0:
                cena = price if price else self.get_last_price(time, self.symbol)
                if (self.cash - reserved_price - float(int(size)*float(cena))) < 0:
                    printanyway("ERROR: not enough cash to buy long. cash",self.cash,"reserved_qty",reserved_qty,"reserved_price",reserved_price, "available",self.cash-reserved_price,"needed",float(int(size)*float(cena)))
                    return -1

        id = str(uuid4())
        order = Order(id=id,
                    account=account,
                    submitted_at = datetime.fromtimestamp(float(time)),
                    symbol=symbol,
                    order_type = order_type,
                    status = OrderStatus.ACCEPTED,
                    side=side,
                    qty=int(size),
                    filled_qty=0,
                    limit_price=(float(price) if price else None))
        
        self.open_orders.append(order)
        #ic("order SUBMITTED", order)
        return id


    def replace_order(self, id: str, time: float, account: Account, size: int = None, price: float = None):
        """replace order
        - zakladni validace vrací synchronně
        - vrací číslo nové objednávky
        """
        print("BT: replace order entry",id,size,price)

        if not price and not size:
            printanyway("size or price required")
            return -1

        if len(self.open_orders) == 0:
            printanyway("BT: order doesnt exist")
            return 0
        #with lock:
        for o in self.open_orders:
            print(o.id)
            if str(o.id) == str(id) and o.account == account:
                newid = str(uuid4())
                o.id = newid
                o.submitted_at = datetime.fromtimestamp(time)
                o.qty = int((size if size else o.qty))
                o.limit_price = float(price if price else o.limit_price)
                print("order replaced")
                return newid
        print("BT: replacement order doesnt exist")
        return 0
    
    def cancel_order(self, time: float, id: str, account: Account):
        """cancel order
        - základní validace vrací synchronně
        - vymaže objednávku z open orders
        - nastavuje v open orders  flag zrušeno, který pak exekuce ignoruje a odstraní
        (je tak podchycen stav, kdy se cancel volá z bt callbacku a z iterovaného listu by se odstraňovalo během iterace)

        TODO: teoreticky bych pred cancel order mohl zavolat execution, abych vyloucil, ze za 20ms zpozdeni, kdy se vola alpaca mi neprojde nejaka objednavka
        spise do budoucna
        """
        print("BT: cancel order entry",id)
        if len(self.open_orders) == 0:
            printanyway("BTC: order doesnt exist")
            return 0
        #with lock:
        for o in self.open_orders:
            if str(o.id) == id and o.account == account:
                o.canceled_at = time
                print("set as canceled in self.open_orders")
                return 1
        print("BTC: cantchange. open order doesnt exist")
        return 0
    
    def get_open_position(self, symbol: str, account: Account):
        """get positions ->(avg,size)"""
        #print("BT:get open positions entry")
        try:
            return self.internal_account[account.name][symbol][1], self.internal_account[account.name][symbol][0]
        except:
            return (0,0)

    def get_open_orders(self, side: OrderSide, symbol: str, account: Account):
        """get open orders ->list(OrderNotification)""" 
        print("BT:get open orders entry")
        if len(self.open_orders) == 0:
            print("BTC: order doesnt exist")
            return []
        res = []
        #with lock:
        for o in self.open_orders:
            #print(o)
            if o.symbol == symbol and o.canceled_at is None and o.account == account:
                if side is None or o.side == side:
                    res.append(o)
        return res

    ##toto bude predelano na display_results(ve variantach) umozni zobrazit result jak BT tak LIVE
    def display_backtest_result(self, state):
        """
        Displays backtest results chart, trades and orders with option to save the result as static HTML.
        """ 
        #open_orders to dataset
        oo_dict = AttributeDict(orderid=[],submitted_at=[],symbol=[],side=[],order_type=[],qty=[],limit_price=[],status=[])
        for t in self.open_orders:
            oo_dict.orderid.append(str(t.id))
            oo_dict.submitted_at.append(t.submitted_at)
            oo_dict.symbol.append(t.symbol)
            oo_dict.side.append(t.side)
            oo_dict.qty.append(t.qty)
            oo_dict.order_type.append(t.order_type)
            oo_dict.limit_price.append(t.limit_price)
            oo_dict.status.append(t.status)

        open_orders_df = pd.DataFrame(oo_dict)
        open_orders_df = open_orders_df.set_index('submitted_at', drop=False)

        #trades to dataset
        trade_dict = AttributeDict(orderid=[],timestamp=[],symbol=[],side=[],order_type=[],qty=[],price=[],position_qty=[],value=[],cash=[],pos_avg_price=[])
        for t in self.trades:
            trade_dict.orderid.append(str(t.order.id))
            trade_dict.timestamp.append(t.timestamp)
            trade_dict.symbol.append(t.order.symbol)
            trade_dict.side.append(t.order.side)
            trade_dict.qty.append(t.qty)
            trade_dict.price.append(t.price)
            trade_dict.position_qty.append(t.position_qty)
            trade_dict.value.append(t.value)
            trade_dict.cash.append(t.cash)
            trade_dict.order_type.append(t.order.order_type)
            trade_dict.pos_avg_price.append(t.pos_avg_price)

        trade_df = pd.DataFrame(trade_dict)
        trade_df = trade_df.set_index('timestamp',drop=False)

        #ohlcv dataset (TODO podporit i trady)
        hist_df = pd.DataFrame(state.bars)
        hist_df = hist_df.set_index('time', drop=False)

        #indicators
        #TODO vyresit if no indicators or no trades - pada na ValueError protoze pole obsahuje time, ale nikoliv indikatory
        #zatim jen takto workaround
        #print(state.indicators)
        try:
            ind_df = pd.DataFrame(state.indicators)
            ind_df = ind_df.set_index('time', drop=False)
        except ValueError as e:
            print("Value error", str(e))
            state.indicators = {'time': [] }
            ind_df = pd.DataFrame(state.indicators)
            ind_df = ind_df.set_index('time', drop=False)
            
        #print("Indicators", ind_df)
        #print(state.indicators)

        #KONEC přípravy dat
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.7, 0.3], specs=[[{"secondary_y": True}],[{"secondary_y": True}]])


        # fig.add_trace(go.Scatter(x=trade_df.index,
        #                          y=trade_df.cash,
        #                          mode="lines+text",
        #                          name="Value"),
        #                 row = 1, col=1, secondary_y=True)

        #add_openorders 
        fig.add_trace(go.Scatter(x=open_orders_df.index,
                                    y=open_orders_df.limit_price,
                                    mode="markers+text",
                                    name="Open orders",
                                    customdata=open_orders_df.orderid,
                                    marker=dict(size=17, color='blue', symbol='arrow-bar-down'),
                                    text=open_orders_df.qty),
                        row = 1, col=1, secondary_y=False)
        
        #add trades
        fig.add_trace(go.Scatter(x=trade_df.loc[trade_df.side==OrderSide.BUY].index,
                                    y=trade_df.loc[trade_df.side==OrderSide.BUY].price,
                                    mode="markers+text",
                                    name="BUY Trades",
                                    customdata=trade_df.loc[trade_df.side==OrderSide.BUY].orderid,
                                    marker=dict(size=15, color='green', symbol='arrow-up'),
                                    text=trade_df.loc[trade_df.side==OrderSide.BUY].position_qty),
                        row = 1, col=1, secondary_y=False)

        fig.add_trace(go.Scatter(x=trade_df.loc[trade_df.side==OrderSide.SELL].index,
                                    y=trade_df.loc[trade_df.side==OrderSide.SELL].price,
                                    mode="markers+text",
                                    name="SELL Trades",
                                    customdata=trade_df.loc[trade_df.side==OrderSide.SELL].orderid,
                                    marker=dict(size=15, color='red', symbol='arrow-down'),
                                    text=trade_df.loc[trade_df.side==OrderSide.SELL].qty),
                        row = 1, col=1, secondary_y=False)
        
        #add avgprices of all buy trades
        
        fig.add_trace(go.Scatter(x=trade_df.loc[trade_df.side==OrderSide.BUY].index,
                    y=trade_df.loc[trade_df.side==OrderSide.BUY].pos_avg_price,
                    mode="markers+text",
                    name="BUY Trades avg prices",
                    customdata=trade_df.loc[trade_df.side==OrderSide.BUY].orderid,
                    marker=dict(size=15, color='blue', symbol='diamond-wide'),
                    text=trade_df.loc[trade_df.side==OrderSide.BUY].position_qty),
        row = 1, col=1, secondary_y=False)

        #display ohlcv
        fig.add_trace(go.Candlestick(x=hist_df.index,
                                    open=hist_df['open'],
                                    high=hist_df['high'],
                                    low=hist_df['low'],
                                    close=hist_df['close'],
                                    name = "OHLC"),
                        row = 1, col=1, secondary_y=False)

        #addvwap
        fig.add_trace(go.Scatter(x=hist_df.index,
                                    y=hist_df.vwap,
                                    mode="lines",
                                    opacity=1,
                                    name="VWAP"
                                    ),
                        row = 1, col=1,secondary_y=False)
        

        #display indicators from history
        for col in ind_df.columns:
            fig.add_trace(go.Scatter(x=ind_df.index, y = ind_df[col], mode = 'lines', name = col),
                          row = 1, col=1, secondary_y=False)

        fig.add_trace(go.Bar(x=hist_df.index, y=hist_df.volume, showlegend=True, marker_color='#ef5350', name='Volume'), row=2,
                 col=1)

        fig.update_layout(xaxis_rangeslider_visible=False)
        #fig.update_layout(title=f'Backtesting Results   '+str(Neco.vars), yaxis_title=f'Price')
        fig.update_layout(yaxis_title=f'Price')
        fig.update_yaxes(title_text=f'Price', secondary_y=False)
        fig.update_yaxes(title_text=f'Cash value', secondary_y=True)
        fig.update_yaxes(title_text=f'Volume', row=2, col=1)
        fig.update_xaxes(title_text='Date', row=2)


        # #remove gaps
        # alldays =set(hist_df.time[0]+timedelta(x) for x in range((hist_df.time[len(hist_df.time)-1]- hist_df.time[0]).days))
        # missing=sorted(set(alldays)-set(hist_df.time))

        
        rangebreaks=[
            # NOTE: Below values are bound (not single values), ie. hide x to y
            dict(bounds=["sat", "mon"]),  # hide weekends, eg. hide sat to before mon
            dict(bounds=[22, 15.5], pattern="hour"),  # hide hours outside of 9.30am-4pm
            # dict(values=["2020-12-25", "2021-01-01"])  # hide holidays (Christmas and New Year's, etc)
        ]

        fig.update_xaxes(rangebreaks=rangebreaks)


        ##START DASH
        app = Dash(__name__)

        ## Define the title for the app
        mytitle = dcc.Markdown('# Backtesting results')
        button = html.Button('save static', id='save', n_clicks=0)
        saved = html.Span('', id='saved')
        textik1 = html.Div('''
            Strategy:''' + state.name)
        textik2 = html.Div('''
            Tested period:'''+ self.bp_from.strftime("%d/%m/%Y, %H:%M:%S") + '-' + self.bp_to.strftime("%d/%m/%Y, %H:%M:%S"))
        textik3 = html.Div('''
            Stratvars:'''+ str(state.vars))
        textik35 = html.Div('''
            Resolution:'''+ str(state.resolution) + "s  rectype:" + str(state.rectype))
        textik4 = html.Div('''
            Started at:''' + self.backtest_start.strftime("%d/%m/%Y, %H:%M:%S") + " Duration:"+str(self.backtest_end-self.backtest_start))
        textik5 = html.Div('''
            Cash start:''' + str(self.cash_init)+ "  Cash final" + str(self.cash))
        textik55 = html.Div('''
            Positions:''' + str(self.account))
        textik6 = html.Div('''
            Open orders:''' + str(len(self.open_orders)))
        textik7 = html.Div('''
            Trades:''' + str(len(self.trades)))
        textik8 = html.Div('''
            Profit:''' + str(state.profit))
        textik9 = html.Div(f"{cfh.config_handler.get_val('BT_FILL_CONS_TRADES_REQUIRED')=}")
        textik10 = html.Div(f"{cfh.config_handler.get_val('BT_FILL_LOG_SURROUNDING_TRADES')=}")
        textik11 = html.Div(f"{cfh.config_handler.get_val('BT_FILL_CONDITION_BUY_LIMIT')=}")
        textik12 = html.Div(f"{cfh.config_handler.get_val('BT_FILL_CONDITION_SELL_LIMIT')=}")
        
        orders_title = dcc.Markdown('## Open orders')
        trades_title = dcc.Markdown('## Trades')
        ## Define the graph
        mygraph= dcc.Graph(id = "hlavni-graf", figure=fig)

        open_orders_table = dash_table.DataTable(
            id="orderstable",
            data=open_orders_df.to_dict('records'),
            columns=[{'id': c, 'name': c} for c in open_orders_df.columns],
            sort_action="native",
            row_selectable="single",
            column_selectable=False,
            fill_width = False,
            filter_action = "native",
            style_table={
                'height': 500,
                'overflowY': 'scroll'
            },
            style_header={
                'backgroundColor': 'lightgrey',
                'color': 'black'
            },
            style_data={
                'backgroundColor': 'white',
                'color': 'black'
            },
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 220,
                'minWidth': 5,
                'width': 5
            }
        )

        trades_table = dash_table.DataTable(
            id="tradestable",
            data=trade_df.to_dict('records'),
            columns=[{'id': c, 'name': c} for c in trade_df.columns],
            sort_action="native",
            row_selectable="single",
            column_selectable=False,
            fill_width = False,
            filter_action = "native",
            style_table={
                'height': 500,
                'overflowY': 'scroll'
            },
            style_header={
                'backgroundColor': 'lightgrey',
                'color': 'black'
            },
            style_data={
                'backgroundColor': 'white',
                'color': 'black'
            },
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 220,
                'minWidth': 5,
                'width': 5
            }
            # page_size=15
        )

        @app.callback(Output("tradestable", "style_data_conditional"),
                    Input("hlavni-graf", "hoverData"))
        def highlight(hoverData):
            #print(hoverData)
            if hoverData is None:
                return None
            try:
                row = hoverData["points"][0]["customdata"]
            except KeyError:
                return None
            #print(row)

            #print({"if": {"filter_query": "{{orderid}}={}".format(row)}, "backgroundColor": "lightgrey"})
            return [
                {"if": {"filter_query": "{{orderid}}={}".format(row)}, "backgroundColor": "lightgrey"}
            ]
        @app.callback(Output("orderstable", "style_data_conditional"),
                    Input("hlavni-graf", "hoverData"))
        def highlight(hoverData):
            #print(hoverData)
            if hoverData is None:
                return None
            try:
                row = hoverData["points"][0]["customdata"]
            except KeyError:
                return None
            #print(row)

            #print({"if": {"filter_query": "{{orderid}}={}".format(row)}, "backgroundColor": "lightgrey"})
            return [
                {"if": {"filter_query": "{{orderid}}={}".format(row)}, "backgroundColor": "lightgrey"}
            ]

        @app.callback(
            Output('saved', 'children'),
            Input('save', 'n_clicks'),
        )
        def save_result(n_clicks):
            if n_clicks == 0:
                return 'not saved'
            else:
                bt_dir = DATA_DIR + "/backtestresults/" + self.symbol + self.bp_from.strftime("%d-%m-%y-%H-%M-%S") + ' ' + self.bp_to.strftime("%d-%m-%y-%H-%M-%S") + ' ' + str(datetime.now().microsecond)
                make_static(f'http://127.0.0.1:{port}/', bt_dir)
                return 'saved'

        ## Customize your layout
        app.layout = dbc.Container([mytitle,button,saved, textik1, textik2, textik3, textik35, textik4, textik5, textik55, textik6,textik7, textik8, textik9, textik10, textik11, textik12, mygraph, trades_title, trades_table, orders_title, open_orders_table])

        port = 9050
        print("Backtest FINSIHED"+str(self.backtest_end-self.backtest_start))
        threading.Thread(target=lambda: app.run(port=port, debug=False, use_reloader=False)).start()
        #app.run_server(debug=False, port = port)
        print("tady se spouští server")
        print("Jedeme dal?")

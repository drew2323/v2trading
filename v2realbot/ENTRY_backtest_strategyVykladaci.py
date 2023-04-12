import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaci import StrategyOrderLimitVykladaci
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.indicators.indicators import ema
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, dict_replace_value
from datetime import datetime
from icecream import install, ic
from rich import print
from threading import Event
import asyncio
import os
import tomli
install()
ic.configureOutput(includeContext=True)
#ic.disable()

print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
""""
Vykladaci strategie refactored z původního engine
Params:
(maxpozic = 200, chunk = 50, MA = 6, Trend = 6, profit = 0.02, lastbuyindex=-6, pendingbuys={},limitka = None, jevylozeno=0, ticks2reset = 0.04, blockbuy=0)


Více nakupuje oproti Dokupovaci. Tady vylozime a nakupujeme 5 pozic hned. Pri dokupovaci se dokupuje, az na zaklade dalsich triggeru.
Do budoucna vice ridit nakupy pri klesani - napr. vyložení jen 2-3 pozic a další dokupy až po triggeru.
#
"""
stratvars = AttributeDict(maxpozic = 250,
                          chunk = 10,
                          MA = 3,
                          Trend = 3,
                          profit = 0.02,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None,
                          jevylozeno=0,
                          vykladka=5,
                          curve = [0.01, 0.01, 0.01, 0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01],
                          blockbuy = 0,
                          ticks2reset = 0.04)
##toto rozparsovat a strategii spustit stejne jako v main
toml_string = """
[[strategies]]
name = "V1 na BAC"
symbol = "BAC"
script = "ENTRY_backtest_strategyVykladaci"
class = "StrategyOrderLimitVykladaci"
open_rush = 0
close_rush = 0
[strategies.stratvars]
maxpozic = 200
chunk = 10
MA = 6
Trend = 5
profit = 0.02
lastbuyindex=-6
pendingbuys={}
limitka = "None"
jevylozeno=0
vykladka=5
curve = [0.01, 0.01, 0.01,0.01, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01]
blockbuy = 0
ticks2reset = 0.04
[[strategies.add_data]]
symbol="BAC"
rectype="bar"
timeframe=5
update_ltp=true
align="round"
mintick=0
minsize=100
exthours=false
"""

def next(data, state: StrategyState):
    print(10*"*","NEXT START",10*"*")
    ic(state.avgp, state.positions)
    ic(state.vars)
    ic(data)

    #mozna presunout o level vys
    def vyloz():
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        #curve = [0.01, 0.01, 0, 0, 0.01, 0, 0, 0, 0.02, 0, 0, 0, 0.03, 0,0,0,0,0, 0.02, 0,0,0,0,0,0, 0.02]
        curve = state.vars.curve

        #vykladani po 5ti kusech, když zbývají 2 a méně, tak děláme nový výklad
        vykladka = state.vars.vykladka
        #kolik muzu max vylozit
        kolikmuzu = int((int(state.vars.maxpozic) - int(state.positions))/int(state.vars.chunk))
        if kolikmuzu < vykladka: vykladka = kolikmuzu

        if len(curve) < vykladka:
            vykladka = len(curve)
        qty = int(state.vars.chunk)
        last_price = price2dec(state.interface.get_last_price(state.symbol))
        #profit = float(state.vars.profit)
        price = last_price
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        state.buy_l(price=price, size=qty)
        print("prvni limitka na aktuální cenu. Další podle křicvky", price, qty)
        for i in range(0,vykladka-1):
            price = price2dec(float(price - curve[i]))
            if price == last_price:
                qty = qty + int(state.vars.chunk)
            else:
                state.buy_l(price=price, size=qty)
                print(i,"BUY limitka - delta",curve[i]," cena:", price, "mnozstvi:", qty)
                qty = int(state.vars.chunk)
            last_price = price
        state.vars.blockbuy = 1
        state.vars.jevylozeno = 1

    #CBAR protection,  only 1x order per CBAR - then wait until another confirmed bar

    if state.vars.blockbuy == 1 and state.rectype == RecordType.CBAR:
        if state.bars.confirmed[-1] == 0:
            print("OCHR: multibuy protection. waiting for next bar")
            return 0
        # pop potvrzeni jeste jednou vratime (aby se nekoupilo znova, je stale ten stejny bar)
        # a pak dalsi vejde az po minticku
        else:
            # pro vykladaci
            state.vars.blockbuy = 0
            return 0

    try:
        print(state.vars.MA, "MACKO")
        print(state.bars.hlcc4)
        state.indicators.ema = ema(state.bars.hlcc4, state.vars.MA) #state.bars.vwap
        #trochu prasarna, EMAcko trunc na 3 mista - kdyz se osvedci, tak udelat efektivne
        state.indicators.ema = [trunc(i,3) for i in state.indicators.ema]
        ic(state.vars.MA, state.vars.Trend, state.indicators.ema[-5:])
    except Exception as e:
        print("No data for MA yet", str(e))

    print("is falling",isfalling(state.indicators.ema,state.vars.Trend))
    print("is rising",isrising(state.indicators.ema,state.vars.Trend))

    #and data['index'] > state.vars.lastbuyindex+state.vars.Trend:
    #neni vylozeno muzeme nakupovat
    if ic(state.vars.jevylozeno) == 0:
        print("Neni vylozeno, muzeme testovat nakup")

        if isfalling(state.indicators.ema,state.vars.Trend):
            print("BUY MARKET")
            ic(data['updated'])
            ic(state.time)
            #zatim vykladame full
            #positions = int(int(state.vars.maxpozic)/int(state.vars.chunk))
            vyloz()

    ## testuje aktualni cenu od nejvyssi visici limitky
    ##toto spoustet jednou za X iterací - ted to jede pokazdé
    #pokud to ujede o vic, rusime limitky
    #TODO: zvazit jestli nechat i pri otevrenych pozicich, zatim nechavame
    #TODO int(int(state.oa.poz)/int(state.variables.chunk)) > X

    #TODO predelat mechanismus ticků (zrelativizovat), aby byl pouzitelny na tituly s ruznou cenou
    #TODO spoustet 1x za X iteraci nebo cas
    if state.vars.jevylozeno == 1:
        #pokud mame vylozeno a cena je vetsi nez 0.04 
            if len(state.vars.pendingbuys)>0:
                maxprice = max(state.vars.pendingbuys.values())
                print("max cena v orderbuys", maxprice)
                if state.interface.get_last_price(state.symbol) > float(maxprice) + state.vars.ticks2reset:
                    print("ujelo to vice nez o " + str(state.vars.ticks2reset) + ", rusime limit buye")
                    ##TODO toto nejak vymyslet - duplikovat?
                    res = asyncio.run(state.cancel_pending_buys())


            #pokud mame vylozeno a pendingbuys se vyklepou a 
            # 1 vykladame idned znovu
                # vyloz()
            # 2 nebo - počkat zase na signál a pokračovat dál  
                # state.vars.blockbuy = 0
                # state.vars.jevylozeno = 0
            # 3 nebo - počkat na signál s enablovaným lastbuy indexem (tzn. počká nutně ještě pár barů)   
            #podle BT vyhodnejsi vylozit ihned
            if len(state.vars.pendingbuys) == 0:
                state.vars.blockbuy = 0
                state.vars.jevylozeno = 0

            #TODO toto dodelat
            #pokud je vylozeno a mame pozice a neexistuje limitka - pak ji vytvorim
            # if int(state.oe.poz)>0 and state.oe.limitka == 0:
            #     #pro jistotu updatujeme pozice
            #     state.oe.avgp, state.oe.poz = state.oe.pos()
            #     if int(state.oe.poz) > 0:
            #         cena = round(float(state.oe.avgp) + float(state.oe.stratvars["profit"]),2)
            #         print("BUGF: limitka neni vytvarime, a to za cenu",cena,"mnozstvi",state.oe.poz)
            #         print("aktuzalni ltp",ltp.price[state.oe.symbol])

            #         try:
            #             state.oe.limitka = state.oe.sell_noasync(cena, state.oe.poz)
            #             print("vytvorena limitka", state.oe.limitka)
            #         except Exception as e:
            #             print("Neslo vytvorit profitku. Problem,ale jedeme dal",str(e))
            #             pass
            #             ##raise Exception(e)

    print(10*"*","NEXT STOP",10*"*")

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)
    state.indicators['ema'] = []

def main():

    try:
        strat_settings = tomli.loads("]] this is invalid TOML [[")
    except tomli.TOMLDecodeError:
        print("Yep, definitely not valid.")
    
    #strat_settings = dict_replace_value(strat_settings, "None", None)

    name = os.path.basename(__file__)
    se = Event()
    pe = Event()
    s = StrategyOrderLimitVykladaci(name = name, symbol = "BAC", account=Account.ACCOUNT2, next=next, init=init, stratvars=stratvars, open_rush=40, close_rush=0, pe=pe, se=se)
    s.set_mode(mode = Mode.PAPER,
               debug = False,
               start = datetime(2023, 3, 30, 9, 30, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 3, 31, 16, 0, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.BAR,timeframe=5,minsize=100,update_ltp=True,align=StartBarAlign.ROUND,mintick=0, exthours=True)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()
    print("zastavujeme")

if __name__ == "__main__":
    main()




 
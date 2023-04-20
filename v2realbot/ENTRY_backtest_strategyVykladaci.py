import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaci import StrategyOrderLimitVykladaci
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide
from v2realbot.indicators.indicators import ema
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, dict_replace_value, print
from datetime import datetime
from icecream import install, ic
#from rich import print
from threading import Event
from msgpack import packb, unpackb
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

Pozor na symbolu nesmi byt dalsi cizí otevrene objednavky:
Pravidelny konzolidacni process da SELL order da do limitka, BUY - do pole pendingbuys

consolidation_bar_count - pocet baru po kterych se triggeruje konzolidační proces

Více nakupuje oproti Dokupovaci. Tady vylozime a nakupujeme 5 pozic hned. Pri dokupovaci se dokupuje, az na zaklade dalsich triggeru.
Do budoucna vice ridit nakupy pri klesani - napr. vyložení jen 2-3 pozic a další dokupy až po triggeru.
#
"""
stratvars = AttributeDict(maxpozic = 400,
                          chunk = 10,
                          MA = 2,
                          Trend = 2,
                          profit = 0.02,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None,
                          limitka_price = None,
                          jevylozeno=0,
                          vykladka=5,
                          curve = [0.01, 0.01, 0.01, 0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01],
                          blockbuy = 0,
                          ticks2reset = 0.04,
                          consolidation_bar_count = 10,
                          slope_lookback = 300,
                          lookback_offset = 20,
                          minimum_slope = -0.05,
                          )
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
        state.ilog(e="BUY Vykladame", msg="first price"+str(price) + "pozic:"+str(vykladka), curve=curve, ema=state.indicators.ema[-1], trend=state.vars.Trend, price=price, vykladka=vykladka)
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        state.buy_l(price=price, size=qty)
        print("prvni limitka na aktuální cenu. Další podle křivky", price, qty)
        for i in range(0,vykladka-1):
            price = price2dec(float(price - curve[i]))
            if price == last_price:
                qty = qty + int(state.vars.chunk)
            else:
                state.buy_l(price=price, size=qty)
                #print(i,"BUY limitka - delta",curve[i]," cena:", price, "mnozstvi:", qty)
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

        ## slope vyresi rychlé sesupy - jeste je treba podchytit pomalejsi sesupy

        slope = 99
        #minimum slope disabled if -1


        #roc_lookback = 20
        #print(state.vars.MA, "MACKO")
        #print(state.bars.hlcc4)
        state.indicators.ema = ema(state.bars.close, state.vars.MA) #state.bars.vwap
        #trochu prasarna, EMAcko trunc na 3 mista - kdyz se osvedci, tak udelat efektivne
        state.indicators.ema = [trunc(i,3) for i in state.indicators.ema]
        ic(state.vars.MA, state.vars.Trend, state.indicators.ema[-5:])

        slope_lookback = int(state.vars.slope_lookback)
        minimum_slope = float(state.vars.minimum_slope)
        lookback_offset = int(state.vars.lookback_offset)

        if len(state.bars.close) > (slope_lookback + lookback_offset):

            #SLOPE INDICATOR POPULATION
            #úhel stoupání a klesání vyjádřený mezi -1 až 1
            #pravý bod přímky je aktuální cena, levý je průměr X(lookback offset) starších hodnot od slope_lookback.
            #obsahuje statický indikátor pro vizualizaci
            array_od = slope_lookback + lookback_offset
            array_do = slope_lookback
            lookbackprice_array = state.bars.vwap[-array_od:-array_do]
            #obycejný prumer hodnot
            lookbackprice = sum(lookbackprice_array)/lookback_offset

            #výpočet úhlu
            slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
            state.indicators.slope.append(slope)
 
            state.statinds.angle = dict(time=state.bars.time[-1], price=state.bars.close[-1], lookbacktime=state.bars.time[-slope_lookback], lookbackprice=lookbackprice, minimum_slope=minimum_slope)
 
            #state.indicators.roc.append(roc)
            #print("slope", state.indicators.slope[-5:])
            state.ilog(e="Slope "+str(slope), msg="lookback price:"+str(lookbackprice), lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators.slope[-5:])
        else:
            state.ilog(e="Slope - not enough data", slope_lookback=slope_lookback)

    except Exception as e:
        print("Exception in NEXT Indicator section", str(e))
        state.ilog(e="EXCEPTION", msg="Exception in NEXT Indicator section" + str(e))

    print("is falling",isfalling(state.indicators.ema,state.vars.Trend))
    print("is rising",isrising(state.indicators.ema,state.vars.Trend))

    ##CONSOLIDATION PART - moved here, musí být před nákupem, jinak to dělalo nepořádek v pendingbuys
    if state.vars.jevylozeno == 1:
        ##CONSOLIDATION PART kazdy Nty bar dle nastaveni
        if int(data["index"])%int(state.vars.consolidation_bar_count) == 0:
            print("***Consolidation ENTRY***")
            state.ilog(e="***Konzolidujeme")

            orderlist = state.interface.get_open_orders(symbol=state.symbol, side=None)
            #print(orderlist)
            pendingbuys_new = {}
            limitka_old = state.vars.limitka
            #print("Puvodni LIMITKA", limitka_old)
            #zaciname s cistym stitem
            state.vars.limitka = None
            state.vars.limitka_price = None
            limitka_found = False
            limitka_qty = 0
            for o in orderlist:
                if o.side == OrderSide.SELL:
                    #print("Nalezena LIMITKA")
                    limitka_found = True
                    state.vars.limitka = o.id
                    state.vars.limitka_price = o.limit_price
                    limitka_qty = o.qty
                    ##TODO sem pridat upravu ceny
                if o.side == OrderSide.BUY:
                    pendingbuys_new[str(o.id)]=float(o.limit_price)

            state.ilog(e="Konzolidace limitky", msg="limitka stejna?:"+str((str(limitka_old)==str(state.vars.limitka))), limitka_old=str(limitka_old), limitka_new=str(state.vars.limitka), limitka_new_price=state.vars.limitka_price, limitka_qty=limitka_qty)
            
            #neni limitka, ale mela by byt - vytváříme ji
            if int(state.positions) > 0 and state.vars.limitka is None:
                state.ilog(e="Limitka neni, ale mela by být.")
                price=price2dec(float(state.avgp)+state.vars.profit)
                state.vars.limitka = asyncio.run(state.interface.sell_l(price=price, size=state.positions))
                state.vars.limitka_price = price
                state.ilog(e="Vytvořena nová limitka", limitka=str(state.vars.limitka), limtka_price=state.vars.limitka_price)

            if int(state.positions) > 0 and (int(state.positions) != int(limitka_qty)):
                #limitka existuje, ale spatne mnostvi - updatujeme
                state.ilog(e="Limitka existuje, ale spatne mnozstvi - updatujeme", msg="POS"+str(state.positions)+" lim_qty:"+str(limitka_qty), pos=state.positions, limitka_qty=limitka_qty)
                #snad to nespadne, kdyztak pridat exception handling
                state.vars.limitka = asyncio.run(state.interface.repl(price=state.vars.limitka_price, orderid=state.vars.limitka, size=int(state.positions)))
                limitka_qty = int(state.positions)
                state.ilog(e="Změněna limitka", limitka=str(state.vars.limitka), limitka_price=state.vars.limitka_price, limitka_qty=limitka_qty)
            
            if pendingbuys_new != state.vars.pendingbuys:
                state.ilog(e="Rozdilna PB prepsana", pb_new=pendingbuys_new, pb_old = state.vars.pendingbuys)
                print("ROZDILNA PENDINGBUYS přepsána")
                print("OLD",state.vars.pendingbuys)
                state.vars.pendingbuys = unpackb(packb(pendingbuys_new))
                print("NEW", state.vars.pendingbuys)
            else:
                print("PENDINGBUYS sedí - necháváme", state.vars.pendingbuys)
                state.ilog(e="PB sedi nechavame", pb_new=pendingbuys_new, pb_old = state.vars.pendingbuys)
            print("OLD jevylozeno", state.vars.jevylozeno)
            if len(state.vars.pendingbuys) > 0:
                state.vars.jevylozeno = 1
            else:
                state.vars.jevylozeno = 0
            print("NEW jevylozeno", state.vars.jevylozeno)
            state.ilog(e="Nove jevylozeno", msg=state.vars.jevylozeno)

            #print(limitka)
            #print(pendingbuys_new)
            #print(pendingbuys)
            #print(len(pendingbuys))
            #print(len(pendingbuys_new))
            #print(jevylozeno)
            print("***CONSOLIDATION EXIT***")
            state.ilog(e="***Konzolidace konec")
        else:
            state.ilog(e="No time for consolidation", msg=data["index"])
            print("no time for consolidation", data["index"])

    #HLAVNI ITERACNI LOG JESTE PRED AKCI - obsahuje aktualni hodnoty vetsiny parametru
    lp = state.interface.get_last_price(symbol=state.symbol)
    state.ilog(e="ENTRY", msg="AVGP:"+str(state.avgp)+ "POS:" +str(state.positions), last_price=lp, stratvars=state.vars)

    #SLOPE ANGLE PROTECTION
    if slope < minimum_slope:
        print("OCHRANA SLOPE TOO HIGH")
        state.ilog(e="Slope too high "+str(slope))
        if len(state.vars.pendingbuys)>0:
            print("CANCEL PENDINGBUYS")
            ic(state.vars.pendingbuys)
            res = asyncio.run(state.cancel_pending_buys())
            ic(state.vars.pendingbuys)
            state.ilog(e="Rusime pendingbuyes", pb=state.vars.pendingbuys, res=res)
        print("slope", slope)
        print("min slope", minimum_slope)

    if ic(state.vars.jevylozeno) == 0:
        print("Neni vylozeno, muzeme testovat nakup")

        if isfalling(state.indicators.ema,state.vars.Trend) and slope > minimum_slope:
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
        #pokud mame vylozeno a cena je vetsi nez tick2reset 
            if len(state.vars.pendingbuys)>0:
                maxprice = max(state.vars.pendingbuys.values())
                print("max cena v orderbuys", maxprice)
                if state.interface.get_last_price(state.symbol) > float(maxprice) + float(state.vars.ticks2reset):
                    ##TODO toto nejak vymyslet - duplikovat?
                    res = asyncio.run(state.cancel_pending_buys())
                    state.ilog(e="UJELO to o více " + str(state.vars.ticks2reset), msg="zrusene pb buye", pb=state.vars.pendingbuys)


            #PENDING BUYS SPENT - PART
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
                state.ilog(e="PB se vyklepaly nastavujeme: neni vylozeno", jevylozeno=state.vars.jevylozeno)

            #TODO toto dodelat konzolidaci a mozna lock na limitku a pendingbuys a jevylozeno ??

            #kdykoliv se muze notifikace ztratit 
                # - pendingbuys - vsechny open orders buy
                # - limitka - open order sell




            

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
    state.indicators['slope'] = []
    #static indicators - those not series based
    state.statinds['angle'] = {}

    #state.indicators['roc'] = []
    #state.ilog(e="INIT", stratvars=state.vars)

def main():

    try:
        strat_settings = tomli.loads("]] this is invalid TOML [[")
    except tomli.TOMLDecodeError:
        print("Yep, definitely not valid.")
    
    #strat_settings = dict_replace_value(strat_settings, "None", None)

    name = os.path.basename(__file__)
    se = Event()
    pe = Event()
    s = StrategyOrderLimitVykladaci(name = name, symbol = "BAC", account=Account.ACCOUNT1, next=next, init=init, stratvars=stratvars, open_rush=10, close_rush=0, pe=pe, se=se)
    s.set_mode(mode = Mode.BT,
               debug = False,
               start = datetime(2023, 4, 14, 10, 42, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 4, 14, 14, 35, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.BAR,timeframe=2,minsize=100,update_ltp=True,align=StartBarAlign.ROUND,mintick=0, exthours=False)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()
    print("zastavujeme")

if __name__ == "__main__":
    main()




 
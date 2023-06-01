import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide, OrderType
from v2realbot.indicators.indicators import ema
from v2realbot.indicators.oscillators import rsi
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, print, safe_get, get_tick, round2five, is_open_rush, is_close_rush, eval_cond_dict
from datetime import datetime
#from icecream import install, ic
#from rich import print
from threading import Event
from msgpack import packb, unpackb
import asyncio
import os
from traceback import format_exc
import inspect

print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
""""
Využívá: StrategyOrderLimitVykladaciNormalizedMYSELL

Kopie RSI Normalizovane Vykladaci navíc s řízením prodeje.
Nepoužíváme LIMITKU.

Required CBAR. (pouze se změnou ceny)

nepotvrzený CBAR bez minticku (pouze se změnou ceny)
- se používá pro žízení prodeje

potvrzený CBAR 
- se používá pro BUY


"""
stratvars = AttributeDict(maxpozic = 400,
                          def_mode_from = 200,
                          chunk = 10,
                          MA = 2,
                          Trend = 2,
                          profit = 0.02,
                          def_profit = 0.01,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None,
                          limitka_price = None,
                          jevylozeno=0,
                          vykladka=5,
                          curve = [0.01, 0.01, 0.01, 0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01],
                          curve_def = [0.02, 0.02, 0.02, 0, 0, 0.02, 0, 0, 0, 0.02],
                          blockbuy = 0,
                          ticks2reset = 0.04,
                          consolidation_bar_count = 10,
                          slope_lookback = 300,
                          lookback_offset = 20,
                          minimum_slope = -0.05,
                          first_buy_market = False
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
    #ic(state.avgp, state.positions)
    #ic(state.vars)
    #ic(data)

    #
    def is_defensive_mode():
        akt_pozic = int(state.positions)
        max_pozic = int(state.vars.maxpozic)
        def_mode_from = safe_get(state.vars, "def_mode_from",max_pozic/2)
        if akt_pozic >= int(def_mode_from):
            #state.ilog(e=f"DEFENSIVE mode ACTIVE {state.vars.def_mode_from=}", msg=state.positions)
            return True
        else:
            #state.ilog(e=f"STANDARD mode ACTIVE {state.vars.def_mode_from=}", msg=state.positions)
            return False
    
    def get_limitka_price():
        def_profit = safe_get(state.vars, "def_profit",state.vars.profit) 
        cena = float(state.avgp)
        #v MYSELL hrajeme i na 3 desetinna cisla - TBD mozna hrat jen na 5ky (0.125, 0.130, 0.135 atp.)
        if is_defensive_mode():
            return price2dec(cena+get_tick(cena,float(def_profit)),3)
        else:
            return price2dec(cena+get_tick(cena,float(state.vars.profit)),3)
        
    def consolidation():
        ##CONSOLIDATION PART - moved here, musí být před nákupem, jinak to dělalo nepořádek v pendingbuys
        #docasne zkusime konzolidovat i kdyz neni vylozeno (aby se srovnala limitka ve vsech situacich)
        if state.vars.jevylozeno == 1 or 1==1:
            ##CONSOLIDATION PART kazdy Nty bar dle nastaveni
            if int(data["index"])%int(state.vars.consolidation_bar_count) == 0:
                print("***CONSOLIDATION ENTRY***")
                state.ilog(e="CONSOLIDATION ENTRY ***")

                orderlist = state.interface.get_open_orders(symbol=state.symbol, side=None)
                #pro jistotu jeste dotahneme aktualni pozice
                state.avgp, state.positions = state.interface.pos()            

                #print(orderlist)
                pendingbuys_new = {}
                #zaciname s cistym stitem
                state.vars.limitka = None
                state.vars.limitka_price = None
                for o in orderlist:
                    if o.side == OrderSide.BUY and o.order_type == OrderType.LIMIT:
                        pendingbuys_new[str(o.id)]=float(o.limit_price)

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

                print("***CONSOLIDATION EXIT***")
                state.ilog(e="CONSOLIDATION EXIT ***")
            else:
                state.ilog(e="No time for consolidation", msg=data["index"])
                print("no time for consolidation", data["index"])
    #mozna presunout o level vys
    def vyloz():
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        #curve = [0.01, 0.01, 0, 0, 0.01, 0, 0, 0, 0.02, 0, 0, 0, 0.03, 0,0,0,0,0, 0.02, 0,0,0,0,0,0, 0.02]
        curve = state.vars.curve
        ##defenzivni krivka pro 
        curve_def = state.vars.curve_def
        #vykladani po 5ti kusech, když zbývají 2 a méně, tak děláme nový výklad
        vykladka = state.vars.vykladka
        #kolik muzu max vylozit
        kolikmuzu = int((int(state.vars.maxpozic) - int(state.positions))/int(state.vars.chunk))
        akt_pozic = int(state.positions)
        max_pozic = int(state.vars.maxpozic)

        if akt_pozic >= max_pozic:
            state.ilog(e="MAX pozic reached, cannot vyklad")
            return
        
        #mame polovinu a vic vylozeno, pouzivame defenzicni krivku
        if is_defensive_mode():
            state.ilog(e="DEF: Pouzivame defenzivni krivku", akt_pozic=akt_pozic, max_pozic=max_pozic, curve_def=curve_def)
            curve = curve_def
            #zaroven docasne menime ticks2reset na defenzivni 0.06
            state.vars.ticks2reset = 0.06
            state.ilog(e="DEF: Menime tick2reset na 0.06", ticks2reset=state.vars.ticks2reset, ticks2reset_backup=state.vars.ticks2reset_backup)
        else:
            #vracime zpet, pokud bylo zmeneno
            if state.vars.ticks2reset != state.vars.ticks2reset_backup:
                state.vars.ticks2reset = state.vars.ticks2reset_backup
                state.ilog(e="DEF: Menime tick2reset zpet na"+str(state.vars.ticks2reset), ticks2reset=state.vars.ticks2reset, ticks2reset_backup=state.vars.ticks2reset_backup)

        if kolikmuzu < vykladka: vykladka = kolikmuzu

        if len(curve) < vykladka:
            vykladka = len(curve)
        qty = int(state.vars.chunk)
        last_price = price2dec(state.interface.get_last_price(state.symbol))
        #profit = float(state.vars.profit)
        price = last_price
        state.ilog(e="BUY Vykladame", msg=f"first price {price=} {vykladka=}", curve=curve, ema=state.indicators.ema[-1], trend=state.vars.Trend, price=price, vykladka=vykladka)
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        
        ##VAR - na zaklade conf. muzeme jako prvni posilat MARKET order
        if safe_get(state.vars, "first_buy_market") == True:
            #pri defenzivnim rezimu pouzivame vzdy LIMIT order
            if is_defensive_mode():
                state.ilog(e="DEF mode on, odesilame jako prvni limitku")
                state.buy_l(price=price, size=qty)
            else:
                state.ilog(e="Posilame jako prvni MARKET order")
                state.buy(size=qty)
        else:
            state.buy_l(price=price, size=qty)
        print("prvni limitka na aktuální cenu. Další podle křivky", price, qty)
        for i in range(0,vykladka-1):
            price = price2dec(float(price - get_tick(price, curve[i])))
            if price == last_price:
                qty = qty + int(state.vars.chunk)
            else:
                state.buy_l(price=price, size=qty)
                #print(i,"BUY limitka - delta",curve[i]," cena:", price, "mnozstvi:", qty)
                qty = int(state.vars.chunk)
            last_price = price
        state.vars.blockbuy = 1
        state.vars.jevylozeno = 1
        state.vars.last_buysignal_index = data['index']

    def eval_sell():
        """"
        TBD
        Když je RSI nahoře tak neprodávat, dokud 1) RSI neprestane stoupat 2)nedosahne to nad im not greedy limit
        """
        ##mame pozice
        ##aktualni cena je vetsi nebo rovna cene limitky
        #muzeme zde jet i na pulcenty
        curr_price = float(data['close'])
        state.ilog(e="Eval SELL", price=curr_price, pos=state.positions, sell_in_progress=state.vars.sell_in_progress)
        if int(state.positions) > 0 and state.vars.sell_in_progress is False:
            goal_price = get_limitka_price()
            state.ilog(e=f"Goal price {goal_price}")
            if curr_price>=goal_price:

                #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                #TODO mozna cekat na nejaky signal RSI
                #TODO pripadne pokud dosahne TGTBB prodat ihned

                #OPTIMALIZACE pri stoupajícím angle
                if sell_protection_enabled() is False:
                    state.interface.sell(size=state.positions)
                    state.vars.sell_in_progress = True
                    state.ilog(e=f"market SELL was sent {curr_price=}", positions=state.positions, avgp=state.avgp, sellinprogress=state.vars.sell_in_progress)

    def populate_ema_indicator():
        #BAR EMA INDICATOR - 
        #plnime MAcko - nyni posilame jen N poslednich hodnot
        #zaroven osetrujeme pripady, kdy je malo dat a ukladame nulu
        try:
            ma = int(state.vars.MA)
            #poslednich ma hodnot
            source = state.bars.close[-ma:] #state.bars.vwap
            ema_value = ema(source, ma)

            ##pokus MACKO zakrouhlit na tri desetina a petku
            state.indicators.ema[-1]=round2five(ema_value[-1])
            ##state.indicators.ema[-1]=trunc(ema_value[-1],3)
            #state.ilog(e=f"EMA {state.indicators.ema[-1]}", ema_last=state.indicators.ema[-6:])
        except Exception as e:
            state.ilog(e="EMA nechavame  0", message=str(e)+format_exc())
            #state.indicators.ema[-1]=(0)
            #evaluate buy signal
            #consolidation

    def populate_slope_indicator():
        #SLOPE INDICATOR
        #úhel stoupání a klesání vyjádřený mezi -1 až 1
        #pravý bod přímky je aktuální cena, levý je průměr X(lookback offset) starších hodnot od slope_lookback.
        #obsahuje statický indikátor (angle) pro vizualizaci
        try:
            slope = 99
            slope_lookback = int(state.vars.slope_lookback)
            minimum_slope = float(state.vars.minimum_slope)
            lookback_offset = int(state.vars.lookback_offset)

            if len(state.bars.close) > (slope_lookback + lookback_offset):
                array_od = slope_lookback + lookback_offset
                array_do = slope_lookback
                lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                #obycejný prumer hodnot
                lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)

                #výpočet úhlu - a jeho normalizace
                slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
                slope = round(slope, 4)
                state.indicators.slope[-1]=slope
    
                #angle je ze slope
                state.statinds.angle = dict(time=state.bars.time[-1], price=state.bars.close[-1], lookbacktime=state.bars.time[-slope_lookback], lookbackprice=lookbackprice, minimum_slope=minimum_slope)
    
                #slope MA vyrovna vykyvy ve slope, dále pracujeme se slopeMA
                slope_MA_length = 5
                source = state.indicators.slope[-slope_MA_length:]
                slopeMAseries = ema(source, slope_MA_length) #state.bars.vwap
                slopeMA = slopeMAseries[-1]
                state.indicators.slopeMA[-1]=slopeMA

                state.ilog(e=f"{slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators.slope[-10:], last_slopesMA=state.indicators.slopeMA[-10:])

                #dale pracujeme s timto MAckovanym slope
                slope = slopeMA         
            else:
                #pokud plnime historii musime ji plnit od zacatku, vsehcny idenitifkatory maji spolecny time
                #kvuli spravnemu zobrazovani na gui
                #state.indicators.slopeMA[-1]=0
                #state.indicators.slopeMA.append(0)
                state.ilog(e="Slope - not enough data", slope_lookback=slope_lookback, slope=state.indicators.slope, slopeMA=state.indicators.slopeMA)
        except Exception as e:
            print("Exception in NEXT Slope Indicator section", str(e))
            state.ilog(e="EXCEPTION", msg="Exception in Slope Indicator section" + str(e) + format_exc())

    def populate_rsi_indicator():
            #RSI14 INDICATOR
        try:
            rsi_length = int(safe_get(state.vars, "rsi_length",14))
            source = state.bars.close #[-rsi_length:] #state.bars.vwap
            rsi_res = rsi(source, rsi_length)
            rsi_value = trunc(rsi_res[-1],3)
            state.indicators.RSI14[-1]=rsi_value
            #state.ilog(e=f"RSI {rsi_length=} {rsi_value=} {rsi_dont_buy=} {rsi_buy_signal=}", rsi_indicator=state.indicators.RSI14[-5:])
        except Exception as e:
            state.ilog(e=f"RSI {rsi_length=} necháváme 0", message=str(e)+format_exc())
            #state.indicators.RSI14[-1]=0

    def slope_too_low():
        return state.indicators.slopeMA[-1] < float(state.vars.minimum_slope)
    
    def slope_too_high():
        return state.indicators.slopeMA[-1] > float(safe_get(state.vars, "bigwave_slope_above",0.20))

    #resetujeme, kdyz 1) je aktivni buy protection 2) kdyz to ujede
    #TODO mozna tick2reset spoustet jednou za X opakovani
    def pendingbuys_optimalization():
        if len(state.vars.pendingbuys)>0:
            if buy_protection_enabled():
                #state.ilog(e="PENDINGBUYS reset", message=inspect.currentframe().f_code.co_name)
                res = asyncio.run(state.cancel_pending_buys())
                state.ilog(e="CANCEL pendingbuyes", pb=state.vars.pendingbuys, res=res)
            else:
                #pokud mame vylozeno a cena je vetsi nez tick2reset 
                maxprice = max(state.vars.pendingbuys.values())
                if state.interface.get_last_price(state.symbol) > float(maxprice) + get_tick(maxprice, float(state.vars.ticks2reset)):
                    res = asyncio.run(state.cancel_pending_buys())
                    state.ilog(e=f"UJELO to. Rusime PB", msg=f"{state.vars.ticks2reset=}", pb=state.vars.pendingbuys)

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
                state.ilog(e="PB prazdne nastavujeme: neni vylozeno", jevylozeno=state.vars.jevylozeno)

    ##kdy nenakupovat - tzn. neprojdou nakupy a kdyz uz jsou tak se zrusi
    def buy_protection_enabled():
        dont_buy_when = dict(AND=dict(), OR=dict())
        ##add conditions here
        dont_buy_when['rsi_too_high'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
        dont_buy_when['slope_too_low'] = slope_too_low()

        result, cond_met = eval_cond_dict(dont_buy_when)
        if result:
            state.ilog(e=f"BUY_PROTECTION {cond_met}")
        return result

    def sell_protection_enabled():
        dont_sell_when = dict(AND=dict(), OR=dict())
        ##add conditions here

        #IDENTIFIKOVAce rustoveho MOMENTA - pokud je momentum, tak prodávat později
        
        #pokud je slope too high, pak prodavame jakmile slopeMA zacne klesat, napr. 4MA (TODO 3)

        #toto docasne pryc dont_sell_when['slope_too_high'] = slope_too_high() and not isfalling(state.indicators.slopeMA,4)
        dont_sell_when['AND']['slopeMA_rising'] = isrising(state.indicators.slopeMA,2)
        dont_sell_when['AND']['rsi_not_falling'] = not isfalling(state.indicators.RSI14,3)
        #dont_sell_when['rsi_dont_buy'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
 
        result, conditions_met = eval_cond_dict(dont_sell_when)
        if result:
            state.ilog(e=f"SELL_PROTECTION {conditions_met} enabled")
        return result

    #preconditions and conditions of BUY SIGNAL
    def buy_conditions_met():
        #preconditions
        dont_buy_when = dict(AND=dict(), OR=dict())
        dont_buy_when['bar_not_confirmed'] = (data['confirmed'] == 0)
        #od posledniho vylozeni musi ubehnout N baru
        dont_buy_when['last_buy_offset_too_soon'] =  data['index'] < (state.vars.last_buysignal_index + safe_get(state.vars, "lastbuy_offset",3))
        dont_buy_when['blockbuy_active'] = (state.vars.blockbuy == 1)
        dont_buy_when['jevylozeno_active'] = (state.vars.jevylozeno == 1)
        #dont_buy_when['buy_protection_enabled'] = buy_protection_enabled()
        dont_buy_when['open_rush'] = is_open_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "open_rush",0))
        dont_buy_when['close_rush'] = is_close_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "close_rush",0))
        dont_buy_when['rsi_is_zero'] = (state.indicators.RSI14[-1] == 0)

        #testing preconditions
        result, cond_met = eval_cond_dict(dont_buy_when)
        if result:
            state.ilog(e=f"BUY precondition not met {cond_met}")
            return False

        #conditions - bud samostatne nebo v groupe - ty musi platit dohromady
        buy_cond = dict(AND=dict(), OR=dict())
        ##add buy conditions here
        #cond groups ["AND"]
        #cond groups ["OR"]
        #no cond group - takes first
        #TEST BUY SIGNALu z cbartick_price - 3klesave za sebou
        #buy_cond['tick_price_falling_trend'] = isfalling(state.cbar_indicators.tick_price,state.vars.Trend)

        #slopeMA jde dolu, rsi jde nahoru
        #buy mame kazdy potvrzeny, tzn. rsi falling muze byt jen 2
        
        #buy_cond['AND']['slopeMA_falling'] = isfalling(state.indicators.slopeMA,3)
        #buy_cond['AND']['rsi_is_rising'] = isrising(state.indicators.RSI14,2)
        #buy_cond["AND"]["rsi_buy_signal_below"] = state.indicators.RSI14[-1] < safe_get(state.vars, "rsi_buy_signal_below",40)

        #puvodni buy conditiony
        #buy_cond["AND"]["rsi_buy_signal_below"] = state.indicators.RSI14[-1] < safe_get(state.vars, "rsi_buy_signal_below",40)
        #buy_cond["AND"]["ema_trend_is_falling"] = isfalling(state.indicators.ema,state.vars.Trend)

        #pouze RSI pod 35 a zadny jiny
        buy_cond["AND"]["rsi_buy_signal_below"] = state.indicators.RSI14[-1] < safe_get(state.vars, "rsi_buy_signal_below",40)

        result, conditions_met = eval_cond_dict(buy_cond)
        if result:
            state.ilog(e=f"BUY SIGNAL {conditions_met}")
        return result

    def eval_buy():
        if buy_conditions_met():
                vyloz()

    def populate_cbar_tick_price_indicator():
        try:
            #pokud v potvrzovacím baru nebyly zmeny, nechavam puvodni hodnoty
            # if tick_delta_volume == 0:
            #     state.indicators.tick_price[-1] = state.indicators.tick_price[-2]
            #     state.indicators.tick_volume[-1] = state.indicators.tick_volume[-2]
            # else:

            tick_price = round2five(data['close'])
            tick_delta_volume = data['volume'] - state.vars.last_tick_volume

            #docasne dame pryc volume deltu a davame absolutni cislo
            state.cbar_indicators.tick_price[-1] = tick_price
            state.cbar_indicators.tick_volume[-1] = tick_delta_volume
        except:
            pass

        state.ilog(e=f"TICK PRICE {tick_price} VOLUME {tick_delta_volume} {conf_bar=}", prev_price=state.vars.last_tick_price, prev_volume=state.vars.last_tick_volume)

        state.vars.last_tick_price = tick_price
        state.vars.last_tick_volume = data['volume']

    def get_last_ind_vals():
        last_ind_vals = {}
        #print(state.indicators.items())
        for key in state.indicators:
            if key != 'time':
                last_ind_vals[key] = state.indicators[key][-5:]
        
        for key in state.cbar_indicators:
            if key != 'time':
                last_ind_vals[key] = state.cbar_indicators[key][-5:]    
        return last_ind_vals

    conf_bar = data['confirmed'] 
    state.ilog(e=f"---{data['index']}-{conf_bar}--")

    #kroky pro CONFIRMED BAR only
    if conf_bar == 1:
        #logika pouze pro potvrzeny bar
        state.ilog(e="BAR potvrzeny")


        #pri potvrzem CBARu nulujeme counter volume pro tick based indicator
        state.vars.last_tick_volume = 0
        state.vars.next_new = 1

    #kroky pro CONTINOUS TICKS only
    else:
        #CBAR INDICATOR pro tick price a deltu VOLUME
        populate_cbar_tick_price_indicator()

    #SPOLECNA LOGIKA - bar indikatory muzeme populovat kazdy tick (dobre pro RT GUI), ale uklada se stejne az pri confirmu
    populate_ema_indicator()
    populate_slope_indicator()
    populate_rsi_indicator()
    eval_sell()
    consolidation()

    #HLAVNI ITERACNI LOG JESTE PRED AKCI - obsahuje aktualni hodnoty vetsiny parametru
    lp = state.interface.get_last_price(symbol=state.symbol)
    state.ilog(e="ENTRY", msg=f"LP:{lp} P:{state.positions}/{round(float(state.avgp),3)} profit:{round(float(state.profit),2)} Trades:{len(state.tradeList)} DEF:{str(is_defensive_mode())}", last_price=lp, data=data, stratvars=state.vars)
    state.ilog(e="Indikatory", msg=str(get_last_ind_vals()))

    eval_buy()
    pendingbuys_optimalization()

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)

    state.vars['sell_in_progress'] = False
    state.vars.last_tick_price = 0
    state.vars.last_tick_volume = 0
    state.vars.next_new = 0
    state.vars.last_buysignal_index = 0
    #state.cbar_indicators['ivwap'] = []
    state.cbar_indicators['tick_price'] = []
    state.cbar_indicators['tick_volume'] = []
    state.indicators['ema'] = []
    state.indicators['slope'] = []
    state.indicators['slopeMA'] = []
    state.indicators['RSI14'] = []
    #static indicators - those not series based
    state.statinds['angle'] = dict(minimum_slope=state.vars["minimum_slope"], maximum_slope=safe_get(state.vars, "bigwave_slope_above",0.20))
    state.vars["ticks2reset_backup"] = state.vars.ticks2reset

def main():
    name = os.path.basename(__file__)
    se = Event()
    pe = Event()
    s = StrategyOrderLimitVykladaciNormalizedMYSELL(name = name, symbol = "BAC", account=Account.ACCOUNT1, next=next, init=init, stratvars=stratvars, open_rush=10, close_rush=0, pe=pe, se=se, ilog_save=True)
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




 
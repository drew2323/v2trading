import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account, OrderSide, OrderType
from v2realbot.indicators.indicators import ema
from v2realbot.indicators.oscillators import rsi
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY, price2dec, print, safe_get, get_tick, round2five, is_open_rush, is_close_rush, eval_cond_dict, Average, crossed_down, crossed_up, is_pivot
from datetime import datetime
#from icecream import install, ic
#from rich import print
from threading import Event
from msgpack import packb, unpackb
import asyncio
import os
from traceback import format_exc

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
    
    def get_profit_price():
        def_profit = safe_get(state.vars, "def_profit",state.vars.profit) 
        cena = float(state.avgp)
        #v MYSELL hrajeme i na 3 desetinna cisla - TBD mozna hrat jen na 5ky (0.125, 0.130, 0.135 atp.)
        if is_defensive_mode():
            return price2dec(cena+get_tick(cena,float(def_profit)),3)
        else:
            return price2dec(cena+get_tick(cena,float(state.vars.profit)),3)
        
    def get_max_profit_price():
        max_profit = float(safe_get(state.vars, "max_profit",0.03))
        cena = float(state.avgp)
        return price2dec(cena+get_tick(cena,max_profit),3)        
        
    def optimize_qty_multiplier():
        akt_pozic = int(state.positions)/int(state.vars.chunk)
        multiplier = 1

        #zatim jednoduse pokud je akt. pozice 1 nebo 3 chunky (<4) tak zdvojnásubuju
        #aneb druhy a treti nakup
        if akt_pozic > 0 and akt_pozic < 4:
            multiplier = safe_get(state.vars, "market_buy_multiplier", 1)
        state.ilog(e=f"BUY MULTIPLIER: {multiplier}")
        return multiplier


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
                    state.ilog(e="PB sedi nechavame", pb_new=pendingbuys_new, pb_old = str(state.vars.pendingbuys))
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
        state.ilog(e="BUY Vykladame", msg=f"first price {price=} {vykladka=}", curve=curve, price=price, vykladka=vykladka)
        ##prvni se vyklada na aktualni cenu, další jdou podle krivky, nula v krivce zvyšuje množství pro následující iteraci
        
        ##VAR - na zaklade conf. muzeme jako prvni posilat MARKET order
        if safe_get(state.vars, "first_buy_market") == True:
            #pri defenzivnim rezimu pouzijeme LIMIT nebo MARKET podle nastaveni 
            if is_defensive_mode() and safe_get(state.vars, "first_buy_market_def_mode", False) is False:
                state.ilog(e="DEF mode on, odesilame jako prvni limitku")
                state.buy_l(price=price, size=qty)
            else:
                state.ilog(e="Posilame jako prvni MARKET order")
                #market size optimalization based on conditions
                state.buy(size=optimize_qty_multiplier()*qty)
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
        state.vars.lastbuyindex = data['index']

    def eval_sell():
        """"
        TBD
        Když je RSI nahoře tak neprodávat, dokud 1) RSI neprestane stoupat 2)nedosahne to nad im not greedy limit
        """
        ##mame pozice
        ##aktualni cena je vetsi nebo rovna cene limitky
        #muzeme zde jet i na pulcenty
        curr_price = float(data['close'])
        state.ilog(e="Eval SELL", price=curr_price, pos=state.positions, avgp=state.avgp, sell_in_progress=state.vars.sell_in_progress)
        if int(state.positions) > 0 and float(state.avgp)>0 and state.vars.sell_in_progress is False:
            goal_price = get_profit_price()
            max_price = get_max_profit_price()
            state.ilog(e=f"Goal price {goal_price} max price {max_price}")
            
            #pokud je cena vyssi
            if curr_price>=goal_price:

                #TODO cekat az slope prestane intenzivn erust, necekat az na klesani
                #TODO mozna cekat na nejaky signal RSI
                #TODO pripadne pokud dosahne TGTBB prodat ihned
                max_price_signal = curr_price>=max_price
                #OPTIMALIZACE pri stoupajícím angle
                if max_price_signal or sell_protection_enabled() is False:
                    state.interface.sell(size=state.positions)
                    state.vars.sell_in_progress = True
                    state.ilog(e=f"market SELL was sent {curr_price=} {max_price_signal=}", positions=state.positions, avgp=state.avgp, sellinprogress=state.vars.sell_in_progress)
            #pokud je cena nizsi, testujeme REVERSE POZITION PROTECTION
            else:
                pass
                #reverse_position()

    # def reverse_position():
    #     """"
    #     Reverse position - ochrana pred vetsim klesanim
    #     - proda kdyz je splnena podminka
    #     - nakoupi opet ve stejnem mnozstvi, kdyz je splnena podminka 

    #     required STRATVARS:
    #     reverse_position_slope = -0.9
    #     reverse_position_on_confirmed_only = true
    #     reverse_position_waiting_amount = 0
    #     """""
    #     #reverse position preconditions
    #     dont_do_reverse_when = {}
    
    #     dont_do_reverse_when['reverse_position_waiting_amount_not_0'] = (state.vars.reverse_position_waiting_amount != 0)
    
    #     result, conditions_met = eval_cond_dict(dont_do_reverse_when)
    #     if result:
    #         state.ilog(e=f"REVERSE_PRECOND PROTECTION {conditions_met}")
    #         return result


    #     #reverse position for
    #     confirmrequried = safe_get(state.vars, "reverse_position_on_confirmed_only", True)
    #     if (confirmrequried and data['confirmed'] == 1) or confirmrequried is False:
    #         #check reverse position 
    #         state.ilog(e="REVERSE POSITION check - GO")
    #     else:
    #         #not time for reverse position
    #         state.ilog(e="REVERSE POSITION check - NO TIME")

    #     #predpokladame, ze uz byly testovany pozice a mame je if int(state.positions) > 0 and float(state.avgp)>0 
    #     if state.indicators.slopeMA[-1] < float(safe_get(state.vars, "reverse_position_slope", -0.10)):
    #         state.interface.sell(size=state.positions)
    #         state.vars.sell_in_progress = True
    #         state.ilog(e=f"REV POS market SELL was sent {curr_price=}", positions=state.positions, avgp=state.avgp, sellinprogress=state.vars.sell_in_progress)
    #         state.vars.rev_position_waiting_amount = 



    # None - standard, defaults mode - attributes are read from general stratvars section
    # other modes - attributtes are read from mode specific stratvars section, defaults to general section
    #WIP
    def set_mode():
        state.vars.mode = None
        
    #dotahne hodnotu z prislusne sekce
    #pouziva se namisto safe_get
    # stratvars
    #       buysignal = 1
    #  stratvars.mode1
    #       buysignal = 2
    # PARAMS:
    # - section: napr. stratvars.buysignal
    # - var name: MA_length
    # - default: defaultní hodnota, kdyz nenalezeno
    # Kroky: 1) 
    # vrati danou hodnotu nastaveni podle aktualniho modu state.vars.mode
    # pokud je None, vrati pro standardni mod, pokud neni nalezeno vrati default
    # EXAMPLE:
    # get_modded_vars("state")
    #get_modded_vars(state.vars, 'buysignal', 1) - namista safe_get

    #WIP
    def get_modded_vars(section,  name: str, default = None):
        if state.vars.mode is None:
            return safe_get(section, name, default)
        else:
            try:
                modded_section = section[state.vars.mode]
            except KeyError:
                modded_section = section
            return safe_get(modded_section, name, safe_get(section, name, default))

    def populate_cbar_rsi_indicator():
        #CBAR RSI indicator
        options = safe_get(state.vars.indicators, 'crsi', None)
        if options is None:
            state.ilog(e="No options for crsi in stratvars")
            return

        try:
            crsi_length = int(safe_get(options, 'crsi_length', 14))
            source = state.cbar_indicators.tick_price #[-rsi_length:] #state.bars.vwap
            crsi_res = rsi(source, crsi_length)
            crsi_value = crsi_res[-1]
            if str(crsi_value) == "nan":
                crsi_value = 0
            state.cbar_indicators.CRSI[-1]=crsi_value
            #state.ilog(e=f"RSI {rsi_length=} {rsi_value=} {rsi_dont_buy=} {rsi_buy_signal=}", rsi_indicator=state.indicators.RSI14[-5:])
        except Exception as e:
            state.ilog(e=f"CRSI {crsi_length=} necháváme 0", message=str(e)+format_exc())
            #state.indicators.RSI14[-1]=0

    #resetujeme, kdyz 1) je aktivni buy protection 2) kdyz to ujede
    #TODO mozna tick2reset spoustet jednou za X opakovani
    def pendingbuys_optimalization():
        if len(state.vars.pendingbuys)>0:
            #misto volani buy_protection vytvarime direktivu cancel_pendingbuys

            #pouze jako OR
            #cancel_pendingbuys_above
            #cancel_pendingbuys_below

            pb_dict= get_work_dict_with_directive(starts_with="cancel_pendingbuys_if")
            
            state.ilog(e=f"CANCEL PB work_dict", message=pb_dict)
            #u techto ma smysl pouze OR
            cond = create_conditions_from_directives(pb_dict, "OR")
            result, conditions_met = eval_cond_dict(cond)
            state.ilog(e=f"CANCEL PB =OR= {result}", **conditions_met)
            if result:
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

    def sell_protection_enabled():
        options = safe_get(state.vars, 'sell_protection', None)
        if options is None:
            state.ilog(e="No options for sell protection in stratvars")
            return False
        
        disable_sell_proteciton_when = dict(AND=dict(), OR=dict())

        #preconditions
        disable_sell_proteciton_when['disabled_in_config'] = safe_get(options, 'enabled', False) is False
        #too good to be true (maximum profit)
        #disable_sell_proteciton_when['tgtbt_reached'] = safe_get(options, 'tgtbt', False) is False
        disable_sell_proteciton_when['disable_if_positions_above'] = int(safe_get(options, 'disable_if_positions_above', 0)) < state.positions

        #testing preconditions
        result, conditions_met = eval_cond_dict(disable_sell_proteciton_when)
        if result:
            state.ilog(e=f"SELL_PROTECTION DISABLED by {conditions_met}", **conditions_met)
            return False
        
        work_dict_dont_sell_if = get_work_dict_with_directive(starts_with="dont_sell_if")
        state.ilog(e=f"SELL PROTECTION work_dict", message=work_dict_dont_sell_if)

        or_cond = create_conditions_from_directives(work_dict_dont_sell_if, "OR")
        result, conditions_met = eval_cond_dict(or_cond)
        state.ilog(e=f"SELL PROTECTION =OR= {result}", **conditions_met)
        if result:
            return True
        
        #OR neprosly testujeme AND
        and_cond = create_conditions_from_directives(work_dict_dont_sell_if, "AND")
        result, conditions_met = eval_cond_dict(and_cond)
        state.ilog(e=f"SELL PROTECTION =AND= {result}", **conditions_met)
        return result    

        # #IDENTIFIKOVAce rustoveho MOMENTA - pokud je momentum, tak prodávat později
        
        # #pokud je slope too high, pak prodavame jakmile slopeMA zacne klesat, napr. 4MA (TODO 3)

        # #TODO zkusit pro pevny profit, jednoduse pozdrzet prodej - dokud tick_price roste nebo se drzi tak neprodavat, pokud klesne prodat
        # #mozna mit dva mody - pri vetsi volatilite pouzivat momentum, pri mensi nebo kdyz potrebuju pryc, tak prodat hned

        #puvodni nastaveni
#         slopeMA_rising = 2
#         rsi_not_falling = 3


        # #testing preconditions
        # result, conditions_met = eval_cond_dict(disable_sell_proteciton_when)
        # if result:
        #     state.ilog(e=f"SELL_PROTECTION DISABLED by precondition {conditions_met}")
        #     return False

        # dont_sell_when = dict(AND=dict(), OR=dict())
        # ##add conditions here

        # #IDENTIFIKOVAce rustoveho MOMENTA - pokud je momentum, tak prodávat později
        
        # #pokud je slope too high, pak prodavame jakmile slopeMA zacne klesat, napr. 4MA (TODO 3)

        # #TODO zkusit pro pevny profit, jednoduse pozdrzet prodej - dokud tick_price roste nebo se drzi tak neprodavat, pokud klesne prodat
        # #mozna mit dva mody - pri vetsi volatilite pouzivat momentum, pri mensi nebo kdyz potrebuju pryc, tak prodat hned

        # #TOTO do budoucna zdynamictit

        # #toto docasne pryc dont_sell_when['slope_too_high'] = slope_too_high() and not isfalling(state.indicators.slopeMA,4)
        # dont_sell_when['AND']['slopeMA_rising'] = isrising(state.indicators.slopeMA,safe_get(options, 'slopeMA_rising', 2))
        # dont_sell_when['AND']['rsi_not_falling'] = not isfalling(state.indicators.RSI14,safe_get(options, 'rsi_not_falling',3))
        # #dont_sell_when['rsi_dont_buy'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
 
        # result, conditions_met = eval_cond_dict(dont_sell_when)
        # if result:
        #     state.ilog(e=f"SELL_PROTECTION {conditions_met} enabled")
        # return result

    #preconditions and conditions of BUY SIGNAL
    def conditions_met():
        #preconditions - TODO zdynamictit
        dont_buy_when = dict(AND=dict(), OR=dict())

        #OBECNE DONT BUYS
        if safe_get(state.vars, "buy_only_on_confirmed",True):
            dont_buy_when['bar_not_confirmed'] = (data['confirmed'] == 0)
        #od posledniho vylozeni musi ubehnout N baru
        dont_buy_when['last_buy_offset_too_soon'] =  data['index'] < (int(state.vars.lastbuyindex) + int(safe_get(state.vars, "lastbuy_offset",3)))
        dont_buy_when['blockbuy_active'] = (state.vars.blockbuy == 1)
        dont_buy_when['jevylozeno_active'] = (state.vars.jevylozeno == 1)
        dont_buy_when['open_rush'] = is_open_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "open_rush",0))
        dont_buy_when['close_rush'] = is_close_rush(datetime.fromtimestamp(data['updated']).astimezone(zoneNY), safe_get(state.vars, "close_rush",0))
    
        #testing preconditions
        result, cond_met = eval_cond_dict(dont_buy_when)
        if result:
            state.ilog(e=f"BUY PRECOND GENERAL not met {cond_met}", message=cond_met)
            return False

        #SPECIFICKE DONT BUYS - direktivy zacinajici dont_buy
        #dont_buy_below = value nebo nazev indikatoru
        #dont_buy_above = value nebo hazev indikatoru

        #do INITU
        work_dict_dont_buy = get_work_dict_with_directive(starts_with="dont_buy_if")
        
        state.ilog(e=f"BUY PRECOND DONTBUY work_dict", message=work_dict_dont_buy)
        #u techto ma smysl pouze OR
        precond = create_conditions_from_directives(work_dict_dont_buy, "OR")
        result, conditions_met = eval_cond_dict(precond)
        state.ilog(e=f"BUY PRECOND DONTBUY =OR= {result}", **conditions_met)
        if result:
            return False

        #tyto timto nahrazeny - dat do konfigurace
        #dont_buy_when['rsi_too_high'] = state.indicators.RSI14[-1] > safe_get(state.vars, "rsi_dont_buy_above",50)
        #dont_buy_when['slope_too_low'] = slope_too_low()
        #dont_buy_when['slope_too_high'] = slope_too_high()
        #dont_buy_when['rsi_is_zero'] = (state.indicators.RSI14[-1] == 0)
        #dont_buy_when['reverse_position_waiting_amount_not_0'] = (state.vars.reverse_position_waiting_amount != 0)



        #u indikatoru muzoun byt tyto directivy pro generovani buysignalu
        # buy_if_crossed_down - kdyz prekrocil dolu, VALUE: hodnota nebo nazev indikatoru
        # buy_if_crossed_up - kdyz prekrocil nahoru, VALUE: hodnota nebo nazev indikatoru
        # buy_if_falling - kdyz je klesajici po N, VALUE: hodnota
        # buy_if_rising - kdyz je rostouci po N, VALUE: hodnota
        # buy_if_below - kdyz je pod prahem, VALUE: hodnota nebo nazev indikatoru
        # buy_if_above - kdyz je nad prahem, VALUE: hodnota nebo nazev indikatoru
        # buy_if_pivot_a - kdyz je pivot A. VALUE: delka nohou
        # buy_if_pivot_v - kdyz je pivot V. VALUE: delka nohou
        
        # direktivy se mohou nachazet v podsekci AND nebo OR - daneho indikatoru (nebo na volno, pak = OR)
        # OR - staci kdyz plati jedna takova podminka a buysignal je aktivni
        # AND - musi platit vsechny podminky ze vsech indikatoru, aby byl buysignal aktivni

        #populate work dict - muze byt i jen jednou v INIT nebo 1x za cas
        #dict oindexovane podminkou (OR/AND) obsahuje vsechny buy_if direktivy v tuplu (nazevind,direktiva,hodnota
        # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
        work_dict_buy_if = get_work_dict_with_directive(starts_with="buy_if")
        state.ilog(e=f"BUY SIGNAL work_dict", message=work_dict_buy_if)

        buy_or_cond = create_conditions_from_directives(work_dict_buy_if, "OR")
        result, conditions_met = eval_cond_dict(buy_or_cond)
        state.ilog(e=f"BUY SIGNAL =OR= {result}", **conditions_met)
        if result:
            return True
        
        #OR neprosly testujeme AND
        buy_and_cond = create_conditions_from_directives(work_dict_buy_if, "AND")
        result, conditions_met = eval_cond_dict(buy_and_cond)
        state.ilog(e=f"BUY SIGNAL =AND= {result}", **conditions_met)
        return result      

    #preklad direktivy podle typu, pokud je int anebo float - je to primo hodnota
    #pokud je str, jde o indikator a dotahujeme posledni hodnotu z nej
    def value_or_indicator(value):
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            try:
                #pokud existuje MA bereme MA jinak standard
                ret = get_source_or_MA(indicator=value)[-1]
                state.ilog(e=f"Pro porovnani bereme posledni hodnotu {ret} z indikatoru {value}")
            except Exception as e   :
                ret = 0
                state.ilog(e=f"Neexistuje indikator s nazvem {value} vracime 0" + str(e) + format_exc())
            return ret

    #funkce vytvori podminky (bud pro AND/OR) z pracovniho dict
    def create_conditions_from_directives(work_dict, cond_type):
        cond = {}
        cond[cond_type] = {}
        for indname, directive, value in work_dict[cond_type]:
            #direktivy zobecnime ve tvaru prefix_ACTION
            # ACTIONS = is_above, is_below, is_falling, is_rising, crossed_up, crossed_down, is_pivot_a, is_pivot_v
            
            #OBECNE DIREKTIVY - REUSOVATELNE
            if directive.endswith("above"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = get_source_or_MA(indname)[-1] > value_or_indicator(value)
            elif directive.endswith("below"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = get_source_or_MA(indname)[-1] < value_or_indicator(value)
            elif directive.endswith("falling"):
                if directive.endswith("not_falling"):
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = not isfalling(get_source_or_MA(indname),value)
                else:
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = isfalling(get_source_or_MA(indname),value)
            elif directive.endswith("rising"):
                if directive.endswith("not_rising"):
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = not isrising(get_source_or_MA(indname),value)
                else:
                    cond[cond_type][directive+"_"+indname+"_"+str(value)] = isrising(get_source_or_MA(indname),value)
            elif directive.endswith("crossed_down"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = buy_if_crossed_down(indname, value_or_indicator(value))
            elif directive.endswith("crossed_up"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = buy_if_crossed_up(indname, value_or_indicator(value))
            elif directive.endswith("pivot_a"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = is_pivot(source=get_source_or_MA(indname), leg_number=value, type="A")
            elif directive.endswith("pivot_v"):
                cond[cond_type][directive+"_"+indname+"_"+str(value)] = is_pivot(source=get_source_or_MA(indname), leg_number=value, type="V")

            #PRIPADNE DALSI SPECIFICKE ZDE
            # elif directive == "buy_if_necospecifckeho":
            #     pass

        return cond


    #tato funkce vytvori dictionary typu podminek (OR/AND) 
    # z indikatoru, ktere obsahuji direktivami daneho typu(buy_if, dont_buy_when)
    # v tuplu (nazevind,direktiva,hodnota)
    # do OR jsou dane i bez prefixu
    # {'AND': [('nazev indikatoru', 'nazev direktivy', 'hodnotadirektivy')], 'OR': []}
    def get_work_dict_with_directive(starts_with: str):
        reslist = dict(AND=[], OR=[])

        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                    if option.startswith(starts_with):
                        reslist["OR"].append((indname, option, value))
                    if option == "AND":
                        #vsechny buy direktivy, ktere jsou pod AND
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["AND"].append((indname, key, val))
                    if option == "OR" :
                        #vsechny buy direktivy, ktere jsou pod OR
                        for key, val in value.items():
                            if key.startswith(starts_with):
                                reslist["OR"].append((indname, key, val))
        return reslist     

    def get_source_or_MA(indicator):
        #pokud ma, pouzije MAcko, pokud ne tak standardni indikator
        try:
            return state.indicators[indicator+"MA"]
        except KeyError:
            return state.indicators[indicator]

    #vrati true pokud dany indikator prekrocil threshold dolu
    def buy_if_crossed_down(indicator, value):
        res = crossed_down(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(e=f"buy_if_crossed_down {indicator} {value} {res}")
        return res

    #vrati true pokud dany indikator prekrocil threshold nahoru
    def buy_if_crossed_up(indicator, value):
        res = crossed_up(threshold=value, list=get_source_or_MA(indicator))
        state.ilog(e=f"buy_if_crossed_up {indicator} {value} {res}")
        return res    

    def eval_buy():
        if conditions_met():
                vyloz()

    def populate_cbar_tick_price_indicator():
        try:
            #pokud v potvrzovacím baru nebyly zmeny, nechavam puvodni hodnoty
            # if tick_delta_volume == 0:
            #     state.indicators.tick_price[-1] = state.indicators.tick_price[-2]
            #     state.indicators.tick_volume[-1] = state.indicators.tick_volume[-2]
            # else:

            #tick_price = round2five(data['close'])
            tick_price = data['close']
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
                last_ind_vals[key] = state.indicators[key][-6:]
        
        for key in state.cbar_indicators:
            if key != 'time':
                last_ind_vals[key] = state.cbar_indicators[key][-6:]

        # for key in state.secondary_indicators:
        #     if key != 'time':
        #         last_ind_vals[key] = state.secondary_indicators[key][-5:]   

        return last_ind_vals

    def populate_dynamic_indicators():
        #pro vsechny indikatory, ktere maji ve svych stratvars TYPE, poustime populaci daneho typu indikaotru
        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                if option == "type":
                    populate_dynamic_indicator_hub(type=value, name=indname)

    def populate_dynamic_indicator_hub(type, name):
        if type == "slope":
            populate_dynamic_slope_indicator(name = name)
        #slope variant with continuous Left Point
        elif type == "slopeLP":
            populate_dynamic_slopeLP_indicator(name = name)
        elif type == "RSI":
            populate_dynamic_RSI_indicator(name = name)
        elif type == "EMA":
            populate_dynamic_ema_indicator(name = name)
        else:
            return

    #EMA INDICATOR
    # type = EMA, source = [close, vwap, hlcc4], length = [14], on_confirmed_only = [true, false]
    def populate_dynamic_ema_indicator(name):
        ind_type = "EMA"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(e=f"Unknown source error {req_source} for {name}")
            return
        ema_length = int(safe_get(options, "length",14))
        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                source = state.bars[req_source][-ema_length:]
                #if len(source) > ema_length:
                ema_value = ema(source, ema_length)
                val = round(ema_value[-1],4)
                state.indicators[name][-1]= val
                #state.indicators[name][-1]= round2five(val)
                state.ilog(e=f"IND {name} EMA {val} {ema_length=}")
                #else:
                #    state.ilog(e=f"IND {name} EMA necháváme 0", message="not enough source data", source=source, ema_length=ema_length)
            except Exception as e:
                state.ilog(e=f"IND ERROR {name} EMA necháváme 0", message=str(e)+format_exc())

    #RSI INDICATOR
    # type = RSI, source = [close, vwap, hlcc4], rsi_length = [14], MA_length = int (optional), on_confirmed_only = [true, false]
    # pokud existuje MA, vytvarime i stejnojnojmenny MAcko
    def populate_dynamic_RSI_indicator(name):
        ind_type = "RSI"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return       
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)
        req_source = safe_get(options, 'source', 'vwap')
        if req_source not in ["close", "vwap","hlcc4"]:
            state.ilog(e=f"Unknown source error {req_source} for {name}")
            return
        rsi_length = int(safe_get(options, "RSI_length",14))
        rsi_MA_length = safe_get(options, "MA_length", None)

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                source = state.bars[req_source]
                #cekame na dostatek dat
                if len(source) > rsi_length:
                    rsi_res = rsi(source, rsi_length)
                    rsi_value = round(rsi_res[-1],4)
                    state.indicators[name][-1]=rsi_value
                    state.ilog(e=f"IND {name} RSI {rsi_value}")

                    if rsi_MA_length is not None:
                        src = state.indicators[name][-rsi_MA_length:]
                        rsi_MA_res = ema(src, rsi_MA_length)
                        rsi_MA_value = round(rsi_MA_res[-1],4)
                        state.indicators[name+"MA"][-1]=rsi_MA_value
                        state.ilog(e=f"IND {name} RSIMA {rsi_MA_value}")

                else:
                    state.ilog(e=f"IND {name} RSI necháváme 0", message="not enough source data", source=source, rsi_length=rsi_length)
            except Exception as e:
                state.ilog(e=f"IND ERROR {name} RSI necháváme 0", message=str(e)+format_exc())

    #SLOPE LP
    def populate_dynamic_slopeLP_indicator(name):
        ind_type = "slopeLP"
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e=f"No options for {name} in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != ind_type:
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)

        #slopeLP INDIKATOR
        #levy bod je nejdrive standardne automaticky vypočtený podle hodnoty lookbacku (např. -8, offset 4)
        #při nákupu se BUY POINT se stává levým bodem (až do doby kdy není lookbackprice nižší, pak pokračuje lookbackprice)
        #při prodeji se SELL POINT se stává novým levým bodem (až do doby kdy není lookbackprice vyšší, pak pokračuje lookbackprice)
        #zatím implementovat prvni část (mimo části ..až do doby) - tu pak dodelat podle vysledku, pripadne ji neimplementovat vubec a misto toho 
        #udelat slope RESET pri dosazeni urciteho pozitivniho nebo negativni slopu

        #zkusime nejdriv: levy bod automat, po nakupu je levy bod cena nakupu

        #VYSTUPY:    state.indicators[name], 
        #            state.indicators[nameMA]
        #            statický indikátor (angle) - stejneho jmena pro vizualizaci uhlu

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                #slow_slope = 99
                slope_lookback = safe_get(options, 'slope_lookback', 100)
                minimum_slope =  safe_get(options, 'minimum_slope', 25)
                maximum_slope = safe_get(options, "maximum_slope",0.9)
                lookback_offset = safe_get(options, 'lookback_offset', 25)
                
                #typ leveho bodu [lastbuy - cena posledniho nakupu, baropen - cena otevreni baru]
                leftpoint = safe_get(options, 'leftpoint', "lastbuy")

                #lookback has to be even
                if lookback_offset % 2 != 0:
                    lookback_offset += 1

                if leftpoint == "lastbuy":
                    if len(state.bars.close) > (slope_lookback + lookback_offset):
                        #test prumer nejvyssi a nejnizsi hodnoty 
                        # if name == "slope":

                        #levy bod bude vzdy vzdaleny o slope_lookback
                        #ten bude prumerem hodnot lookback_offset a to tak ze polovina offsetu z kazde strany
                        array_od = slope_lookback + int(lookback_offset/2)
                        array_do = slope_lookback - int(lookback_offset/2)
                        lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                        #cas nastavujeme vzdy podle nastaveni (zatim)
                        lookbacktime = state.bars.time[-slope_lookback]

                        #pokud mame aktivni pozice, nastavime lookbackprice a time podle posledniho tradu
                        if state.avgp > 0:
                            lb_index = -1 - (state.bars.index[-1] - int(state.vars.lastbuyindex))
                            lookbackprice = state.bars.vwap[lb_index]
                            state.ilog(e=f"IND {name} slope {leftpoint}- LEFT POINT OVERRIDE bereme buy {state.avgp=} {lookbackprice=} {lookbacktime=} {lb_index=}")
                        else:
                            #dame na porovnani jen prumer
                            lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                                #lookbackprice = round((min(lookbackprice_array)+max(lookbackprice_array))/2,3)
                            # else:
                            #     #puvodni lookback a od te doby dozadu offset
                            #     array_od = slope_lookback + lookback_offset
                            #     array_do = slope_lookback
                            #     lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                            #     #obycejný prumer hodnot
                            #     lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                            
                            lookbacktime = state.bars.time[-slope_lookback]
                            state.ilog(e=f"IND {name} slope {leftpoint} - LEFT POINT STANDARD AVGP {state.avgp} {lookbackprice=} {lookbacktime=}")
                    else:
                        #kdyz neni  dostatek hodnot, pouzivame jako levy bod open hodnotu close[0]
                        lookbackprice = state.bars.close[0]
                        lookbacktime = state.bars.time[0]
                        state.ilog(e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback)
                elif leftpoint == "baropen":
                    lookbackprice = state.bars.open[-1]
                    lookbacktime = state.bars.time[-1]
                    state.ilog(e=f"IND {name} slope {leftpoint}- bereme cenu bar OPENu ", lookbackprice=lookbackprice, lookbacktime=lookbacktime)
                else:
                    state.ilog(e=f"IND {name} UNKNOW LEFT POINT TYPE {leftpoint=}")

                #výpočet úhlu - a jeho normalizace
                slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
                slope = round(slope, 4)
                state.indicators[name][-1]=slope

                #angle ze slope
                state.statinds[name] = dict(time=state.bars.updated[-1], price=state.bars.close[-1], lookbacktime=lookbacktime, lookbackprice=lookbackprice, minimum_slope=minimum_slope, maximum_slope=maximum_slope)

                #slope MA vyrovna vykyvy ve slope
                slope_MA_length = safe_get(options, 'MA_length', None)
                slopeMA = None
                last_slopesMA = None
                #pokud je nastavena MA_length tak vytvarime i MAcko dane delky na tento slope
                if slope_MA_length is not None:
                    source = state.indicators[name][-slope_MA_length:]
                    slopeMAseries = ema(source, slope_MA_length) #state.bars.vwap
                    slopeMA = round(slopeMAseries[-1],5)
                    state.indicators[name+"MA"][-1]=slopeMA
                    last_slopesMA = state.indicators[name+"MA"][-10:]

                state.ilog(e=f"{name=} {slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())

    def populate_dynamic_slope_indicator(name):
        options = safe_get(state.vars.indicators, name, None)
        if options is None:
            state.ilog(e="No options for slow slope in stratvars")
            return
        
        if safe_get(options, "type", False) is False or safe_get(options, "type", False) != "slope":
            state.ilog(e="Type error")
            return
        
        #poustet kazdy tick nebo jenom na confirmed baru (on_confirmed_only = true)
        on_confirmed_only = safe_get(options, 'on_confirmed_only', False)

        #SLOW SLOPE INDICATOR
        #úhel stoupání a klesání vyjádřený mezi -1 až 1
        #pravý bod přímky je aktuální cena, levý je průměr X(lookback offset) starších hodnot od slope_lookback.
        #VYSTUPY:    state.indicators[name], 
        #            state.indicators[nameMA]
        #            statický indikátor (angle) - stejneho jmena pro vizualizaci uhlu

        if on_confirmed_only is False or (on_confirmed_only is True and data['confirmed']==1):
            try:
                #slow_slope = 99
                slope_lookback = safe_get(options, 'slope_lookback', 100)
                minimum_slope =  safe_get(options, 'minimum_slope', 25)
                maximum_slope = safe_get(options, "maximum_slope",0.9)
                lookback_offset = safe_get(options, 'lookback_offset', 25)

                #lookback has to be even
                if lookback_offset % 2 != 0:
                    lookback_offset += 1

                #TBD pripdadne /2
                if len(state.bars.close) > (slope_lookback + lookback_offset):
                    #test prumer nejvyssi a nejnizsi hodnoty 
                    # if name == "slope":

                    #levy bod bude vzdy vzdaleny o slope_lookback
                    #ten bude prumerem hodnot lookback_offset a to tak ze polovina offsetu z kazde strany
                    array_od = slope_lookback + int(lookback_offset/2)
                    array_do = slope_lookback - int(lookback_offset/2)
                    lookbackprice_array = state.bars.vwap[-array_od:-array_do]

                        #dame na porovnani jen prumer
                    lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                        #lookbackprice = round((min(lookbackprice_array)+max(lookbackprice_array))/2,3)
                    # else:
                    #     #puvodni lookback a od te doby dozadu offset
                    #     array_od = slope_lookback + lookback_offset
                    #     array_do = slope_lookback
                    #     lookbackprice_array = state.bars.vwap[-array_od:-array_do]
                    #     #obycejný prumer hodnot
                    #     lookbackprice = round(sum(lookbackprice_array)/lookback_offset,3)
                    
                    lookbacktime = state.bars.time[-slope_lookback]
                else:
                    #kdyz neni  dostatek hodnot, pouzivame jako levy bod open hodnotu close[0]
                    lookbackprice = state.bars.close[0]
                    lookbacktime = state.bars.time[0]
                    state.ilog(e=f"IND {name} slope - not enough data bereme left bod open", slope_lookback=slope_lookback)

                #výpočet úhlu - a jeho normalizace
                slope = ((state.bars.close[-1] - lookbackprice)/lookbackprice)*100
                slope = round(slope, 4)
                state.indicators[name][-1]=slope

                #angle je ze slope, ale pojmenovavame ho podle MA
                state.statinds[name] = dict(time=state.bars.time[-1], price=state.bars.close[-1], lookbacktime=lookbacktime, lookbackprice=lookbackprice, minimum_slope=minimum_slope, maximum_slope=maximum_slope)

                #slope MA vyrovna vykyvy ve slope
                slope_MA_length = safe_get(options, 'MA_length', None)
                slopeMA = None
                last_slopesMA = None
                #pokud je nastavena MA_length tak vytvarime i MAcko dane delky na tento slope
                if slope_MA_length is not None:
                    source = state.indicators[name][-slope_MA_length:]
                    slopeMAseries = ema(source, slope_MA_length) #state.bars.vwap
                    slopeMA = round(slopeMAseries[-1],4)
                    state.indicators[name+"MA"][-1]=slopeMA
                    last_slopesMA = state.indicators[name+"MA"][-10:]

                state.ilog(e=f"{name=} {slope=} {slopeMA=}", msg=f"{lookbackprice=}", lookbackoffset=lookback_offset, minimum_slope=minimum_slope, last_slopes=state.indicators[name][-10:], last_slopesMA=last_slopesMA)
                #dale pracujeme s timto MAckovanym slope
                #slope = slopeMA         

            except Exception as e:
                print(f"Exception in {name} slope Indicator section", str(e))
                state.ilog(e=f"EXCEPTION in {name}", msg="Exception in slope Indicator section" + str(e) + format_exc())


    conf_bar = data['confirmed']

    #PROCESs DELTAS - to function
    last_update_delta = round((float(data['updated']) - state.vars.last_update_time),6) if state.vars.last_update_time != 0 else 0
    state.vars.last_update_time = float(data['updated'])

    if len(state.vars.last_50_deltas) >=50:
        state.vars.last_50_deltas.pop(0)
    state.vars.last_50_deltas.append(last_update_delta)
    avg_delta = Average(state.vars.last_50_deltas)

    state.ilog(e=f"---{data['index']}-{conf_bar}--delta:{last_update_delta}---AVGdelta:{avg_delta}")


    #populate indicators, that have type in stratvars.indicators


    #kroky pro CONFIRMED BAR only
    if conf_bar == 1:
        #logika pouze pro potvrzeny bar
        state.ilog(e="BAR potvrzeny")

        #pri potvrzem CBARu nulujeme counter volume pro tick based indicator
        state.vars.last_tick_volume = 0
        state.vars.next_new = 1

        #zatim takto na confirm
        #populate_slow_slope_indicator()

    #kroky pro CONTINOUS TICKS only
    else:
        #CBAR INDICATOR pro tick price a deltu VOLUME
        populate_cbar_tick_price_indicator()
        #TBD nize predelat na typizovane RSI (a to jak na urovni CBAR tak confirmed)
        populate_cbar_rsi_indicator()

    
    populate_dynamic_indicators()

    #SPOLECNA LOGIKA - bar indikatory muzeme populovat kazdy tick (dobre pro RT GUI), ale uklada se stejne az pri confirmu

    #populate_ema_indicator()
    #populate_slope_indicator()
    #populate_rsi_indicator()
    eval_sell()
    consolidation()

    #HLAVNI ITERACNI LOG JESTE PRED AKCI - obsahuje aktualni hodnoty vetsiny parametru
    #lp = state.interface.get_last_price(symbol=state.symbol)
    lp = data['close']
    state.ilog(e="ENTRY", msg=f"LP:{lp} P:{state.positions}/{round(float(state.avgp),3)} profit:{round(float(state.profit),2)} Trades:{len(state.tradeList)} DEF:{str(is_defensive_mode())}", pb=str(state.vars.pendingbuys), last_price=lp, data=data, stratvars=str(state.vars))
    inds = get_last_ind_vals()
    state.ilog(e="Indikatory", **inds)

    eval_buy()
    pendingbuys_optimalization()

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)

    def initialize_dynamic_indicators():
        #pro vsechny indikatory, ktere maji ve svych stratvars TYPE inicializujeme
        for indname, indsettings in state.vars.indicators.items():
            for option,value in indsettings.items():
                #inicializujeme nejenom typizovane
                #if option == "type":
                state.indicators[indname] = []
                #pokud ma MA_length incializujeme i MA variantu
                if safe_get(indsettings, 'MA_length', False):
                    state.indicators[indname+"MA"] = []
                #specifika pro slope
                if value == "slope":
                    #inicializujeme statinds (pro uhel na FE)
                    state.statinds[indname] = dict(minimum_slope=safe_get(indsettings, 'minimum_slope', -1), maximum_slope=safe_get(indsettings, 'maximum_slope', 1))


    #TODO presunout inicializaci work_dict u podminek - sice hodnoty nepujdou zmenit, ale zlepsi se performance
    #pripadne udelat refresh kazdych x-iterací
    state.vars['sell_in_progress'] = False
    state.vars.mode = None
    state.vars.last_tick_price = 0
    state.vars.last_50_deltas = []
    state.vars.last_tick_volume = 0
    state.vars.next_new = 0
    state.vars.lastbuyindex = 0
    state.vars.last_update_time = 0
    state.vars.reverse_position_waiting_amount = 0
    #INIT promenne, ktere byly zbytecne ve stratvars
    state.vars.pendingbuys={}
    state.vars.limitka = None
    state.vars.limitka_price=0
    state.vars.jevylozeno=0
    state.vars.blockbuy = 0

    state.vars["ticks2reset_backup"] = state.vars.ticks2reset
    #state.cbar_indicators['ivwap'] = []
    state.cbar_indicators['tick_price'] = []
    state.cbar_indicators['tick_volume'] = []
    state.cbar_indicators['CRSI'] = []
    #state.secondary_indicators['SRSI'] = []
    #state.indicators['ema'] = []
    #state.indicators['RSI14'] = []

    initialize_dynamic_indicators()


    #TODO - predelat tuto cas, aby dynamicky inicializovala indikatory na zaklade stratvars a type
    # vsechno nize vytvorit volana funkce
    # to jestli inicializovat i MA variantu pozna podle pritomnosti MA_length 
    # # 
    # state.indicators['slope'] = []
    # state.indicators['slopeNEW'] = []
    # state.indicators['slopeNEWMA'] = []
    # state.indicators['slope10'] = []
    # state.indicators['slope10puv'] = []
    # state.indicators['slope30'] = []
    # state.indicators['slopeMA'] = []
    # state.indicators['slow_slope'] = []
    # state.indicators['slow_slopeMA'] = []
    # #static indicators - those not series based
    # state.statinds['slope'] = dict(minimum_slope=state.vars['indicators']['slope']["minimum_slope"], maximum_slope=safe_get(state.vars['indicators']['slope'], "maximum_slope",0.20))
    # #state.statinds['angle_slow'] = dict(minimum_slope=safe_get(state.vars.indicators.slow_slope, "minimum_slope",-2), maximum_slope=safe_get(state.vars.indicators.slow_slope, "maximum_slope",2))
    # state.statinds['slow_slope'] = dict(minimum_slope=state.vars['indicators']['slow_slope']["minimum_slope"], maximum_slope=state.vars['indicators']['slow_slope']["maximum_slope"])
 


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




 
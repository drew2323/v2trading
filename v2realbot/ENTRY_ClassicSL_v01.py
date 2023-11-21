import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.utils.utils import zoneNY, print
from v2realbot.utils.historicals import get_historical_bars
from datetime import datetime, timedelta
from rich import print as printanyway
from threading import Event
import os
from traceback import format_exc
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from v2realbot.strategyblocks.newtrade.prescribedtrades import execute_prescribed_trades
from v2realbot.strategyblocks.newtrade.signals import signal_search
from v2realbot.strategyblocks.activetrade.activetrade_hub import manage_active_trade
from v2realbot.strategyblocks.inits.init_indicators import initialize_dynamic_indicators
from v2realbot.strategyblocks.inits.init_directives import intialize_directive_conditions
from alpaca.trading.requests import GetCalendarRequest
from alpaca.trading.client import TradingClient
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR, OFFLINE_MODE
from alpaca.trading.models import Calendar

print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
""""
Využívá: StrategyClassicSL

Klasická obousměrná multibuysignal strategie se stoplos.
Používá pouze market order, hlídá profit a stoploss.

Ve dvou fázích: 1) search and create prescriptions 2) evaluate prescriptions

list(prescribedTrade)

prescribedTrade:
- validfrom
- status .READY, ACTIVE, finished)
- direction (long/short)
- entry price: 
- stoploss: (fixed, trailing)

Hlavní loop:
- indikátory

- if empty positions (avgp=0):
    - no prescribed trades

    - any prescribed trade?
        - eval input
    
    - eval eligible entries (do buy/sell)

- if positions (avgp <>0)
    - eval exit (standard, forced by eod)
    - if not exit - eval optimalizations

"""
def next(data, state: StrategyState):
    ##print(10*"*","NEXT START",10*"*")
    # important vars state.avgp, state.positions, state.vars, data
    
    #indicators moved to call_next in upper class

    #pokud mame prazdne pozice a neceka se na nic
    if state.positions == 0 and state.vars.pending is None:
        #vykoname trady ve fronte
        execute_prescribed_trades(state, data)
        #pokud se neaktivoval nejaky trade, poustime signal search - ale jen jednou za bar?
        #if conf_bar == 1:
        if state.vars.pending is None:
            signal_search(state, data)
            #pro jistotu ihned zpracujeme
            execute_prescribed_trades(state, data)

    #mame aktivni trade a neceka se n anic
    elif state.vars.activeTrade and state.vars.pending is None:
            manage_active_trade(state, data)

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)

    #init klice v extData pro ulozeni historie SL
    state.extData["sl_history"] = []

    #nove atributy na rizeni tradu
    #identifikuje provedenou změnu na Tradu (neděláme změny dokud nepřijde potvrzeni z notifikace)
    state.vars.pending = None
    #obsahuje aktivni Trade a jeho nastaveni
    state.vars.activeTrade = None #pending/Trade
    #obsahuje pripravene Trady ve frontě
    state.vars.prescribedTrades = []
    #flag pro reversal
    state.vars.requested_followup = None

    #TODO presunout inicializaci work_dict u podminek - sice hodnoty nepujdou zmenit, ale zlepsi se performance
    #pripadne udelat refresh kazdych x-iterací
    state.vars['sell_in_progress'] = False
    state.vars.mode = None
    state.vars.last_tick_price = 0
    state.vars.last_50_deltas = []
    state.vars.last_tick_volume = 0
    state.vars.next_new = 0
    state.vars.last_buy_index = None
    state.vars.last_exit_index = None
    state.vars.last_in_index = None
    state.vars.last_update_time = 0
    state.vars.reverse_position_waiting_amount = 0
    #INIT promenne, ktere byly zbytecne ve stratvars
    state.vars.pendingbuys={}
    state.vars.limitka = None
    state.vars.limitka_price=0
    state.vars.jevylozeno=0
    state.vars.blockbuy = 0
    #models
    state.vars.loaded_models = {}
    #state.cbar_indicators['ivwap'] = []
    state.cbar_indicators['tick_price'] = []
    state.cbar_indicators['tick_volume'] = []
    state.cbar_indicators['CRSI'] = []

    initialize_dynamic_indicators(state)
    intialize_directive_conditions(state)

    #intitialize indicator mapping (for use in operation) -  mozna presunout do samostatne funkce prip dat do base kdyz se osvedci
    local_dict_inds = {key: state.indicators[key] for key in state.indicators.keys() if key != "time"}
    local_dict_bars = {key: state.bars[key] for key in state.bars.keys() if key != "time"}

    state.ind_mapping = {**local_dict_inds, **local_dict_bars}
    printanyway("IND MAPPING DONE:", state.ind_mapping)

    #30 DAYS historicall data fill - pridat do base pokud se osvedci
    # -1 je vždy včerejšek v tomto případě
    #diky tomu mají indikátory data 30 dní zpět (tzn. můžu počítat last day close, atp)
    #do budoucna systematizovat přístup k historickým dat
    # např. historicals.days state.historical.bars["days"]atp.
    #nyní jednoucelne state.dailyBars

    #LIVE a PAPER - bereme time now
    #BT - bereme time bt_start
    if state.mode in (Mode.LIVE, Mode.PAPER):
        time_to = datetime.now(tz=zoneNY)
    else:
        time_to = state.bt.bp_from


    #TBD pridat i hour data - pro pocitani RSI na hodine
    #get 30 days (history_datetime_from musí být alespoň -2 aby to bralo i vcerejsek)
    #history_datetime_from = time_to - timedelta(days=40)
    #get previous market day
    #time_to = time_to - timedelta(days=1)

    #time_to = time_to.date()

    #vypocet posledniho market dne - do samostatne funkce get_previous_market_day(today)
    #time_to = time_to.date()

    today = time_to.date()
    several_days_ago = today - timedelta(days=40)
    #printanyway(f"{today=}",f"{several_days_ago=}")
    clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
    #get all market days from here to 40days ago
    calendar_request = GetCalendarRequest(start=several_days_ago,end=today)
    cal_dates = clientTrading.get_calendar(calendar_request)

    #find the first market day - 40days ago
    #history_datetime_from = zoneNY.localize(cal_dates[0].open)
    history_datetime_from = cal_dates[0].open

    # Find the previous market day
    history_datetime_to = None
    for session in reversed(cal_dates):
        if session.date < today:
            #history_datetime_to = zoneNY.localize(session.close)
            history_datetime_to = session.close
            break
    #printanyway("Previous Market Day Close:", history_datetime_to)
    #printanyway("Market day 40days ago Open:", history_datetime_from)

    #printanyway(history_datetime_from, history_datetime_to)
    #az do predchziho market dne dne
    state.dailyBars = get_historical_bars(state.symbol, history_datetime_from, history_datetime_to, TimeFrame.Day)
    #printanyway("daily bars FILLED", state.dailyBars)
    #zatim ukladame do extData - pro instant indicatory a gui
    state.extData["dailyBars"] = state.dailyBars

def main():
    name = os.path.basename(__file__)
    se = Event()
    pe = Event()
    s = StrategyOrderLimitVykladaciNormalizedMYSELL(name = name, symbol = "BAC", account=Account.ACCOUNT1, next=next, init=init, stratvars=None, open_rush=10, close_rush=0, pe=pe, se=se, ilog_save=True)
    s.set_mode(mode = Mode.BT,
               debug = False,
               start = datetime(2023, 4, 14, 10, 42, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 4, 14, 14, 35, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.BAR,resolution=2,minsize=100,update_ltp=True,align=StartBarAlign.ROUND,mintick=0, exthours=False)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()
    print("zastavujeme")

if __name__ == "__main__":
    main()




 
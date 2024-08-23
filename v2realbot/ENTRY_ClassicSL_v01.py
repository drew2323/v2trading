import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import StrategyState
from v2realbot.strategy.StrategyOrderLimitVykladaciNormalizedMYSELL import StrategyOrderLimitVykladaciNormalizedMYSELL
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode, Account
from v2realbot.utils.utils import zoneNY, print, fetch_calendar_data, send_to_telegram
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
from v2realbot.strategyblocks.inits.init_attached_data import attach_previous_data
from alpaca.trading.client import TradingClient
from v2realbot.config import ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, DATA_DIR
from alpaca.trading.models import Calendar
from v2realbot.indicators.oscillators import rsi
from v2realbot.indicators.moving_averages import sma
import numpy as np

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
    print(10*"*", state.account_variables)

    execute_prescribed_trades(state, data)
    signal_search(state, data)
    execute_prescribed_trades(state, data) #pro jistotu ihned zpracujeme
    manage_active_trade(state, data)

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)

    #init klice v extData pro ulozeni historie SL
    state.extData["sl_history"] = []

    #nove atributy na rizeni tradu
    #identifikuje provedenou změnu na Tradu (neděláme změny dokud nepřijde potvrzeni z notifikace)
    #state.vars.pending = None #nahrazeno pebnding pod accountem state.account_variables[account.name].pending
    #obsahuje aktivni Trade a jeho nastaveni
    #state.vars.activeTrade = None #pending/Trade moved to account_variables
    #obsahuje pripravene Trady ve frontě
    state.vars.prescribedTrades = []
    #flag pro reversal
    #state.vars.requested_followup = None #nahrazeno pod accountem

    #TODO presunout inicializaci work_dict u podminek - sice hodnoty nepujdou zmenit, ale zlepsi se performance
    #pripadne udelat refresh kazdych x-iterací
    state.vars['sell_in_progress'] = False
    state.vars.mode = None
    state.vars.last_50_deltas = []
    state.vars.next_new = 0
    state.vars.last_entry_index = None #mponechano obecne pro vsechny accounty
    state.vars.last_exit_index = None #obecna varianta ponechana
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

    #state attributes for martingale sizing mngmt
    state.vars["transferables"] = {}
    state.vars["transferables"]["martingale"] = dict(cont_loss_series_cnt=0)
    
    #INITIALIZE CBAR INDICATORS - do vlastni funkce
    #state.cbar_indicators['ivwap'] = []
    state.vars.last_tick_price = 0
    state.vars.last_tick_volume = 0
    state.vars.last_tick_trades = 0
    state.cbar_indicators['tick_price'] = []
    state.cbar_indicators['tick_volume'] = []
    state.cbar_indicators['tick_trades'] = []
    state.cbar_indicators['CRSI'] = []

    initialize_dynamic_indicators(state)
    intialize_directive_conditions(state)

    #attach part of yesterdays data, bars, indicators, cbar_indicators
    attach_previous_data(state)

    #intitialize indicator mapping (for use in operation) -  mozna presunout do samostatne funkce prip dat do base kdyz se osvedci
    local_dict_cbar_inds = {key: state.cbar_indicators[key] for key in state.cbar_indicators.keys() if key != "time"}
    local_dict_inds = {key: state.indicators[key] for key in state.indicators.keys() if key != "time"}
    local_dict_bars = {key: state.bars[key] for key in state.bars.keys() if key != "time"}

    state.ind_mapping = {**local_dict_inds, **local_dict_bars, **local_dict_cbar_inds}
    print("IND MAPPING DONE:", state.ind_mapping)

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


    #TBD NASLEDUJICI SEKCE BUDE PREDELANA, ABY UMOZNOVALA LIBOVOLNE ROZLISENI
    #INDIKATORY SE BUDOU TAKE BRAT Z KONFIGURACE
    #get 30 days (history_datetime_from musí být alespoň -2 aby to bralo i vcerejsek)
    #history_datetime_from = time_to - timedelta(days=40)
    #get previous market day
    #time_to = time_to - timedelta(days=1)

    #time_to = time_to.date()

    #vypocet posledniho market dne - do samostatne funkce get_previous_market_day(today)
    #time_to = time_to.date()

    today = time_to.date()
    several_days_ago = today - timedelta(days=60)
    #printanyway(f"{today=}",f"{several_days_ago=}")
    #clientTrading = TradingClient(ACCOUNT1_PAPER_API_KEY, ACCOUNT1_PAPER_SECRET_KEY, raw_data=False)
    #get all market days from here to 40days ago

    #calendar_request = GetCalendarRequest(start=several_days_ago,end=today)

    cal_dates = fetch_calendar_data(several_days_ago, today)
    #cal_dates = clientTrading.get_calendar(calendar_request)

    #find the first market day - 40days ago
    #history_datetime_from = zoneNY.localize(cal_dates[0].open)
    history_datetime_from = cal_dates[0].open

    #ulozime si dnesni market close
    #pro automaticke ukonceni
    #TODO pripadne enablovat na parametr
    state.today_market_close = zoneNY.localize(cal_dates[-1].close)

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

    #NOTE zatim pridano takto do baru dalsi indikatory
    #BUDE PREDELANO - v rámci custom rozliseni a static indikátoru
    if state.dailyBars is None:
        print("Nepodařilo se načíst denní bary")
        err_msg = f"Nepodařilo se načíst denní bary (get_historical_bars) pro {state.symbol} od {history_datetime_from} do {history_datetime_to} ve strat.init. Probably wrong symbol?"
        send_to_telegram(err_msg)
        raise Exception(err_msg)
    
    #RSI vraci pouze pro vsechny + prepend with zeros nepocita prvnich N (dle rsi length)
    rsi_calculated = rsi(state.dailyBars["vwap"], 14).tolist()
    num_zeros_to_prepend = len(state.dailyBars["vwap"]) - len(rsi_calculated)
    state.dailyBars["rsi"] = [0]*num_zeros_to_prepend + rsi_calculated
    
    #VOLUME
    volume_sma = sma(state.dailyBars["volume"], 10) #vraci celkovy pocet - 10
    items_to_prepend = len(state.dailyBars["volume"]) - len(volume_sma)

    volume_sma = np.hstack((np.full(items_to_prepend, np.nan), volume_sma))

    #normalized divergence currvol-smavolume/currvol+smavolume
    volume_data = np.array(state.dailyBars["volume"])
    normalized_divergence = (volume_data - volume_sma) / (volume_data + volume_sma)
    # Replace NaN values with 0 or some other placeholder if needed
    normalized_divergence = np.nan_to_num(normalized_divergence)
    volume_sma = np.nan_to_num(volume_sma)
    state.dailyBars["volume_sma_divergence"] = normalized_divergence.tolist()
    state.dailyBars["volume_sma"] = volume_sma.tolist()

    #vwap_cum and divergence
    volume_np = np.array(state.dailyBars["volume"])
    close_np = np.array(state.dailyBars["close"])
    high_np = np.array(state.dailyBars["high"])
    low_np = np.array(state.dailyBars["low"])
    vwap_cum_np = np.cumsum(((high_np + low_np + close_np) / 3) * volume_np) / np.cumsum(volume_np)
    state.dailyBars["vwap_cum"] = vwap_cum_np.tolist()
    normalized_divergence = (close_np - vwap_cum_np) / (close_np + vwap_cum_np)
    #divergence close ceny a cumulativniho vwapu
    state.dailyBars["div_vwap_cum"] = normalized_divergence.tolist()

    #creates log returns for open, close, high and lows
    open_np = np.array(state.dailyBars["open"])
    state.dailyBars["open_log_return"] = np.log(open_np[1:] / open_np[:-1]).tolist()
    state.dailyBars["close_log_return"] = np.log(close_np[1:] / close_np[:-1]).tolist()
    state.dailyBars["high_log_return"] = np.log(high_np[1:] / high_np[:-1]).tolist()
    state.dailyBars["low_log_return"] = np.log(low_np[1:] / low_np[:-1]).tolist()


    #Features to emphasize the shape characteristics of each candlestick. For use in ML https://chat.openai.com/c/c1a22550-643b-4037-bace-3e810dbce087
    # Calculate the ratios of 
    total_range = high_np - low_np
    upper_shadow = (high_np - np.maximum(open_np, close_np)) / total_range
    lower_shadow = (np.minimum(open_np, close_np) - low_np) / total_range
    body_size = np.abs(close_np - open_np) / total_range
    body_position = np.where(close_np >= open_np,
                            (close_np - low_np) / total_range,
                            (open_np - low_np) / total_range)

    #other possibilities
    # Open to Close Change: (close[-1] - open[-1]) / open[-1]
    # High to Low Range: (high[-1] - low[-1]) / low[-1]

    # Store the ratios in the bars dictionary
    state.dailyBars['upper_shadow_ratio'] = upper_shadow.tolist()
    state.dailyBars['lower_shadow_ratio'] = lower_shadow.tolist()
    state.dailyBars['body_size_ratio'] = body_size.tolist()
    state.dailyBars['body_position_ratio'] = body_position.tolist()  

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




 
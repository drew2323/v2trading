from strategy.base import Strategy, StrategyState
from strategy.strategyOrderLimitWatched import StrategyOrderLimitWatched
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode
from indicators import ema
from rich import print
from utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY
from datetime import datetime
from icecream import install, ic
install()
ic.configureOutput(includeContext=True)
#ic.disable()
""""
Simple strategie pro test backtesting
"""

def next(data, state: StrategyState):
    print(10*"*","NEXT START",10*"*")
    #ic(state.avgp, state.positions)
    #ic(state.vars.lastbuyindex)
    #ic(data)
    #ic(state.positions)
    #ic(state.vars.watched)
    #ic(state.vars.wait)

    try:
        state.indicators.ema = ema(state.bars.hlcc4, state.vars.MA) #state.bars.vwap
        #trochu prasarna, EMAcko trunc na 3 mista - kdyz se osvedci, tak udelat efektivne
        state.indicators.ema = [trunc(i,3) for i in state.indicators.ema]
        #ic(state.vars.MA, state.vars.Trend, state.indicators.ema[-5:])
    except Exception as e:
        print("No data for MA yet", str(e))

    print("is falling",isfalling(state.indicators.ema,state.vars.Trend))
    print("is rising",isrising(state.indicators.ema,state.vars.Trend))

    #ZDE JSEM SKONCIL
    #nejprve zacit s BARy

    #TODO vyzkoušet limit buy - vetsina z nakupu by se dala koupit o cent dva mene
    #proto dodělat LTP pro BT, neco jako get_last_price(self.state.time)


    ##TODO vyzkouset hlidat si sell objednavku sam na zaklade tradu
    # v pripade ze to jde nahoru(is rising - nebo jiny indikator) tak neprodavat
    #vyuzit CBARy k tomuto .....
    #triggerovat buy treba po polovine CBARu, kdyz se cena bude rovnat nebo bude nizsi nez low
    #a hned na to  (po potvrzeni) hlidat sell +0.01 nebo kdyz roste nechat rust.vyzkouset na LIVE

    datetime.fromtimestamp(state.last_trade_time)
    casbaru = datetime.fromtimestamp(state.last_trade_time)-data['time']
    kupuj = casbaru.seconds > int(int(data['resolution']) * 0.4)
    #ic(kupuj)
    #ic(casbaru.seconds)

    #kupujeme kdyz v druhe polovine baru je aktualni cena=low (nejnizsi)
    #isrising(state.indicators.ema,state.vars.Trend)
    #kdyz se v jednom baru pohneme o 2
    if kupuj and data['confirmed'] != 1 and data['close'] == data['low'] and float(data['close']) + 0.01 < data['open'] and state.vars.wait is False and state.vars.watched is None:
        print("BUY MARKET")
        #ic(data['updated'])
        #ic(state.time)
        ##updatneme realnou cenou po fillu
        state.buy()
        state.vars.wait = True

    if state.vars.watched and state.vars.wait is False:
        currprice = state.interface.get_last_price(symbol = state.symbol)
        #ic(currprice)
        if float(currprice) > (float(state.vars.watched) + float(state.vars.profit)):
            #ic(state.time)
            #ic("prodavame", currprice)
            print("PRODAVAME")
            ##vymyslet jak odchytavat obecne chyby a vracet cislo objednavky
            state.interface.sell(size=1)
            state.vars.wait = True

    
    print(10*"*","NEXT STOP",10*"*")

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)
    state.vars['novaprom'] = 4
    state.indicators['ema'] = []

def main():
    stratvars = AttributeDict(maxpozic = 1, chunk = 1, MA = 2, Trend = 2, profit = 0.005, lastbuyindex=-6, pendingbuys={},watched = None, wait = False)

    s = StrategyOrderLimitWatched(name = "BackTEST", symbol = "BAC", next=next, init=init, stratvars=stratvars, debug=False)
    s.set_mode(mode = Mode.PAPER,
               start = datetime(2023, 3, 24, 11, 30, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 3, 24, 11, 45, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.CBAR,timeframe=5,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()

if __name__ == "__main__":
    main()


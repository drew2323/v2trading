from strategy.base import Strategy, StrategyState
from strategy.strategyOrderLimit import StrategyOrderLimit
from enums import RecordType, StartBarAlign, Mode
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE, PAPER
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
    ic(state.avgp, state.positions)
    ic(state.vars.limitka)
    ic(state.vars.lastbuyindex)
    ic(data)
    #print("last trade price")
    #print(state.interface.get_last_price("BAC"))
    #print(state.vars.novaprom)
    #print("trades history", state.trades)
    #print("bar history", state.bars)
    #print("ltp", ltp.price["BAC"], ltp.time["BAC"])

    #TODO indikátory ukládat do vlastní historie - tu pak automaticky zobrazuje backtester graf

    #TODO ema = state.indicators.ema a pouzivat nize ema, zjistit jestli bude fungovat

    try:
        state.indicators.ema = ema(state.bars.hlcc4, state.vars.MA) #state.bars.vwap
        #trochu prasarna, EMAcko trunc na 3 mista - kdyz se osvedci, tak udelat efektivne
        state.indicators.ema = [trunc(i,3) for i in state.indicators.ema]
        ic(state.vars.MA, state.vars.Trend, state.indicators.ema[-5:])
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

    if isfalling(state.indicators.ema,state.vars.Trend) and data['index'] > state.vars.lastbuyindex+state.vars.Trend: #and state.blockbuy == 0
        print("BUY MARKET")
        ic(data['updated'])
        ic(state.time)
        state.buy_l()

    
    print(10*"*","NEXT STOP",10*"*")

def init(state: StrategyState):
    #place to declare new vars
    print("INIT v main",state.name)
    state.vars['novaprom'] = 4
    state.indicators['ema'] = []

def main():
    stratvars = AttributeDict(maxpozic = 2400, chunk = 400, MA = 6, Trend = 7, profit = 0.03, lastbuyindex=-6, pendingbuys={},limitka = None)

    s = StrategyOrderLimit(name = "BackTEST", symbol = "KO", next=next, init=init, stratvars=stratvars, debug=False)
    s.set_mode(mode = Mode.BT,
               start = datetime(2023, 2, 23, 9, 30, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 2, 23, 16, 00, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="KO",rectype=RecordType.BAR,timeframe=30,filters=None,update_ltp=True,align=StartBarAlign.RANDOM,mintick=0)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()

if __name__ == "__main__":
    main()


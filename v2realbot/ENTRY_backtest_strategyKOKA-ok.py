# import os,sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2realbot.strategy.base import Strategy, StrategyState
from v2realbot.strategy.StrategyOrderLimitKOKA import StrategyOrderLimitKOKA
from v2realbot.enums.enums import RecordType, StartBarAlign, Mode
from v2realbot.indicators.indicators import ema
from rich import print
from v2realbot.utils.utils import ltp, isrising, isfalling,trunc,AttributeDict, zoneNY
from datetime import datetime
from icecream import install, ic
import os
install()
ic.configureOutput(includeContext=True)
#ic.disable()
""""
Simple strategie LIMIT buy a lIMIT SELL working ok

DOkupovaci strategie, nakupuje dalsi pozice až po dalším signálu.

POZOR nekontroluje se maximální pozice - tzn. nejvic se vycerpalo 290, ale prezila kazdy den.
Dobrá defenzivní pri nastaveni
30s maxpozic = 290,chunk = 10,MA = 6,Trend = 6,profit = 0.02,
"""
stratvars = AttributeDict(maxpozic = 250,
                          chunk = 10,
                          MA = 6,
                          Trend = 6,
                          profit = 0.02,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None)

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
    name = os.path.basename(__file__)
    s = StrategyOrderLimitKOKA(name = name, symbol = "BAC", next=next, init=init, stratvars=stratvars, open_rush=30, close_rush=0)
    s.set_mode(mode = Mode.PAPER,
               debug = False,
               start = datetime(2023, 3, 6, 9, 30, 0, 0, tzinfo=zoneNY),
               end =   datetime(2023, 3, 9, 16, 0, 0, 0, tzinfo=zoneNY),
               cash=100000)

    #na sekundovem baru nezaokrouhlovat MAcko
    s.add_data(symbol="BAC",rectype=RecordType.BAR,timeframe=30,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()
    print("zastavujeme")

if __name__ == "__main__":
    main()


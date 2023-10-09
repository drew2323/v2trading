from strategy.base import Strategy
from strategy.base import StrategyState
from enums import RecordType, StartBarAlign, Mode
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE, PAPER
from indicators import ema
from rich import print
from utils import ltp, isrising, isfalling,trunc,AttributeDict
from datetime import datetime

""""
Simple strategie pro měření roundtripu na konkrétním prostředí

    - koupí 1 akcii a vypíše časy
        - tradu který triggeroval
        - čas triggeru buy
        - příchod zpětné notifikace NEW
        - příchod zpětné notifikace FILL
        - vypíše trade, když přijde do agregátoru (vyžaduje do agregátoru na řádek 79: if int(data['s']) == 1: print(data))
        - vyžaduje ve strategy base v orderupdate 
                    - print("NOTIFICATION ARRIVED AT:", datetime.now().timestamp(), datetime.now())
                    - print(data)

        výsledek latencyroudntrip.log

        """

def next(data, state: StrategyState):
    print("avgp:", state.avgp)
    print("positions", state.positions)
    print("přišly tyto data", data)
    print("bar updated time:", data['updated'], datetime.fromtimestamp(data['updated']))
    print("state  time(now):", state.time, datetime.fromtimestamp(state.time))
    #print("trades history", state.trades)
    #print("bar history", state.bars)
    print("ltp", ltp.price["BAC"], ltp.time["BAC"])

    try:
        ema_output = ema(state.bars.hlcc4, state.vars.MA) #state.bars.vwap
        ema_output = [trunc(i,3) for i in ema_output]
        print("emacko na wvap",state.vars.MA,":", ema_output[-5:])
    except:
        print("No data for MA yet")
   
    print("MA is falling",state.vars.Trend,"value:",isfalling(ema_output,state.vars.Trend))
    print("MA is rising",state.vars.Trend,"value:",isrising(ema_output,state.vars.Trend))

    if isfalling(ema_output,state.vars.Trend) and state.vars.blockbuy == 0:
        print("kupujeme MARKET")
        print("v baru mame cas posledniho tradu", data['updated'])
        print("na LIVE je skutecny cas - tento ", state.time)
        print("v nem odesilame")
        state.interface.buy(time=state.time)
        state.vars.blockbuy = 1

def init(state: StrategyState):
    print("INIT strategie", state.name, "symbol", state.symbol)

def main():  
    stratvars = AttributeDict(maxpozic = 200, chunk = 10, MA = 3, Trend = 3, profit = 0.01, blockbuy=0, lastbuyindex=0, pendingbuys={})
    s = Strategy(name = "BackTEST", symbol = "BAC", next=next, init=init, stratvars=stratvars)

    #s.set_mode(mode = Mode.BT, start= datetime(2023, 3, 16, 15, 54, 30, 0), end=datetime(2023, 3, 16, 15, 54, 40, 999999))

    s.add_data(symbol="BAC",rectype=RecordType.BAR,timeframe=5,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)
    #s.add_data(symbol="C",rectype=RecordType.BAR,timeframe=1,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)

    s.start()

if __name__ == "__main__":
    main()

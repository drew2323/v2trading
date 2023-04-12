from strategy import MyStrategy, StrategyState
from enums import RecordType, StartBarAlign
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE, PAPER
from indicators import ema
from rich import print

def next(data, state: StrategyState):
    print("next")
    print(state.variables.MA)
    print(state.variables.maxpozic)
    print(data)
    print(state.oe.pos())

def init(state: StrategyState):
    print("init - zatim bez data")
    print(state.oe.symbol)
    print(state.oe.pos())
    print()

def main():  
    stratvars = dict(maxpozic = 10, chunk = 1, MA = 3, Trend = 4,profit = 0.01)
    s = MyStrategy("TSLA",paper=PAPER, next=next, init=init, stratvars=stratvars)
    s.add_data(symbol="TSLA",rectype=RecordType.TRADE,timeframe=5,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=0)
    s.start()

if __name__ == "__main__":
    main()

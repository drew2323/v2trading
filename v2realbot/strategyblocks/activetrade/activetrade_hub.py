from v2realbot.strategyblocks.activetrade.sl.trailsl import trail_SL_management
from v2realbot.strategyblocks.activetrade.close.evaluate_close import eval_close_position

def manage_active_trade(state, data):
    trade = state.vars.activeTrade
    if trade is None:
        return -1
    trail_SL_management(state, data)
    eval_close_position(state, data)
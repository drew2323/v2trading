from v2realbot.strategyblocks.activetrade.sl.trailsl import trail_SL_management
from v2realbot.strategyblocks.activetrade.close.evaluate_close import eval_close_position
from v2realbot.utils.utils import gaka
def manage_active_trade(state, data):  
    accountsWithActiveTrade = gaka(state.account_variables, "activeTrade", None, lambda x: x is not None)
    # {"account1": activeTrade,
    #  "account2": activeTrade}

    if len(accountsWithActiveTrade.values()) == 0:
        return
    
    trail_SL_management(state, accountsWithActiveTrade, data)
    eval_close_position(state, accountsWithActiveTrade, data)
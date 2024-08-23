import numpy as np
from v2realbot.common.model import Trade, TradeDirection, TradeStatus
from typing import Tuple
from copy import deepcopy
from v2realbot.strategyblocks.activetrade.helpers import get_signal_section_directive
from v2realbot.utils.utils import safe_get
# FIBONACCI PRO PROFIT A SL

##most used fibonacci retracement levels
# 23.6% retracement level = (stop loss price - current price) * 0.236 + current price
# 38.2% retracement level = (stop loss price - current price) * 0.382 + current price
# 50.0% retracement level = (stop loss price - current price) * 0.500 + current price
# 61.8% retracement level = (stop loss price - current price) * 0.618 + current price
# 78.6% retracement level = (stop loss price - current price) * 0.786 + current price

#cil: moznost pouzit fibanocci scale pro castecny stoploss exit (percentage at each  downlevel) 
#a zároveň exit, případně add at each up level

#up retracements (profit retracement)
#    exit part of position at certain - 
#      [0.236, 0.382, 0.618, 1.0]  - 25% off at each level? a nebo 5% add? - TBD vymyslet jak pojmout v direktive?
#down retracement (stoploss retracement)
#    exit part of position at certain levels - TBD jak zapsat v dsirektive? 
#    [0.236, 0.382, 0.618, 1.0] - 25% off at each level



# #tridu, kterou muze vyuzivat SL a Profit optimizer
class SLOptimizer:
    """"
    Class to handle SL positition optimization for active trade. It is assumed that two instances exists 
    one for LONG trade and one for SHORT. During evaluate call, settings is initialized from trade setting
    and used for every call on that trade. When evaluate is called on different trade, it is again initialized
    according to new trade settings.

    -samostatna instance pro short a long
    -zatim pri opakovem prekroceni targetu nic nedelame (target aplikovany jen jednouo)

    exit_levels = aktuální levely, prekroceny je povazovan za vyuzitý a maze se
    exit_sizes = aktualní size multipliers, prekroceny je povazovan za vyuzitý a maze se
    init_exit_levels, init_exit_sizes - puvodni plne
    """
    def __init__(self, direction: TradeDirection) -> None:
        ##init - make exit size same length:
        self.direction = direction
        self.last_trade = 0

    # def reset_levels(self):
    #      self.exit_levels = self.init_exit_levels
    #      self.exit_sizes = self.init_exit_sizes

    def get_trade_details(self, state, activeTrade):
        trade: Trade = activeTrade
        #jde o novy trade - resetujeme levely
        if trade.id != self.last_trade:
            #inicializujeme a vymazeme pripadne puvodni
            if self.initialize_levels(state) is False:
                return None, None
            self.last_trade = trade.id
        #return cost_price, sl_price
        return  state.account_variables[trade.account.name].avgp, trade.stoploss_value

    def initialize_levels(self, state):
        directive_name = 'SL_opt_exit_levels_'+str(self.direction.value)
        SL_opt_exit_levels = get_signal_section_directive(state=state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

        directive_name = 'SL_opt_exit_sizes_'+str(self.direction.value)
        SL_opt_exit_sizes = get_signal_section_directive(state=state, directive_name=directive_name, default_value=safe_get(state.vars, directive_name, None))

        if SL_opt_exit_levels is None or SL_opt_exit_sizes is None:
            #print("no directives found: SL_opt_exit_levels/SL_opt_exit_sizes")
            return False

        if len(SL_opt_exit_sizes) == 1:
            SL_opt_exit_sizes = SL_opt_exit_sizes * len(SL_opt_exit_levels)

        if len(SL_opt_exit_sizes) != len(SL_opt_exit_levels):
            raise Exception("exit_sizes doesnt fit exit_levels")
        self.init_exit_levels = deepcopy(SL_opt_exit_levels)
        self.init_exit_sizes = deepcopy(SL_opt_exit_sizes)
        self.exit_levels = SL_opt_exit_levels
        self.exit_sizes = SL_opt_exit_sizes
        print(f"new levels initialized {self.exit_levels=} {self.exit_sizes=}")
        return True

    def get_initial_abs_levels(self, state, activeTrade):
         """
         Returns price levels corresponding to initial setting of exit_levels
         """
         cost_price, sl_price = self.get_trade_details(state, activeTrade)
         if cost_price is None or sl_price is None:
             return []
         curr_sl_distance = np.abs(cost_price - sl_price)
         if self.direction == TradeDirection.SHORT :
            return [cost_price + exit_level * curr_sl_distance for exit_level in self.init_exit_levels]
         else:
            return [cost_price - exit_level * curr_sl_distance for exit_level in self.init_exit_levels]

    def get_remaining_abs_levels(self, state, activeTrade):
         """
         Returns price levels corresponding to remaing exit_levels for current trade
         """
         cost_price, sl_price = self.get_trade_details(state, activeTrade)
         if cost_price is None or sl_price is None:
             return []
         curr_sl_distance = np.abs(cost_price - sl_price)
         if self.direction == TradeDirection.SHORT :
            return [cost_price + exit_level * curr_sl_distance for exit_level in self.exit_levels]
         else:
            return [cost_price - exit_level * curr_sl_distance for exit_level in self.exit_levels]

    def eval_position(self, state, data, activeTrade) -> Tuple[float, float]:
        """Evaluates optimalization for current position and returns if the given level was
           met and how to adjust exit position.
        """    
        cost_price, sl_price = self.get_trade_details(state)
        if cost_price is None or sl_price is None:
             #print("no settings found")
             return (None, None)
        
        current_price = data["close"]
        # Calculate the distance of the cost prcie from the stop-loss value
        curr_sl_distance = np.abs(cost_price - sl_price)

        level_met = None
        exit_adjustment = None

        if len(self.exit_levels) == 0 or len(self.exit_sizes) == 0:
             #print("levels exhausted")
             return (None, None)

        #for short
        if self.direction == TradeDirection.SHORT :
            #first available exit point
            level_price = cost_price + self.exit_levels[0] * curr_sl_distance 
            if current_price > level_price:
                    # Remove the first element from exit_levels.
                    level_met = self.exit_levels.pop(0)
                    # Remove the first element from exit_sizes.
                    exit_adjustment = self.exit_sizes.pop(0)
        #for shorts
        else:
            #price of first available exit point
            level_price = cost_price - self.exit_levels[0] * curr_sl_distance 
            if current_price < level_price:
                    # Remove the first element from exit_levels.
                    level_met = self.exit_levels.pop(0)
                    # Remove the first element from exit_sizes.
                    exit_adjustment = self.exit_sizes.pop(0)

        return level_met, exit_adjustment

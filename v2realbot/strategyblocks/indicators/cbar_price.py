from v2realbot.strategy.base import StrategyState
from v2realbot.enums.enums import RecordType

def populate_cbar_tick_price_indicator(data, state: StrategyState):
    conf_bar = data['confirmed']

    #specifická sekce pro CBARVOLUME, kde vzdy máme nova data v confirmation baru (tzn. tickprice pocitame jak pri potvrzenem tak nepotvrzenem)
    if state.rectype in (RecordType.CBARVOLUME, RecordType.CBARDOLLAR, RecordType.CBARRENKO):
        try:
            tick_price = data['close']
            tick_delta_volume = data['volume'] - state.vars.last_tick_volume

            state.cbar_indicators.tick_price[-1] = tick_price
            state.cbar_indicators.tick_volume[-1] = tick_delta_volume
        except:
            pass

        state.ilog(lvl=0,e=f"TICK PRICE CBARV {tick_price} VOLUME {tick_delta_volume} {data['confirmed']=}", prev_price=state.vars.last_tick_price, prev_volume=state.vars.last_tick_volume)

        state.vars.last_tick_price = tick_price
        state.vars.last_tick_volume = data['volume']

        if conf_bar == 1:
            #pri potvrzem CBARu nulujeme counter volume pro tick based indicator
            state.vars.last_tick_volume = 0
            state.vars.next_new = 1

    #pro standardní CBARy
    else:
        if conf_bar == 1:
            #pri potvrzem CBARu nulujeme counter volume pro tick based indicator
            state.vars.last_tick_volume = 0
            state.vars.next_new = 1


        #naopak pri CBARu confirmation bar nema zadna nova data (tzn. tickprice pocitame jen pri potvrzenem)
        else:
            try:
                #pokud v potvrzovacím baru nebyly zmeny, nechavam puvodni hodnoty
                # if tick_delta_volume == 0:
                #     state.indicators.tick_price[-1] = state.indicators.tick_price[-2]
                #     state.indicators.tick_volume[-1] = state.indicators.tick_volume[-2]
                # else:

                #tick_price = round2five(data['close'])
                tick_price = data['close']
                tick_delta_volume = data['volume'] - state.vars.last_tick_volume

                state.cbar_indicators.tick_price[-1] = tick_price
                state.cbar_indicators.tick_volume[-1] = tick_delta_volume
            except:
                pass

            state.ilog(lvl=0,e=f"TICK PRICE CBAR {tick_price} VOLUME {tick_delta_volume} {data['confirmed']=}", prev_price=state.vars.last_tick_price, prev_volume=state.vars.last_tick_volume)

            state.vars.last_tick_price = tick_price
            state.vars.last_tick_volume = data['volume']
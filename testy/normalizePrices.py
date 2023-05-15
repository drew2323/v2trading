from v2realbot.utils.utils import price2dec

bacprice = 28.90
cprice = 45.00

bacma = [28.90,28.95,28.96]
bactick = [0.1, 0.1, 0.1]

cma = [45, 45.50, 45.90]


baseprice = 28.90
basetick = 0.01


baseratio = cprice/baseprice

ctick = baseratio*basetick

#print(ctick)

#normalized price for tick 0.01
NORMALIZED_TICK_BASE_PRICE = 30.00

# prevede normalizovany tick na tick relevantni dane cene
# u cen pod 30, vrací 0.01. U cen nad 30 vrací pomerne zvetsene, 
def get_tick(price: float, normalized_ticks: float = 0.01):
    """
    prevede normalizovany tick na tick odpovidajici vstupni cene
    vysledek je zaokoruhleny na 2 des.mista

    u cen pod 30, vrací 0.01. U cen nad 30 vrací pomerne zvetsene, 

    """
    if price<NORMALIZED_TICK_BASE_PRICE:
        return normalized_ticks
    else:
        #ratio of price vs base price
        ratio = price/NORMALIZED_TICK_BASE_PRICE
        return price2dec(ratio*normalized_ticks)


print(get_tick(40,0.04))
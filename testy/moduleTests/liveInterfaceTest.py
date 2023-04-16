from v2realbot.config import Keys, get_key
from v2realbot.enums.enums import Mode, Account, OrderSide
from v2realbot.interfaces.live_interface import LiveInterface
from msgpack import packb, unpackb
key = get_key(mode=Mode.PAPER, account=Account.ACCOUNT1)
symbol = "BAC"
li = LiveInterface(symbol=symbol, key=key)


##tady jsem skoncil - otestovat tento kod na variantach 
# pendinbuys na PAPER
#pak dat do Vykladaci ENTRY a otestovat i na BT
data = {}
data["index"] = 30
consolidation_bar_count = 10
pendingbuys = {'22dd3fe21-2c61-4ddd-b7df-cbdb3c1f7b79': '29.63', 'fe7b4baa-ef61-4867-b111-b1c3fc016dce': '29.59', '40253d42-bc00-4476-8f7a-28449fc00080': '29.57'}
 
##konzolidace kazdy Nty bar dle nastaveni
if int(data["index"])%int(consolidation_bar_count) == 0:
    print("***Consolidation ENTRY***")

    orderlist = li.get_open_orders(symbol=symbol, side=None)
    #print(orderlist)
    pendingbuys_new = {}
    limitka = None
    jevylozeno = 1
    for o in orderlist:
        if o.side == OrderSide.SELL:
            print("Puvodni LIMITKA", limitka)
            limitka = o.id
            print("Přepsaná LIMITKA", limitka)
        if o.side == OrderSide.BUY:
            pendingbuys_new[str(o.id)]=o.limit_price

    if pendingbuys_new != pendingbuys:
        print("ROZDILNA PENDINGBUYS přepsána")
        print("OLD",pendingbuys)
        pendingbuys = unpackb(packb(pendingbuys_new))
        print("NEW", pendingbuys)
    print("OLD jevylozeno",jevylozeno)
    if len(pendingbuys) > 0:
        jevylozeno = 1
    else:
        jevylozeno = 0
    print("NEW jevylozeno",jevylozeno)

    #print(limitka)
    #print(pendingbuys_new)
    #print(pendingbuys)
    #print(len(pendingbuys))
    #print(len(pendingbuys_new))
    #print(jevylozeno)
    print("***CONSOLIDATION EXIT***")

else:
    print("no time for consolidation", data["index"])


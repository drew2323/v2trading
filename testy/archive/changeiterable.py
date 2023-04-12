# to test change iterable (adding items) while iterating

class Notif:
    def __init__(self,time):
        self.time = time

open_orders = []

for i in range(1,10):
    open_orders.append(Notif(i))

print("cele pole objektu",open_orders)

# Here, 'reversed' returns a lazy iterator, so it's performant! reversed(l):

#musi fungovat removing stare a pridavani novych

#this list contains all not processed notification, that we try to process during this iteration
#if time is not right we leave the message for next iter
#if time is right we process the message (- note it can trigger additional open_orders, that are added to queue)

def process_message(notif: Notif):
    global open_orders
    if notif.time % 2 == 0 and notif.time < 300:
        open_orders.append(Notif(notif.time+50))
        
todel = []
for i in open_orders:
    print("*******start iterace polozky", i.time)
    process_message(i)
    print("removing element",i.time)
    todel.append(i)
    print("*****konec iterace", i.time)
    print()

print("to del", todel)
#removing processed from the list
for i in todel:
    open_orders.remove(i)


print("cely list po skonceni vseho")
for i in open_orders: print(i.time)



""""
pred iteraci se zavola synchroné
EXECUTE open orders(time)
    - pokusi se vytvorit vsechny otevrene ordery do daneho casu (casu dalsi iterace)
    - podporuje i volani callbacku a to vcetne pokynu vytvoreneho z pokynu
    - tento novy pokyn muze byt i take exekuovan pokud se vcetne roundtripu vejde do daneho casu
    pripadne soucasne vytvoreni i exekuci pokynu


"""


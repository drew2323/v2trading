from strategy import MyStrategy, StrategyState, Strategy
from enums import RecordType, StartBarAlign
from config import API_KEY, SECRET_KEY, MAX_BATCH_SIZE, PAPER
from indicators import ema
from rich import print
from utils import ltp, isrising, isfalling,trunc



""""
TBD - zpomalit  - nekupovat okamzite nechat dychat


MA Vykládcí Strategie s LIMIT BUY
    # aktualni nastaveni - VELMI AGRESIVNI, STALE KUPUJE, IDEALNI NA POTVRZENE RUSTOVE DNY
    - jede na 10s
    - BUY and HOLD alternative
    - dat do seznamu hotovych strategii

atributy:
    ticks2reset - počet ticků po kterých se resetnou prikazy pokud neni plneni

 TODO:
 - pridat reconciliaci po kazdem X tem potvrzenem baru - konzolidace otevrenych pozic a limitek
 - do kazde asynchronni notifkace orderupdate dat ochranu, kdyz uz ten stav neplati (tzn. napr. pro potvrzeni buye se uz prodalo)
 - podchytit: kdykoliv limitka neexistuje, ale mam pozice, tak ji vytvorit (podchytit situace v rush hours) 
 - cancel pendign buys -  dictionary changed size during iteration podychytit. lock
"""
ticks2reset = 0.03
#TODO pokud bar klesne o jeden nebo vice - tak signál - DEFENZIVNI MOD
#TODO pouzivat tu objekt ochrana (ktery jen vlozim do kodu a kdyz vrati exceptionu tak jdeme do dalsi iterace)
# tak zustane strategie cista
#TODO rušit (pending buys) když oe.poz = 0 a od nejvetsi pending buys je 
# ltp.price vice nez 5 ticků

def next(data, state: StrategyState):

    def vyloz(pozic: int):
        print("vykladame na pocet pozic", pozic)
        # defenzivni krivka
        curve = [0.01, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02,0.03,0.03,0.03,0.03, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04]
        #cent curve = [0.01, 0.01, 0.01,0.01, 0.01, 0.01,0.01, 0.01,0.01, 0.01, 0.01, 0.01,0.01, 0.01,0.01, 0.01,0.01, 0.01,0.01, 0.01,0.01, 0.01,0.01, 0.01,0.01, 0.01]
        #defenzivnejsi s vetsimi mezerami v druhe tretine a vetsi vahou pro dokupy

        # krivka pro AVG, tzn. exponencialne pridavame 0.00
        curve = [0.01, 0, 0.01, 0, 0, 0.01, 0, 0, 0, 0.01, 0, 0, 0, 0, 0.01, 0, 0, 0, 0, 0, 0.01, 0,0,0,0,0,0, 0.01, 0,0,0,0,0,0,0,0,0.01,0,0,0,0,0,0,0,0,0, 0.01,0,0,0,0,0,0,0,0,0,0.01, 0,0,0,0,0,00,0,0,0, 0.5, 0,0,0,0,0.5,0,0,0]
 
        # 10ty clen je o 0.05 tzn.triggeruje nam to tick2reset
        #curve = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.02, 0.05, 0.01, 0.04, 0.01, 0.01, 0.04, 0.05, 0.03, 0.05, 0.01, 0.03, 0.01,0.01, 0.04, 0.01, 0.05,0.01, 0.01,0.01, 0.01]
 
        #defenzivni krivku nastavime vetsimi mezerami a v nich 0.01 - tim se prida vetsi mnostvi a vic se naredi
        #  0.04, 0.01,

        #curve = [0.01,0.01, 0.01, 0.02, 0.02, 0.02, 0.02]
        #cena pro prvni objednavky
        price = trunc(float(ltp.price[state.oe.symbol]),2)
        print("aktualni cena pri vykladu - pro prvni", price)
        qty = int(state.variables.chunk)
        last_price = price
        if len(curve) < pozic:
            pozic = len(curve)
        #stejné ceny posilame jako jednu objednávku
        for i in range(0,pozic):
            price = round(float(price - curve[i]),2)
            if price == last_price:
                qty = qty + int(state.variables.chunk)
            else:
                #flush last_price and stored qty
                # OPT: pokud bude kupovat prilis brzy, osvedcila se prvni cena -0.01 (tzn. stavi prehodit last_price za price)
                state.oe.buy_l(price=last_price, size=qty, force=1)
                print(i,"BUY limitka - delta",curve[i]," cena:", price, "mnozstvi:", qty)
                qty = int(state.variables.chunk)

            last_price = price

            #TODO pokud cena stejna jako predchozi, tak navys predchozi - abychom nemeli vice objednavek na stejne cene (zbytecne)
            
            
            

    print("pending buys", state.oe.stratvars['pendingbuys'])
    print("je vylozeno",state.oe.stratvars['jevylozeno'])
    print("avg,poz,limitka",state.oe.avgp, state.oe.poz, state.oe.limitka)
    print("last buy price", state.oe.lastbuy)
    #CBAR protection,  only 1x order per CBAR - then wait until another confirmed bar
    if state.variables.blockbuy == 1:
        if state.bars.confirmed[-1] == 0:
            print("OCHR: multibuy protection. waiting for next bar")
            return 0
        # pop potvrzeni jeste jednou vratime (aby se nekoupilo znova, je stale ten stejny bar)
        # a pak dalsi vejde az po minticku
        else:
            # pro vykladaci
            state.variables.blockbuy = 0
            return 0


    #print(state.bars) .
    # print("next")
    # print(data)

    #TODO zkusit hlcc4
    try:
        ema_output = ema(state.bars.vwap, state.variables.MA)
        #trochu prasarna, EMAcko trunc na 3 mista - kdyz se osvedci, tak udelat efektivne
        ema_output = [trunc(i,3) for i in ema_output]
        print("emacko na wvap",state.variables.MA,":", ema_output[-5:])
    except:
        print("No data for MA yet")
   
    print("MA is falling",state.variables.Trend,"value:",isfalling(ema_output,state.variables.Trend))
    print("MA is rising",state.variables.Trend,"value:",isrising(ema_output,state.variables.Trend))

    ## testuje aktualni cenu od nejvyssi visici limitky
    ##toto spoustet jednou za X iterací - ted to jede pokazdé
    #pokud to ujede o vic, rusime limitky
    #TODO: zvazit jestli nechat i pri otevrenych pozicich, zatim nechavame
    #TODO int(int(state.oa.poz)/int(state.variables.chunk)) > X
    if state.oe.stratvars['jevylozeno'] == 1: # and int(state.oe.poz) == 0:
        #pokud mame vylozeno a cena je vetsi nez 0.04 
            if len(state.oe.stratvars['pendingbuys'])>0:
                a = max(state.oe.stratvars['pendingbuys'].values())
                print("max cena v orderbuys", a)
                if float(ltp.price[state.oe.symbol]) > float(a) + ticks2reset:
                    print("ujelo to vice nez o 4, rusime limit buye")
                    state.oe.cancel_pending_buys()
                    state.oe.stratvars['jevylozeno'] = 0
            
            #pokud je vylozeno a mame pozice a neexistuje limitka - pak ji vytvorim
            if int(state.oe.poz)>0 and state.oe.limitka == 0:
                #pro jistotu updatujeme pozice
                state.oe.avgp, state.oe.poz = state.oe.pos()
                if int(state.oe.poz) > 0:
                    cena = round(float(state.oe.avgp) + float(state.oe.stratvars["profit"]),2)
                    print("BUGF: limitka neni vytvarime, a to za cenu",cena,"mnozstvi",state.oe.poz)
                    print("aktuzalni ltp",ltp.price[state.oe.symbol])

                    try:
                        state.oe.limitka = state.oe.sell_noasync(cena, state.oe.poz)
                        print("vytvorena limitka", state.oe.limitka)
                    except Exception as e:
                        print("Neslo vytvorit profitku. Problem,ale jedeme dal",str(e))
                        pass
                        ##raise Exception(e)

    if state.oe.stratvars['jevylozeno'] == 0:
        print("neni vylozeno. Muzeme nakupovat")
        # testuji variantu, ze kupuji okamzite, nehlede na vyvoj
        if isfalling(ema_output,state.variables.Trend): # or 1==1:
            ## vyloz pro pocet pozic (maximalni minus aktualni)
            #kolik nam zbyva pozic
            
            #HOKUS: vykladame pouze polovinu pozic - dalsi polovinu davame v dalsimrunu
            # a = available pozice a/2            
            a = int(int(state.variables.maxpozic)/int(state.variables.chunk)-(int(state.oe.poz)/int(state.variables.chunk)))
            a = int(a)
            print("Vykladame na pocet pozic", a)
            
            
            vyloz(pozic=a)
            #blokneme nakupy na dalsi bar
            state.variables.blockbuy = 1
            state.oe.stratvars['jevylozeno'] = 1
             

        #ulozime id baru
        # state.variables.lastbuyindex = state.bars.index[-1]

    # je vylozeno
    else:
        ## po kazde 4te pozici delame revykladani na aktualni zbytek pozic
        if  (int(state.oe.poz)/(int(state.variables.chunk)) % 4 == 0):
            print("ctvrta pozice - v budoucnu realignujeme")
            # state.oe.cancel_pending_buys()
            # ##smazeme ihned pole - necekame na notifiaci
            # vyloz((int(state.variables.maxpozic)-int(state.oe.poz)/state.variables.chunk))


    #kazdy potvrzeny bar dotahneme pro jistotu otevřené objednávky a nahradíme si stav aktuálním

    #pro jistotu update pozic - kdyz se nic nedeje nedeje
    #pripadne dat pryc
    #print("upatujeme pozice")
    #state.oe.avgp, state.oe.poz = state.oe.pos()

def init(state: StrategyState):
    print("init - zatim bez data")
    print(state.oe.symbol)
    print(state.oe.pos())
    print()

def main():  
    stratvars = dict(maxpozic = 2000, chunk = 20, MA = 3, Trend = 4, profit = 0.01, blockbuy=0, lastbuyindex=0, pendingbuys={}, jevylozeno=0)
    s = MyStrategy("BAC",paper=PAPER, next=next, init=init, stratvars=stratvars)
    s.add_data(symbol="BAC",rectype=RecordType.CBAR,timeframe=12,filters=None,update_ltp=True,align=StartBarAlign.ROUND,mintick=4)

    s.start()

if __name__ == "__main__":
    main()

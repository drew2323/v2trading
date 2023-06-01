def buy_conditions_met():
     
    buy_cond = dict(AND=dict(), OR=dict())
    ##group eval rules. 1. single 2. AND 3. ORS
    #cond groups ["AND"]
    #cond groups ["OR"]
    #no cond group - takes first
    #TEST BUY SIGNALu z cbartick_price - 3klesave za sebou
    #buy_cond['tick_price_falling_trend'] = isfalling(state.cbar_indicators.tick_price,state.vars.Trend)
    buy_cond["AND"]["1and"] = True
    buy_cond["AND"]["2and"] = False
    buy_cond["OR"]["3or"] = False
    buy_cond["OR"]["4or"] = False
    buy_cond["5single"] = False
    buy_cond["5siddngle"] = False

    return eval_cond_dict(buy_cond)

def eval_cond_dict(buy_cond: dict):
    """
    group eval rules. 1. single 2. AND 3. ORS
    """
    msg = ""
    #eval single cond
    for klic in buy_cond:
        if klic in ["AND","OR"]: continue
        else:
            if buy_cond[klic]:
                print(f"BUY SIGNAL {klic}")
                return True

    ##check AND group
    if 'AND' in buy_cond.keys():
        for key in buy_cond["AND"]:

            if buy_cond["AND"][key]:
                ret = True
                msg += key + " AND "
            else:
                ret = False
                break
        if ret:
            print(f"BUY SIGNAL {msg}")
            return True
    #eval OR groups 
    if "OR" in buy_cond.keys():
        for key in buy_cond["OR"]:
            if buy_cond["OR"][key]:
                print(f"BUY SIGNAL OR {key}")
                return True
            
    return False
    
buy_conditions_met()
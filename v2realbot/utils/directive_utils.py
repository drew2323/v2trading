#utils pro práci s direktivami (napr. stratvars)


#pomocna funkce pro vytvoreni podminkoveho directory z direktiv v novem formatu
# direktiva v CONDITIONS sekci u daneho SIGNALU
# 
# stratvars.signals.trendfollow.conditions
# slope30.short_if_below = 0.3
# slope20.AND.lonf_if_above = 2
# slope30.AND.ACTION_if_above
# ACTION: long_, short_, exit_ (action)
# AND: optional operator AND/OR

#funkce ktera z dane sekce direktiv vraci adu nakonfigurovanych podminek pro danou akci  (work_dict)
#pouziti: napr. ze signals.trendfollow.conditions chci akce short (pripadne activate, exit ...)

def get_conditions_from_configuration(action: str, section: dict):
    reslist = dict(AND=[], OR=[])
    
    for indname, condition in section.items():
        #prvnim je vzdy indikator na ktery se direktiva odkazuje, tzn. projedeme vsechny tyto indikatory

        # #pokud je zde neco jineho nez dict, tak ignorujeme
        if not isinstance(condition, dict):
            continue
        for directive, value in condition.items():
            if directive.startswith(action):
                reslist["OR"].append((indname, directive, value))
            if directive == "AND":
                #vsechny buy direktivy, ktere jsou pod AND
                for key, val in value.items():
                    if key.startswith(action):
                        reslist["AND"].append((indname, key, val))
            if directive == "OR" :
                #vsechny buy direktivy, ktere jsou pod OR
                for key, val in value.items():
                    if key.startswith(action):
                        reslist["OR"].append((indname, key, val))
    
    #vysledek: v kazdem klici truple (indname, volba, hodnota) 
    return reslist
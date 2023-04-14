from v2realbot.utils.utils import AttributeDict

stratvars_parsed_old = AttributeDict(maxpozic = 250,
                          chunk = 10,
                          MA = 3,
                          Trend = 3,
                          profit = 0.02,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None,
                          jevylozeno=0,
                          vykladka=5,
                          curve = [0.01, 0.01, 0.01, 0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01],
                          blockbuy = 0,
                          ticks2reset = 0.04)

stratvars_parsed_new = AttributeDict(maxpozic = 250,
                          chunk = 10,
                          MA = 3,
                          Trend = 3,
                          profit = 0.02,
                          lastbuyindex=-6,
                          pendingbuys={},
                          limitka = None,
                          jevylozeno=0,
                          vykladka=5,
                          curve = [0.01, 0.01, 0.01, 0, 0.02, 0.02, 0.01,0.01, 0.01,0.03, 0.01, 0.01, 0.01,0.04, 0.01,0.01, 0.01,0.05, 0.01,0.01, 0.01,0.01, 0.06,0.01, 0.01,0.01, 0.01],
                          blockbuy = 0,
                          ticks2reset = 0.04)


STRATVARS_UNCHANGEABLES = ['pendingbuys', 'blockbuy', 'jevylozeno', 'limitka']

changed_keys = []
#get changed values
for key,value in stratvars_parsed_new.items():
    if value != stratvars_parsed_old[key]:
        changed_keys.append(key)

print("changed before check", changed_keys)
#remove keys that cannot be changed
for k in changed_keys:
    if k in STRATVARS_UNCHANGEABLES:
        print(k, "cant be changed removing")
        changed_keys.remove(k)

print("clean changed keys", changed_keys)

for k in changed_keys:
    print("injecting",k, "value", stratvars_parsed_new[k])

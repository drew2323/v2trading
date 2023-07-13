from v2realbot.utils.utils import crossed_down

pole = [48.495432098765434, 48.48296296296296, 48.480617283950615, 48.47475308641976, 48.467543209876546]
thr = 48.4778923123465



res = crossed_down(threshold=thr, list=pole)

print(res)
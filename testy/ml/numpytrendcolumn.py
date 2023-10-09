import numpy as np

y = np.arange(20).reshape(4,5)
print("y",y)
# y = y[1:5:2,]
y = y[::2,::2]
print("y",y)


# a = np.arange(30).reshape(-1,5)

# #pole_posunute o radek dopredu - future a
# fa = a.copy()
# fa = fa[1:]
# print("fa",fa)

# #acko orizneme vzadu - aby byly stejne dlouhe
# a = a[:-1]
# print(a)
# #a pak porovnáme jejich poslední sloupce a vysledek dáme jako další sloupec s 1 nebo 0
# #nicmene melo by to nejak jit i bez pomocného pole
# posl_sloupec=a[:,-1:]<fa[:,-1:]
# print(posl_sloupec)
# #sloupec 1/0 zda je hodnota nizsi nez hodnota o jeden radek vpredu
# #tak si muzu nadefinovat 1ky kdyz je rising for 5 bars - udealt funkcni
# a = np.hstack((a, posl_sloupec))
# print(a)
# #print(a[posl_sloupec>4])


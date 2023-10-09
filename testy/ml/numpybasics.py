import numpy as np

a = np.arange(20).reshape(2,2,5)
print(a)

#b = np.zeros((3,4))
b = np.arange(12).reshape(3,4)
print(b)
#max z kazdeho sloupce
c =  np.max(b, axis=0)
#suma kazdeho radku
c =  np.sum(b, axis=1)
c = c.reshape(3,1)
#sumu pridam na konec kazdeho radku, tzn.pripojim sloupce (horizontalne)
d=np.hstack((b,c))
print(d)

#indexovani booleanem
e = np.arange(12).reshape(3,4)
f = e < 5
print(e,f)
print(e[f])
#vsechny mensi nez 5 se stanou 0
e[e<5] = 0
print(e)


# c = np.ones((2,2))
# c = c.reshape(1,4)
# print(c)
# print(c*b)

# d = np.arange(4).reshape(2,2)
# e = d.copy()

# print("d",d)
# print("e",e)
# print(d*e)
# print(d@e)
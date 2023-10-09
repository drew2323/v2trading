import numpy as np

t = np.array([[[1,2,3,4,5], [2,2,2,2,2]],

              [[3,3,3,3,3], [4,4,4,4,4]],

              [[5,5,5,5,5], [6,6,6,6,6]]])

print(t.shape, t.ndim, t.dtype)

print(t[0:2].shape)


#nasledujici je totozne
a = t[:2]
b = t[0:2, :, :]
c = t[0:2, 0:2, 0:5]

#posledni dve cisla kazdeho elementu tensoru 1
a = t[1, :, 3:]

#prostredni 3 cisla z kazdeho elementu
a = t[:, :, 1:-1]
# print(a==b)
print(a)
# print(b)
# print(c)

print(t.reshape((6,5)))
print(t.reshape((30)))
print(t.reshape((30,1)))
print(np.transpose(t))


#operations
u =np.array([5,2,1,1,4])
print(t+u)
from rich import print
from icecream import ic



def p(*args, **kwargs):
    if ic.enabled:
        print(*args, **kwargs)
    else:
        


p("nazdar")
a = "helo"
b = dict(a=123,b="CUS")
c = 123

p(a,b,c,"nazdar")
p("nazdar","covece",a,c)
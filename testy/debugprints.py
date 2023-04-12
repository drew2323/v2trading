import inspect
import re
import pprint
from rich import print
from datetime import datetime

def d(x, n=None):
    frame = inspect.currentframe().f_back
    s = inspect.getframeinfo(frame).code_context[0]
    print(s)
    r = re.search(r"\((.*)\)", s).group(1)
    print("{} = {}".format(r,x), n)

def prinfo(*args):
    frame = inspect.currentframe().f_back
    s = inspect.getframeinfo(frame).code_context[0]
    r = re.search(r"\((.*)\)", s).group(1)
    print(r)
    vnames = r.split(", ")
    print(vnames)
    for i,(var,val) in enumerate(zip(vnames, args)):
        print(f"{var} = {val}")

def p(var, n = None):
    if n: print(n, f'{var = }')
    else: print(f'{var = }')

a = 34
b= dict(a1=123,b2="cus")
c = "covece"
#p(a)
#d(b, "neco")

p(a)
p(a,"neco")
prinfo(b,c)



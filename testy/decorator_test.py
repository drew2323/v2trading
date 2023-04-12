import inspect

class LiveInterface:

    def prepost(f):
        def prepost_wrapper(self, *args, **kwargs):
            pre_name  = 'pre_'  + f.__name__
            post_name = 'post_' + f.__name__
            print(dir(self))
            print(self.__repr__)
            res = 1
            if hasattr(self, pre_name):
                res = getattr(self, pre_name) (*args, **kwargs)
            if res > 0:
                ret = f(self, *args, **kwargs)
                if hasattr(self, post_name): getattr(self, post_name)(*args, **kwargs)
                return ret
            else:
                print("plugin vratil zaporné. Skipping")
                return res
        return prepost_wrapper
    

    def __init__(self) -> None:
        pass

    @prepost
    def buy(self):
        print("buy")

## 
# class NewInterface(LiveInterface):
#     def __init__(self) -> None:
#         super().__init__()
    


class Strategy():
    def __init__(self) -> None:
        #tady is prepnu na live or bt
        self.interface = Strategy.StrategyInterface()
        self.neco = 1
        #self.interface.buy()
        #self.interface = LiveInterface()
        #self.interface.buy = self.buy_more
        self.interface.buy()



    class StrategyInterface(LiveInterface):
        def __init__(self) -> None:
            super().__init__()

        def pre_buy(self):
            print("prebuy")
            return 3

        def post_buy(self):
            print("postbuy")
            return -2



def main():
    a = Strategy()

if __name__ == "__main__":
    main()

    ##
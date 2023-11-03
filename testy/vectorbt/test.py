import vectorbt as vb


class ShortOnCloseBreakoutStrategy:
    def init(self):
        self.last_close = self.data.close[-1]

    def next(self):
        # Enter a short position when the price is below the last day's close
        if self.data.close < self.last_close:
            self.sell()

        # Exit the short position after 10 ticks
        elif self.data.close > self.last_close + 10:
            self.buy()

# Create a backtest object
#backtest = vb.Backtest(ShortOnCloseBreakoutStrategy())

# Load the closing prices for the assets in the portfolio
close = vb.YFData.download('AAPL', start='2023-01-01').get('Close')
print(close)
# Backtest the strategy
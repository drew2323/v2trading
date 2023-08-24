from alpaca.data.live.stock import StockDataStream
from v2realbot.config import ACCOUNT2_PAPER_API_KEY, ACCOUNT2_PAPER_SECRET_KEY, ACCOUNT2_PAPER_FEED

# keys required
stock_stream = StockDataStream(ACCOUNT2_PAPER_API_KEY, ACCOUNT2_PAPER_SECRET_KEY, raw_data=True, websocket_params={}, feed=ACCOUNT2_PAPER_FEED)

# async handler
async def trade_data_handler(data):
    # quote data will arrive here
    print(data)

stock_stream.subscribe_trades(trade_data_handler, "BAC")

stock_stream.run()
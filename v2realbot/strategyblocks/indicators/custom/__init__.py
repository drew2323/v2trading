import os
# import importlib
# from v2realbot.strategyblocks.indicators.custom.opengap import opengap

for filename in os.listdir("v2realbot/strategyblocks/indicators/custom"):
    if filename.endswith(".py") and filename != "__init__.py":
       # __import__(filename[:-3])
        __import__(f"v2realbot.strategyblocks.indicators.custom.{filename[:-3]}")
        #importlib.import_module()


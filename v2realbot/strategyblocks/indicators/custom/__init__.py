import os
# import importlib
# from v2realbot.strategyblocks.indicators.custom.opengap import opengap
# Get the directory of the current file (__init__.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

for filename in os.listdir(current_dir):
    if filename.endswith(".py") and filename != "__init__.py":
       # __import__(filename[:-3])
        __import__(f"v2realbot.strategyblocks.indicators.custom.{filename[:-3]}")
        #importlib.import_module()


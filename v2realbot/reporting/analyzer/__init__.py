import os

for filename in os.listdir("v2realbot/reporting/analyzer"):
    if filename.endswith(".py") and filename != "__init__.py":
       # __import__(filename[:-3])
        __import__(f"v2realbot.reporting.analyzer.{filename[:-3]}")
        #importlib.import_module()


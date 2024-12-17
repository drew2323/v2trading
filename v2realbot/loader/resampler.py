from v2realbot.enums.enums import RecordType, StartBarAlign
from datetime import timedelta
from v2realbot.common.model import bar_template
from v2realbot.utils.utils import AttributeDict
import v2realbot.strategy.base as strategybase
import copy

class Resampler:
    def __init__(self, symbol: str, bar_align: StartBarAlign, bartype: RecordType, rsmpl_resolution: str, storage: dict):
        self.symbol = symbol
        self.bar_align = bar_align
        self.bartype = bartype
        self.rsmpl_resolution = rsmpl_resolution
        self.storage = storage
        self.resampled_bar = None
        self.index_counter = 0
        self.name = self.symbol + '_' + self.rsmpl_resolution
        self.storage[self.name] = AttributeDict(copy.deepcopy(bar_template))
      
        self.time_unit = ''.join(char.lower() for char in self.rsmpl_resolution if char.isalpha())
        self.time_interval = int(''.join(char for char in self.rsmpl_resolution if char.isdigit()))
                
        match self.time_unit:
            case 's':
                self.rsmpl_resolution = int(self.time_interval)
            case 'm':
                self.rsmpl_resolution = int(self.time_interval*60)
            case 'h':
                self.rsmpl_resolution = int(self.time_interval*3600)
            case 'd':
                self.rsmpl_resolution = int(self.time_interval*86400)
            case _:
                raise Exception("Error: Time format not recognized.")
                

    def update_resampled_bar(self, new_bar_data: dict) -> None:
            self.resampled_bar["high"] = max(self.resampled_bar["high"], new_bar_data["high"])
            self.resampled_bar["low"] = min(self.resampled_bar["low"],  new_bar_data["low"])
            self.resampled_bar["close"] = new_bar_data["close"]
            self.resampled_bar["hlcc4"] = (self.resampled_bar["high"] + self.resampled_bar["low"] +  self.resampled_bar["close"] +  self.resampled_bar["close"]) / 4
            self.resampled_bar["volume"] = self.resampled_bar["volume"] + new_bar_data["volume"]
            self.resampled_bar["trades"] = self.resampled_bar["trades"] + new_bar_data["trades"]
            self.resampled_bar["vwap"] = (self.resampled_bar["vwap"]*self.resampled_bar["volume"] + new_bar_data["vwap"]*new_bar_data["volume"]) / (self.resampled_bar["volume"] + new_bar_data["volume"])
            self.resampled_bar["updated"] = new_bar_data["updated"]


    def initiate_resampled_bar(self, new_bar_data: dict) -> None:
        if self.bar_align == StartBarAlign.ROUND:
            update_minutes = int(new_bar_data["time"].minute - new_bar_data["time"].minute % (self.rsmpl_resolution/60))
            start_time = new_bar_data["time"].replace(minute = update_minutes, second = 0, microsecond = 0)
            
        if self.bar_align == StartBarAlign.RANDOM: 
            start_time = new_bar_data["time"]
            
        self.resampled_bar = {
            "high": new_bar_data["high"],
            "low": new_bar_data["low"],
            "volume": new_bar_data["volume"],
            "close": new_bar_data["close"],
            "hlcc4": new_bar_data["hlcc4"],
            "open": new_bar_data["open"],
            "trades": new_bar_data["trades"],
            "resolution": self.rsmpl_resolution,
            "confirmed": new_bar_data["confirmed"],
            "vwap": new_bar_data["vwap"],
            "updated": new_bar_data["updated"],
            "index": self.index_counter,
            "time": start_time
            }     


    def process_bar(self, inputbar: dict) -> None:
        if self.resampled_bar is None:
            self.initiate_resampled_bar(new_bar_data=inputbar)
        else:
            if self.bartype == RecordType.BAR:
                if (self.resampled_bar["time"] + timedelta(seconds=self.rsmpl_resolution)) > inputbar["time"]:
                    self.update_resampled_bar(new_bar_data=inputbar) 
                else:
                    strategybase.Strategy.append_bar(self.storage[self.name], self.resampled_bar)
                    self.resampled_bar = None
                    self.index_counter +=1 
        
            if self.bartype == RecordType.CBAR:
                if (self.resampled_bar["time"] + timedelta(seconds=self.rsmpl_resolution)) > inputbar["time"]:
                        self.update_resampled_bar(new_bar_data=inputbar)
                        strategybase.Strategy.replace_prev_bar(self.storage[self.name], self.resampled_bar)
                else: 
                    if inputbar["confirmed"] == 1:
                        self.update_resampled_bar(new_bar_data=inputbar)
                        strategybase.Strategy.replace_prev_bar(self.storage[self.name], self.resampled_bar)
                        self.resampled_bar = None   
                        self.index_counter +=1   
                    else:
                        self.index_counter += 1
                        self.initiate_resampled_bar(new_bar_data=inputbar)

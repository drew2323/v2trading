from v2realbot.utils.utils import AttributeDict
indicators = AttributeDict(time=[])

for key,value in indicators.items():
    if key != "time":
        indicators[key].append(0)


#as indicators are stored vector  based, time is populated for each iteration
def populate_indicator_time(self, item):
        if self.rectype == RecordType.BAR:
            #jako cas indikatorů pridavame cas baru, jejich hodnoty se naplni v nextu
            self.state.indicators['time'].append(item['time'])
        elif self.rectype == RecordType.TRADE:
            pass
        elif self.rectype == RecordType.CBAR:
            #novy vzdy pridame
            if self.nextnew:
                self.state.indicators['time'].append(item['time'])
                self.append_bar(self.state.bars,item)
                self.nextnew = 0
            #nasledujici updatneme, po potvrzeni, nasleduje novy bar
            else:
                if item['confirmed'] == 0:
                    self.state.indicators['time'][-1]=item['time']
                    self.replace_prev_bar(self.state.bars,item)
                #confirmed
                else:
                    self.state.indicators['time'][-1]=item['time']
                    self.replace_prev_bar(self.state.bars,item)
                    self.nextnew = 1
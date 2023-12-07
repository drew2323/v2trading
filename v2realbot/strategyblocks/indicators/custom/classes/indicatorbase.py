class IndicatorBase:
    def __init__(self, state):
        self.state = state
        self.data = None
        self.prev_data = None

    def next(self, data):
        #something
        self.prev_data = data
        return None  # No signal
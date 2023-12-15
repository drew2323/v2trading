from collections import deque
from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

class VolumeNeeded2Move(IndicatorBase):
    """
    VOLUME NEEDED FOR MOVEMENT

    This indicator measures the volume required to move the price by a specified amount either upwards or downwards.
    The track_mode parameter determines the direction of price movement to be tracked.
    When the threshold for the opposite movement direction is reached, the indicator resets but returns the previous value.
    
    
    TODO ted se volume neresetuje, ale porad nacita ??? !!

    NOTE pozor dela to neco trohcu jinyho

    ## pocita to average volume per unit of price movement (kolik VOLUME stála(spotřebovala) kumulativně 1 jednotuka pohybu - to je zajimavý)
    - tzn. uloží si to za danou jednotku volume k jejimu dosazeni a ulozi si
        TOTO VOLUME, JEDNOTKA k dosazeni
        45666, 0.03
        36356536, 0.03
        33333, 0.03

        a pak spocte prumer kolik prumerne stala jednotka za cele predchozi obdobi a toto cele vraci

    projit, jak by to spravne melo fungovat pro UP and DOWN


    1) zkusit vracet ty konkretni  nekumulativni hodnoty za obdobi prekonani (nebo prumernou "cenu" jednotky)

    2) kumulovat podle okna (tzn. ze vracim prumernou cenu za jednotku za rolling window)


    TODO vrácena verze s absolutním thresholdem, která fungocvala.
    projít a zkusit relativní threshold nebo nejak uložit natvrdo ten pct ve formě ticku a ten používat po celou dobu, aby se nám neměnil
    
    PCT verze zde:
    #https://chat.openai.com/share/954a3481-f43f-43ee-8cb5-c2278384fa20

    referenční obrázky:https://trading.mujdenik.eu/xwiki/bin/view/Trading-platform/Indicators-detail/VolumeNeeded2Move/
    případně si vytvořit ref runny z této abs verze


    TODO pridat jeste time_window, kdy pro CUM bude vracet jen za dane okno (promyslet)
    """
    #TYPE - last or cumulative
    def __init__(self, price_movement_threshold, track_mode='up', return_type="cum", state=None):
        super().__init__(state)
        self.price_movement_threshold_tmp = price_movement_threshold
        self.price_movement_threshold = None
        self.track_mode = track_mode
        self.price_volume_data = deque()  # Stores tuples of (price, volume)
        self.last_price = None
        self.accumulated_volume = 0
        self.last_avg_volume_per_price_movement = 0
        self.return_type = return_type

    def next(self, close, volume):
        new_price = close[-1]
        new_volume = volume[-1]

        #pri prvni iteraci udelame z pct thresholdu fixni tick a ten pak pouzivame
        if self.price_movement_threshold is None:
            self.price_movement_threshold = (new_price / 100) * self.price_movement_threshold_tmp

            print("threshold in ticks:",self.price_movement_threshold )

        # Initialize last_price if not set
        if self.last_price is None:
            self.last_price = new_price

        # Accumulate volume
        self.accumulated_volume += new_volume

        # Calculate price change
        price_change = new_price - self.last_price

        # Check if the price movement threshold is reached
        reset_indicator = False
        if (self.track_mode == 'up' and price_change >= self.price_movement_threshold) or \
           (self.track_mode == 'down' and price_change <= -self.price_movement_threshold):
            self.price_volume_data.append((self.accumulated_volume, abs(price_change)))
            reset_indicator = True
        elif (self.track_mode == 'up' and price_change <= -self.price_movement_threshold) or \
             (self.track_mode == 'down' and price_change >= self.price_movement_threshold):
            reset_indicator = True

        # Reset if threshold is reached for either direction
        if reset_indicator:
            self.accumulated_volume = 0
            self.last_price = new_price
            if len(self.price_volume_data) > 0:
                #print("pred resetem",self.price_volume_data)
                total_volume, total_price_change = zip(*self.price_volume_data)
                #print("total volume, price change",total_volume,total_price_change)
                #CELKEM PRUMER VOLUME za danou zemnu
                if self.return_type=="cum":
                    self.last_avg_volume_per_price_movement = sum(total_volume)/len(total_volume) #/ sum(total_price_change)
                #(last)
                else:
                    #KONKRETNI zA PREDCHOZI CAST
                    self.last_avg_volume_per_price_movement = total_volume[-1]
 
        return self.last_avg_volume_per_price_movement


#PCT VARIANT

# from collections import deque
# from v2realbot.strategyblocks.indicators.custom.classes.indicatorbase import IndicatorBase

# class VolumePriceMovementIndicator(IndicatorBase):
#     """
#     This indicator measures the volume required to move the price by a specified percentage.
#     It tracks the accumulated volume since the last time the price moved by the predefined threshold.
#     """
#     def __init__(self, price_movement_threshold_pct, state=None):
#         super().__init__(state)
#         # Price movement threshold is now a percentage
#         self.price_movement_threshold_pct = price_movement_threshold_pct / 100.0  # Convert to decimal
#         self.price_volume_data = deque()  # Stores tuples of (price, volume)
#         self.last_price = None
#         self.accumulated_volume = 0

#     def next(self, index, close, volume):
#         new_price = close[-1]
#         new_volume = volume[-1]

#         # Initialize last_price if not set
#         if self.last_price is None:
#             self.last_price = new_price

#         # Accumulate volume
#         self.accumulated_volume += new_volume

#         # Calculate percentage price change relative to the last price
#         price_change_pct = abs((new_price - self.last_price) / self.last_price)
        
#         # Check if price movement threshold is reached
#         if price_change_pct >= self.price_movement_threshold_pct:
#             # Threshold reached, record the data and reset
#             self.price_volume_data.append((self.accumulated_volume, price_change_pct))
#             self.accumulated_volume = 0
#             self.last_price = new_price

#         # Compute average volume per percentage of price movement
#         if len(self.price_volume_data) > 0:
#             total_volume, total_price_change_pct = zip(*self.price_volume_data)
#             avg_volume_per_pct_price_movement = sum(total_volume) / sum(total_price_change_pct)
#         else:
#             avg_volume_per_pct_price_movement = 0

#         return avg_volume_per_pct_price_movement


##puvodni absolutni funkcni
    # def __init__(self, price_movement_threshold, track_mode='up', state=None):
    #     super().__init__(state)
    #     self.price_movement_threshold = price_movement_threshold
    #     self.track_mode = track_mode
    #     self.price_volume_data = deque()  # Stores tuples of (price, volume)
    #     self.last_price = None
    #     self.accumulated_volume = 0
    #     self.last_avg_volume_per_price_movement = 0

    # def next(self, close, volume):
    #     new_price = close[-1]
    #     new_volume = volume[-1]

    #     # Initialize last_price if not set
    #     if self.last_price is None:
    #         self.last_price = new_price

    #     # Accumulate volume
    #     self.accumulated_volume += new_volume

    #     # Calculate price change
    #     price_change = new_price - self.last_price

    #     # Check if the price movement threshold is reached
    #     reset_indicator = False
    #     if (self.track_mode == 'up' and price_change >= self.price_movement_threshold) or \
    #        (self.track_mode == 'down' and price_change <= -self.price_movement_threshold):
    #         self.price_volume_data.append((self.accumulated_volume, abs(price_change)))
    #         reset_indicator = True
    #     elif (self.track_mode == 'up' and price_change <= -self.price_movement_threshold) or \
    #          (self.track_mode == 'down' and price_change >= self.price_movement_threshold):
    #         reset_indicator = True

    #     # Reset if threshold is reached for either direction
    #     if reset_indicator:
    #         self.accumulated_volume = 0
    #         self.last_price = new_price
    #         if len(self.price_volume_data) > 0:
    #             print("pred resetem",self.price_volume_data)
    #             total_volume, total_price_change = zip(*self.price_volume_data)
    #             print("total volume, price change",total_volume,total_price_change)
    #             self.last_avg_volume_per_price_movement = sum(total_volume) / sum(total_price_change)

    #     return self.last_avg_volume_per_price_movement
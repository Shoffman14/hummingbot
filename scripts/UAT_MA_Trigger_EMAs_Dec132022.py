#######################################################################################################################
# Created on: 12/15/22
# Script:
# -When price falls below 200min EMA -> short_entry with TP at 1%
# -When price moves above 200min EMA -> long_entry with TP at 1%
# -Stop_Loss = 0.40% (rough estimate off one eyeball on LINKUSDT

#######################################################################################################################

from decimal import Decimal
from statistics import mean
from collections import deque
import logging

import pandas as pd
# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class EMATriggers(ScriptStrategyBase):

    markets = {
        "bybit_perpetual": {"LINK-USDT"}
    }
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    #: slow_ma is the 200min EMA
    de_slow_ma = deque([], maxlen=12000)
    #: testing -> putting into Pandas Dataframe instead of deque
    # de_slow_ma = pd.DataFrame([], maxlen=12000)
    multiplier = Decimal(0.000416631947337722)

    # value_today = p (the one I calculate in my code for each second, "tick"
    # -> Question: Is my interpretation of value_today correct? is my calc for it correct?
    # -> Update: value is the closing_price of the current period; so would be 'p' in this case
    # smoothing = 5 (manually set; I based off TradingView_Super_Guppy_configs
    # days (ticks in this case) = 12000 (equals the 'maxlen' setting for variable defined above)
    # ema_yesterday = ACTION -> how do I add like a "1-p" function? referring to
    # making a code to call or calc the previous period's price
    # smoothing = 5 (manually set; I based off TradingView_Super_Guppy_configs
    # days = 12000 (equals the 'maxlen' setting for variable defined above)

    def on_tick(self):
        #: at every tick, latest price will be returned
        p = self.connectors["bybit_perpetual"].get_price("LINK-USDT", True)
        print(p)
        #: with every tick, the new price of the trading pair_pair will be appended to the dque
        self.de_slow_ma.append(p)
        #: I think this calculates the SMA. I know it calculates the MA for my interval_range. Code taken from hb original script
        slow_ma = mean(self.de_slow_ma)
        print(slow_ma)
        #: calculating the EMA. The first EMA value is the previous SMA, so 'slow_ma' here
        #: EMA = Closing price * multiplier + EMA (previous day) * (1-multiplier)
        #: Multiplier = smoothing/(#_of_intervals + 1) ---> smoothing (manually chosen) = 5; #_of_intervals = 12000 (ticks from 'maxlen' above)
        first_part = p * self.multiplier
        print(first_part)
        second_part = slow_ma * (1-self.multiplier)
        print(second_part)
        # ema_current = (p*self.multiplier) + (slow_ma*(1-self.multiplier))   # <---CALCULATE THIS for time my bot was running and see if ema is correct
        # print(ema_current)  #: this was helpful
        ema_current = first_part + second_part
        print(ema_current)

        #: latest_test_note -> do I need to let script run for 12000 seconds (ticks) before comparing its 200_EMA to TradingView 200_EMA?
            #: if so, then I need to add a rule to my script saying not to take trades before 12000 seconds (ticks) have completed

        # #: logic for golden cross
        # if (p > ema_current) & (self.pingpong == 0):
        #     self.buy(
        #         connector_name="bybit_perpetual",
        #         trading_pair="LINK-USDT",
        #         amount=Decimal(1),
        #         order_type=OrderType.MARKET,
        #         price=p,
        #         position_action=PositionAction.OPEN
        #     )
        #     self.logger().info(f'{"1 LINK bought"}')
        #     self.pingpong = 1

        # #: logic for death cross
        # elif (p < ema_current) & (self.pingpong == 1):
        #     self.sell(
        #         connector_name="bybit_perpetual",
        #         trading_pair="LINK-USDT",
        #         amount=Decimal(1),
        #         order_type=OrderType.MARKET,
        #         price=p,
        #         position_action=PositionAction.OPEN
        #     )
        #     self.logger().info(f'{"1 LINK sold"}')
        #     self.pingpong = 0
        # else:
        #     self.logger().info(f'{"wait for a signal to be generated"}')
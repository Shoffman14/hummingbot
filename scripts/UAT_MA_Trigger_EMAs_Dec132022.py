#######################################################################################################################
# Created on: 12/13/22
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
    de_slow_ema = deque([], maxlen=12000)


    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("LINK-USDT", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and EMA will be calculated
        self.de_slow_ema.append(p)
        slow_ema = ewm(span=5, adjust=False).mean()

        #: logic for golden cross
        if (p > slow_ema) & (self.pingpong == 0):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="LINK-USDT",
                amount=Decimal(143),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"143 LINK bought"}') #[12/9/22]: 143 is ~ $1,000USDT worth
            self.pingpong = 1

        #: logic for death cross
        elif (p < slow_ema) & (self.pingpong == 1):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="LINK-USDT",
                amount=Decimal(143),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"143 LINK sold"}') #[12/9/22]: 143 is ~ $1,000USDT worth
            self.pingpong = 0
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
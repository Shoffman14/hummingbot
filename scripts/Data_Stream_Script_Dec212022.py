#######################################################################################################################
# Created on: 12/22/22
# Script:
# -Data stream for my tp_spread based on latest avg_entry_price and my tp_spread config

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

class DataStream_TP(ScriptStrategyBase):

    markets = {
        "bybit_perpetual": {"ETH-USDT"}
    }

    def on_tick(self):
        #: at every tick, latest price will be returned
        p = self.connectors["bybit_perpetual"].my_position("ETH-USDT", True)
        print(p)

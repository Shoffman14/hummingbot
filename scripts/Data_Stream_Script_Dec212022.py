#######################################################################################################################
# Created on: 12/22/22
# Script:
# -Data stream for my tp_spread based on latest avg_entry_price and my tp_spread config

#######################################################################################################################

from decimal import Decimal
from statistics import mean
from collections import deque
import logging

# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.in_flight_order import OrderState
# from hummingbot.connector.derivative.bybit_perpetual import bybit_perpetual_constants as CONSTANTS
import asyncio
from typing import List, Optional

from hummingbot.connector.derivative.bybit_perpetual import (
    bybit_perpetual_constants as CONSTANTS,
    bybit_perpetual_web_utils as web_utils,
)
from hummingbot.connector.derivative.bybit_perpetual.bybit_perpetual_auth import BybitPerpetualAuth
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest, WSResponse
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger

class DataStream_TP(ScriptStrategyBase):

    markets = {
        "bybit_perpetual": {"ETH-USDT"}
    }

    def on_tick(self):
        #: at every tick, my position price will be returned
        p = self.connectors["bybit_perpetual"].session_auth.my_position(symbol="ETHUSDT")
        print(p)

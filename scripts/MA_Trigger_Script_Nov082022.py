from decimal import Decimal
from statistics import mean
from collections import deque
import logging



# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class MATriggers(ScriptStrategyBase):

    # [11/08/22]: My attempt at creating a script that incorporates moving_average data as triggers for trades
    # Why?: To test if I can build a simple script for Bybit_Perpetual that is triggered by statistical/price action
        # data (MAs in this case)
    # This script leverages a lot of the code in my initial Bybit_Perpetual Script, 'Basic_Script_Nov082022.py'

    markets = {
        "bybit_perpetual": {"ETH-USDT"}
    }
    de_fast_ma = deque([], maxlen=5)
    de_slow_ma = deque([], maxlen=20)

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        #: logic for golden cross
        if (fast_ma > slow_ma):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.01),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"0.01 ETH bought"}')

        #: logic for death cross
        elif (slow_ma > fast_ma):
            self.sell(
                onnector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.01),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"0.01 ETH sold"}')
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
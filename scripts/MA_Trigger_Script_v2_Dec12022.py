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


    markets = {
        "bybit_perpetual": {"BTC-USDT"}
    }
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    de_fast_ma = deque([], maxlen=5)
    de_slow_ma = deque([], maxlen=20)

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("BTC-USDT", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        #: logic for golden cross
        if (fast_ma > slow_ma) & (self.pingpong == 0):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="BTC-USDT",
                amount=Decimal(0.01),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"0.01 BTC bought"}')
            self.pingpong = 1

        #: logic for death cross
        elif (slow_ma > fast_ma) & (self.pingpong == 1):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="BTC-USDT",
                amount=Decimal(0.01),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.CLOSE
            )
            self.logger().info(f'{"0.01 BTC sold"}')
            self.pingpong = 0
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
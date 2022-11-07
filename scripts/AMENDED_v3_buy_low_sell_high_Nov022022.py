

from collections import deque
from decimal import Decimal
from statistics import mean

from hummingbot.core.data_type.common import OrderType
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class AMENDEDbuyLowSellHigh(ScriptStrategyBase):
    markets = {"bybit_perpetual": {"ETH-USDT"}}
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0

    """
    for the sake of simplicity in testing, we will define fast MA as the 5-secondly-MA, and slow MA as the
    20-secondly-MA. User can change this as desired
    """

# [11/3/22]: Changed titles for each and added a third timeframe
# PENDING: These should reflect Exponential Moving Average (EMA) once I incorporate those calcs
    de_fast_ma = deque([], maxlen=5)
    # de_medium_ma = deque([], maxlen=50)
    de_slow_ma = deque([], maxlen=20)

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)

        #: with every tick, the new price of the trading_pair will be appended to the deque and MA will be calculated
        self.de_fast_ma.append(p)
        # self.de_medium_ma.append(p)  # [11/3/22]: Added 'medium' timeframe
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        # medium_ma = mean(self.de_medium_ma)  # [11/3/22]: Added 'medium' timeframe
        slow_ma = mean(self.de_slow_ma)


        if (fast_ma > slow_ma) & (self.pingpong == 0):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET
            )
            self.logger().info(f'{"0.1 ETH bought"}')
            self.pingpong = 1


        #: logic for death cross
        elif (slow_ma > fast_ma) & (self.pingpong == 1):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
            )
            self.logger().info(f'{"0.1 ETH sold"}')
            self.pingpong = 0

        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
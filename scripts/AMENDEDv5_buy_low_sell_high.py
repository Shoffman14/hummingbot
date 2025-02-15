

from collections import deque
from decimal import Decimal
from statistics import mean

from hummingbot.core.data_type.common import OrderType, PositionAction
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

s_decimal_nan = Decimal("NaN")



class buyLowSellHigh(ScriptStrategyBase):
    markets = {"bybit_perpetual": {"ETH-USDT"}}
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0

    """
    for the sake of simplicity in testing, we will define fast MA as the 5-secondly-MA, and slow MA as the
    20-secondly-MA. User can change this as desired
    """

    de_fast_ma = deque([], maxlen=5)
    de_slow_ma = deque([], maxlen=20)

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)

        #: with every tick, the new price of the trading_pair will be appended to the deque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        #: logic for golden cross
        if (fast_ma > slow_ma) & (self.pingpong == 0):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=s_decimal_nan,
                position_action=PositionAction.OPEN,
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
                price=s_decimal_nan,
                position_action=PositionAction.OPEN,
            )
            self.logger().info(f'{"0.01 ETH sold"}')
            self.pingpong = 0

        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
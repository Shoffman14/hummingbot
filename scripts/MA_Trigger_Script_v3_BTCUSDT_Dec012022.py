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
    de_slow_ma = deque([], maxlen=60) # [12/1/22 10:11 PM EST / 12/2/22 UTC): Increase from 20
    # official_change_long of 'de_slow-_ma' :
    # 1) 20 (original)
    # 2) 60
    # Try increasing 'de_fast_ma' too; try proportionally (like what their ratio is)
        # Why? Having only increase 'de_slow_ma', there looks to be a chance that any fake_pumps can catch it. TBC on
        #   current VWAP observation though (it's still playing out)

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
                amount=Decimal(0.06),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"0.06 BTC bought"}')
            self.pingpong = 1

        #: logic for death cross
        elif (slow_ma > fast_ma) & (self.pingpong == 1):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="BTC-USDT",
                amount=Decimal(0.06),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.CLOSE
            )
            self.logger().info(f'{"0.06 BTC sold"}')
            self.pingpong = 0
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
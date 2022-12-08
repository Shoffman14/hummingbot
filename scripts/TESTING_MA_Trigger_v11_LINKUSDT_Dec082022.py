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
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    de_fast_ma = deque([], maxlen=1200)
    de_slow_ma = deque([], maxlen=12000)
    order_amount_usd = Decimal(1000)    # each order should be ~$1,000
    base = "LINK"
    quote = "USDT"

    markets = {
        "bybit_perpetual": {f"{base}-{quote}"}
    }

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("LINK-USDT", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        #: logic for bullish cross
        if (fast_ma > slow_ma) & (self.pingpong == 0):
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            price = self.connectors["bybit_perpetual"].get_mid_price(f"{self.base}-{self.quote}") * Decimal(0.99)
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="LINK-USDT",
                amount=amount,
                order_type=OrderType.MARKET,
                price=price,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f"{self.amount}-LINK bought") #[12/7/22]: calculated amount should populate
            self.pingpong = 1

        #: logic for bearish cross
        elif (slow_ma > fast_ma) & (self.pingpong == 1):
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            price = self.connectors["bybit_perpetual"].get_mid_price(f"{self.base}-{self.quote}") * Decimal(0.99)
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="LINK-USDT",
                amount=amount,
                order_type=OrderType.MARKET,
                price=price,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f"{self.amount}-LINK sold")  # [12/7/22]: calculated amount should populate
            self.pingpong = 0
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
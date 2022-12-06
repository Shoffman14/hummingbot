from decimal import Decimal
from statistics import mean
from collections import deque
import logging



# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionSide
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class UATMATriggers(ScriptStrategyBase):

    connector_name = "bybit_perpetual"
    trading_pair = "ETH-USDT"
    # markets = {
    #     "bybit_perpetual": {"ETH-USDT"}
    # }
    take_profit = Decimal(0.30)
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    de_fast_ma = deque([], maxlen=1200)
    de_slow_ma = deque([], maxlen=12000)

    markets = {connector_name: {trading_pair}}



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
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN,
                position_side=PositionSide.LONG
            )
            self.logger().info(f'{"0.1 ETH bought"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 1

        #: logic for death cross
        elif (slow_ma > fast_ma):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN,
                position_side=PositionSide.SHORT
            )
            self.logger().info(f'{"0.1 ETH sold"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 2
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')

    def control_take_profit(self):
        if not self._take_profit_order:
            entry_price = self.open_order.order.average_executed_price
            if self._signal.position_config.side == PositionSide.LONG:
                tp_multiplier = 1 + self._signal.position_config.take_profit
            else:
                tp_multiplier = 1 - self._signal.position_config.take_profit
            order_id = self._strategy.place_order(
                connector_name=self._signal.exchange,
                trading_pair=self._signal.trading_pair,
                amount=self.open_order.order.executed_amount_base,
                price=entry_price * tp_multiplier,
                order_type=OrderType.LIMIT,
                position_action=PositionAction.CLOSE,
                position_side=PositionSide.LONG if self._signal.position_config.side == PositionSide.SHORT else PositionSide.SHORT
            )
            self._take_profit_order = TrackedOrder(order_id)
            self._strategy.logger().info(f"Signal id {self._signal.id}: Placing take profit")


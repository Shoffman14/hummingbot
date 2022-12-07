from decimal import Decimal
from statistics import mean
from collections import deque
import logging



# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionSide
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.order_candidate import OrderCandidate

class UATMATriggers(ScriptStrategyBase):

    connector_name = "bybit_perpetual"
    trading_pair = "ETH-USDT"
    # markets = {
    #     "bybit_perpetual": {"ETH-USDT"}
    # }
    take_profit = Decimal(0.30)
    # open_order = define open_order <---PENDING
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    de_fast_ma = deque([], maxlen=20) # changed to 20, from 1200, for quicker testing
    de_slow_ma = deque([], maxlen=60)    # changed to 60, from 12000, for quicker testing

    markets = {connector_name: {trading_pair}}


    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
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
                price=p,
                position_action=PositionAction.OPEN,
            )
            self.logger().info(f'{"0.1 ETH bought"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 1

        #: logic for death cross
        # elif (slow_ma > fast_ma) & (self.pingpong == 1):
        if (slow_ma > fast_ma) & (self.pingpong == 1):
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN,
            )
            self.logger().info(f'{"0.1 ETH sold"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 0

        proposal: List(OrderCandidate) = []
        if self.pingpong == 1:
            proposal.append(self.create_take_profit_order())
        if self.pingpong == 0:
            proposal.append(self.create_take_profit_order())

        else:
            self.logger().info(f'{"wait for a signal to be generated"}')

    def create_take_profit_order(self):
        entry_price_long = self.buy.order.average_executed_price
        entry_price_short = self.sell.order.average_executred_price
        if self.pingpong == 1:
            tp_multiplier_long = 1 + self.take_profit
            self.sell(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.LIMIT,
                price=entry_price_long * tp_multiplier_long,
                position_action=PositionAction.CLOSE,
            )
            self.logger().info(f'{"ETH_Long_TP_Filled"}')
        else:
            tp_multiplier_short = 1 - self.take_profit
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.LIMIT,
                price=entry_price_short * tp_multiplier_short,
                position_action=PositionAction.CLOSE,
            )
            self.logger().info(f'{"ETH_Short_TP_Filled"}')


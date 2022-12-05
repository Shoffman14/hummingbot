# UAT Notes / To-Do:
# My close_position parameter shouldn't be the fast ma falling back below the slow_ma b/c this wipes out the entire
# profit by holding the trade all the way up and all the way down. When I looked at a chart of this it was immediately
# obvious, so the error/bug was caused more by rushing/lack of research.
# Ways to fix -> create a TP variable, to TP after a certain % increase




from decimal import Decimal
from statistics import mean
from collections import deque
import logging



from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType, PositionAction, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.core.event.events import (
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    MarketOrderFailureEvent,
    SellOrderCompletedEvent,
    SellOrderCreatedEvent,
    OrderFilledEvent,
)
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase, Decimal, OrderType
# from hummingbot.core.data_type.order_book import MarketOrder, PositionEntryPrice # <-- added from OpenAI search; not tested

class MATriggersv2(ScriptStrategyBase):


    order_amount_usd = Decimal(100)
    long_take_profit_spread = Decimal(0.30)
    short_take_profit_spread = Decimal(0.30)
    entry_price = Decimal("0")
    trading_pair: dict = {}
    base = "ETH"
    quote = "USDT"
    markets = {
        "bybit_perpetual": {f"{base}-{quote}"}
    }
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0
    de_fast_ma = deque([], maxlen=1200)
    de_slow_ma = deque([], maxlen=12000)


    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)
        entry_price = self.connectors["bybit_perpetual"].get_entry_price(f"{self.base}-{self.quote}")

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        #: logic for bullish crossover
        if (fast_ma > slow_ma) & (self.pingpong == 0):
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            self.buy(
                connector_name=self.connectors,
                trading_pair=self.trading_pair,
                amount=amount,
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"ETH Bought"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 1


        #: logic for death cross
        elif (slow_ma > fast_ma) & (self.pingpong == 0):  # changed to 0 so that it only fires when there isn't an active order open
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            self.sell(
                connector_name=self.connectors,
                trading_pair=self.trading_pair,
                amount=amount,
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"19666 DOGE sold"}') #[12/3/22]: 19666 is ~ $2,000USDT worth
            self.pingpong = 1  # changed to 1 so that it only fires when there isn't an active order open
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')


    def calculate_profit(self):
        # logic for calculating & placing a TP order if there is an active long open
        if self.pingpong == 1 & position_profit_spread < long_take_profit_spread:
            position_profit_spread = (long_take_profit_spread - self.p)/(self.p)
            long_tp_calc = self.entry_price * long_take_profit_spread
            long_tp_price = self.entry_price + long_tp_calc
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            self.sell(
                connector_name=self.connectors,
                trading_pair=self.trading_pair,
                amount=amount,
                order_type=OrderType.LIMIT,
                price=long_tp_price,
                position_action=PositionAction.CLOSE
            )

        # logic for calculating & placing a TP order if there is an active short open
        if self.pingpong == 0 & position_profit_spread < short_take_profit_spread:
            position_profit_spread = (short_take_profit_spread - self.p)/(self.p)
            short_tp_calc = self.entry_price * short_take_profit_spread
            short_tp_price = self.entry_rpice + short_tp_calc
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USD")
            amount = self.order_amount_usd / conversion_rate
            self.buy(
                connector_name=self.connectors,
                trading_pair=self.trading_pair,
                amount=amount,
                order_type=OrderType.LIMIT,
                price=short_tp_price,
                position_action=PositionAction.CLOSE
            )

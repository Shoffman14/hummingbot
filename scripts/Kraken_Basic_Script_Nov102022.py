from decimal import Decimal

from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType  # Removed 'PositionAction' since this isn't for a perp market
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class SimpleBuy(ScriptStrategyBase):

    # [11/10/22]: My attempt at creating a basic script for Kraken to buy_orders only
    # Why?: The point of this exercise to confirm I can at least build a basic script for Kraken connector
    # This script leverages most of the code in Bybit_Perpetual script 'Basic_Script_Nov072022.py"
    # This script leverages a lot of the code in script: ;buy_only_three_times_example.py;

    order_amount_usd = Decimal(10)
    orders_created = 0
    orders_to_create = 3
    base = "ETH"
    quote = "USDT"
    markets = {
        "kraken": {f"{base}-{quote}"}
    }

    def on_tick(self):
        if self.orders_created < self.orders_to_create:
            conversion_rate = RateOracle.get_instance().get_pair_rate(f"{self.base}-USDT")
            amount = self.order_amount_usd / conversion_rate
            price = self.connectors["kraken"].get_mid_price(f"{self.base}-{self.quote}") * Decimal(0.99)
            self.buy(
                connector_name="kraken",
                trading_pair="ETH-USDT",
                amount=amount,
                order_type=OrderType.LIMIT,
                price=price
                # position_action=PositionAction.OPEN
            )

    def did_create_buy_order(self, event: BuyOrderCreatedEvent):
        trading_pair = f"{self.base}-{self.quote}"
        if event.trading_pair == trading_pair:
            self.orders_created += 1
            if self.orders_created == self.orders_to_create:
                self.logger().info("All orders created !")
                HummingbotApplication.main_application().stop()
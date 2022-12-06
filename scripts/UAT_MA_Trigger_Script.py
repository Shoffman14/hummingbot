import logging

from hummingbot.core.event.events import (
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    MarketOrderFailureEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
    SellOrderCompletedEvent,
    SellOrderCreatedEvent,
)
from hummingbot.strategy.script_strategy_base import Decimal, OrderType, ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType, PositionAction
from hummingbot.core.data_type.order_candidate import OrderCandidate

class UATMATriggers(ScriptStrategyBase):
    markets = {"binance_paper_trade": {"ETH-USDT"}}
    pingpong = 0
    long_profit_taking_spread = Decmimal(0.30)
    short_profit_taking_spread = Decimal(0.30)
    de_fast_ma = deque([], maxlen=1200)
    de_slow_ma = deque([], maxlen=12000)

    def on_tick(self):
        p = self.connectors["binance_paper_trade"].get_price("ETH-USDT", True)
        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        slow_ma = mean(self.de_slow_ma)

        # logic for bullish cross
        if (fast_ma > slow_ma) & (self.pingpong == 0):
            self.buy(
                connector_name="binance_paper_trade",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=p,
                position_aciton=PositionAction.OPEN
            )
            self.logger().info(f'{"0.1 ETH bought"}')
            self.pingpong = 1

        # logic for bearish cross
        elif (slow_ma > fast_ma) & (self.pingpong == 0):
            self.sell(
                connector_name="binance_paper_trade",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET,
                price=p,
                position_action=PositionAction.OPEN
            )
            self.logger().info(f'{"0.1 ETH sold"}')
            self.pingpong = 2

        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
            # proposal: List[OrderCandidate] = self.create_proposal()

    def profit_taking_proposal(self, active_positions: List) -> Proposal:

        market: DerivativeBase = self._market_info.market
        unwanted_exit_orders = [o for o in self.active_orders
                                if o.client_order_id not in self._exit_orders.keys()]
        ask_price = market.get_price(self.trading_pair, True)
        bid_price = market.get_price(self.trading_pair, False)
        buys = []
        sells = []

        if mode == PositionMode.ONEWAY:
            # in one-way mode, only one active position is expected per time
            if len(active_positions) > 1:
                self.logger().error(f"More than one open position in {mode.name} position mode. "
                                    "Kindly ensure you do not interact with the exchange through "
                                    "other platforms and restart this strategy.")
            else:
                # Cancel open order that could potentially close position before reaching take_profit_limit
                for order in unwanted_exit_orders:
                    if ((active_positions[0].amount < 0 and order.is_buy)
                            or (active_positions[0].amount > 0 and not order.is_buy)):
                        self.cancel_order(self._market_info, order.client_order_id)
                        self.logger().info(f"Initiated cancelation of {'buy' if order.is_buy else 'sell'} order "
                                           f"{order.client_order_id} in favour of take profit order.")

        for position in active_positions:
            if (ask_price > position.entry_price and position.amount > 0) or (
                    bid_price < position.entry_price and position.amount < 0):
                # check if there is an active order to take profit, and create if none exists
                profit_spread = self._long_profit_taking_spread if position.amount > 0 else self._short_profit_taking_spread
                take_profit_price = position.entry_price * (Decimal("1") + profit_spread) if position.amount > 0 \
                    else position.entry_price * (Decimal("1") - profit_spread)
                price = market.quantize_order_price(self.trading_pair, take_profit_price)
                size = market.quantize_order_amount(self.trading_pair, abs(position.amount))
                old_exit_orders = [
                    o for o in self.active_orders
                    if ((o.price != price or o.quantity != size)
                        and o.client_order_id in self._exit_orders.keys()
                        and ((position.amount < 0 and o.is_buy) or (position.amount > 0 and not o.is_buy)))]
                for old_order in old_exit_orders:
                    self.cancel_order(self._market_info, old_order.client_order_id)
                    self.logger().info(
                        f"Initiated cancelation of previous take profit order {old_order.client_order_id} in favour of new take profit order.")
                exit_order_exists = [o for o in self.active_orders if o.price == price]
                if len(exit_order_exists) == 0:
                    if size > 0 and price > 0:
                        if position.amount < 0:
                            buys.append(PriceSize(price, size))
                        else:
                            sells.append(PriceSize(price, size))
        return Proposal(buys, sells)






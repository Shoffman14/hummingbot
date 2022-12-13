import logging
from decimal import Decimal
from typing import List

from hummingbot.core.data_type.common import OrderType, PriceType, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.core.event.events import OrderFilledEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class SimplePMM(ScriptStrategyBase):
    bid_spread = 0.08
    ask_spread = 0.08
    order_refresh_time = 15
    order_amount = 0.006
    create_timestamp = 0
    trading_pair = "BTC-USDT"
    exchange = "bybit_perpetual"
    # Here you can use for example the LastTrade price to use in your strategy
    price_source = PriceType.MidPrice

    markets = {exchange: {trading_pair}}

    def on_tick(self):
        if self.create_timestamp <= self.current_timestamp:
            self.cancel_all_orders()
            proposal: List[OrderCandidate] = self.create_proposal()
            proposal_adjusted: List[OrderCandidate] = self.adjust_proposal_to_budget(proposal)
            self.place_orders(proposal_adjusted)
            self.create_timestamp = self.order_refresh_time + self.current_timestamp

    def create_proposal(self) -> List[OrderCandidate]:
        ref_price = self.connectors[self.exchange].get_price_by_type(self.trading_pair, self.price_source)
        buy_price = ref_price * Decimal(1 - self.bid_spread)
        sell_price = ref_price * Decimal(1 + self.ask_spread)

        buy_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                   order_side=TradeType.BUY, amount=Decimal(self.order_amount), price=buy_price)

        sell_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                    order_side=TradeType.SELL, amount=Decimal(self.order_amount), price=sell_price)

        return [buy_order, sell_order]

    def adjust_proposal_to_budget(self, proposal: List[OrderCandidate]) -> List[OrderCandidate]:
        proposal_adjusted = self.connectors[self.exchange].budget_checker.adjust_candidates(proposal, all_or_none=True)
        return proposal_adjusted

    #: code from HB team member: fede (pasted from Discord)
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

    def place_orders(self, proposal: List[OrderCandidate]) -> None:
        for order in proposal:
            self.place_order(connector_name=self.exchange, order=order)

    def place_order(self, connector_name: str, order: OrderCandidate):
        if order.order_side == TradeType.SELL:
            self.sell(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
                      order_type=order.order_type, price=order.price)
        elif order.order_side == TradeType.BUY:
            self.buy(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
                     order_type=order.order_type, price=order.price)

    def cancel_all_orders(self):
        for order in self.get_active_orders(connector_name=self.exchange):
            self.cancel(self.exchange, order.trading_pair, order.client_order_id)

    def did_fill_order(self, event: OrderFilledEvent):
        msg = (f"{event.trade_type.name} {round(event.amount, 2)} {event.trading_pair} {self.exchange} at {round(event.price, 2)}")
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)
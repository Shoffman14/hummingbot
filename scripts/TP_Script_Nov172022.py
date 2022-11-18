# # [11/17/22]: This code is based off hummingbot script 'simple_pmm_example
# # 1) Build a TP_reduce_order that is can be both: adjusting (by calcs) + static but refreshing every 5sec or so
#
# # As of 10:56 PM EST 11/17/22 EST: I have not tested this script; so 1) Test then 2) Change for my TP_order code
#
#
# from decimal import Decimal
# # from statistics import mean
# # from collections import deque
# import logging
# from typing import List
#
#
#
# from hummingbot.core.data_type.common import OrderType, PriceType, TraderType, PositionAction
# from hummingbot.core.data_type_order_candidate import OrderCandidate
# from hummingbot.core.event.events import OrderFilledEvent
# from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
#
#
# class SimplePMM(ScriptStrategyBase):
#     # orders_to_cancel = 1
#     order_refresh_time = 5
#     long_take_profit_spread = 0.60
#     short_take_profit_spread = 0.60
#     exchange = "bybit_perpetual"
#     trading_pair = "ETH-USDT"
#     create_timestamp = 0
#     # Here you can use for example the LasTrade price to use in your strategy
#     price_source = PriceType.MidPrice
#
#     markets = {"exchange": {"trading_pair"}}
#
#     def on_tick(self):
#         if self.create_timestamp <= self.current_timestamp:
#             self.cancel_all_orders()
#             proposal: List[OrderCandidate] = self.create_proposal()
#             proposal_adjusted: List[OrderCandidate] = self.adjust_proposal_to_budget(proposal)
#             self.place_orders(proposal_adjusted)
#             self.create_timestamp = self.order_refresh_time + self.current_timestamp
#
#     def create_proposal(self): -> List[OrderCandidate]:
#         ref_price = self.connectors[self.exchange].get_price_by_type(self.trading_pair, self.price_source)
#         for position in active_positions:
#             if (ask_price > position.entry_price and position.amount > 0) or (
#                 bid_price < position.entry_price and position.amount < 0):
#             # Check if there is an active order to take profit, and then create if none exists
#             profit_spread = self.long_take_profit_spread if position.amount > 0 else self.short_take_profit_spread
#             take_profit_price = position.entry_price * (Decimal("1") + profit_spread) if position.amount > 0 \
#                 else position.entry_price * (Decimal("1") - profit_spread)
#             price = market.quantize_order_price(self.trading_pair, take_profit_price)
#             size = market.quantize_order_amount(self.trading_pair, abs(position.amount))
#
#         # buy_price = ref_price * Decimal(1 - self.bid_spread)
#         long_TP = ref_price * Decimal(1 - long_take_profit_spread)
#         # sell_price = ref_price * Decimal(1 + self.ask_spread)
#         sell_TP = ref_price * Decimal(1 - short_take_profit_spread)
#
#         long_TP_reduce_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
#                                    order_side=TradeType.SELL, amount=Decimal(self.order_amount), price=long_TP, position_action=PositionAction.CLOSE)
#         sell_TP_reduce_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
#                                     order_side=TradeType.BUY, amount=Decimal(self.order_amount), price=sell_TP, position_action=PositionAction.CLOSE)
#
#         return [long_TP_reduce_order, sell_TP_reduce_order]
#
#     def adjust_proposal_to_budget(self, proposal: List[OrderCandidate]) -> List[OrderCandidate]:
#         proposal_adjusted = self.connectors[self.exchange].budget_checker.adjust_candidate(proposal, all_or_none=True)
#         return proposal_adjusted
#
#     def place_orders(self, proposal: List[OrderCandidate]) -> None:
#         for order in proposal:
#             self.place_order(connector_name=self.exchange, order=order)
#
#     def place_order(self, connector_name: str, order: OrderCandidate):
#         if order.order_side == TradeType.SELL:
#             self.sell(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
#                       order_type=order.order_type, price=order.price, position_action=order.position_action)
#         elif order.order_side == TradeTypeBUY:
#             self.buy(connector_name=connector_name, trading_pair=order.trading_pair, amount=order.amount,
#                      order_type=order.order_type, price=order.price, position_action=order.position_action)
#
#     def cancel_all_orders(self):
#         for order in self.get_active_orders(connector_name=self.exchange):
#             self.cancel(self.exchange, order.trading_pair, order.client_order_id)
#
#     def did_fill_order(self, event: OrderFilledEvent):
#         msg = (f"{event.trade_type.name} {round(event.amount, 2)} {event.trading_pair} {self.exchange} at {round(event.price, 2)}")
#         self.log_with_clock(logging.INFO, msg)
#         self.notify_hb_api_with_timestamp(msg)

# [11/18/22]: Script code from Github pasted to test run in bybit_perpetual; I want to do this before making further
    # customization changes to this script's code which I'm leveraging for my TP_Script

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
    order_amount = 0.01
    create_timestamp = 0
    trading_pair = "ETH-USDT"
    exchange = "binance_paper_trade"
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





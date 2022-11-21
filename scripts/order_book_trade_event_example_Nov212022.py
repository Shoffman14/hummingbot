from hummingbot.core.data_type.composite_order_book import CompositeOrderBook
from hummingbot.core.event.event_forwarder import SourceInfoEventForwarder
from hummingbot.core.event.events import OrderBookEvent, OrderBookTradeEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class OrderBookTradeEvents(ScriptStrategyBase):
    markets = {'bybit_perpetual': {'ETH-USDT'}}
    order_book_event_initialized = False

    def on_tick(self):
        if not self.order_book_event_initialized:
            self.register_order_book_trades_events()

    def register_order_book_trades_events(self):
        self.order_book_trade_event = SourceInfoEventForwarder(self._process_public_trade)
        for market in self.connectors.values():
            for order_book in market.order_books.values():
                order_book.add_listener(OrderBookEvent.TradeEvent, self.order_book_trade_event)
        self.order_book_event_initialized = True

    def _process_public_trade(self,
                              event_tag: int,
                              order_book: CompositeOrderBook,
                              event: OrderBookTradeEvent):
        self.logger().info(f"Trading Pair: {event.trading_pair}| P: {event.price}| A: {event.amount}")
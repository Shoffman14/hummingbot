from decimal import Decimal
from statistics import mean
from collections import deque
import logging



# from hummingbot.client.hummingbot_application import HummingbotApplication
from hummingbot.core.data_type.common import OrderType      # Removed 'PositionAction' from this line b/c this is for spot market
from hummingbot.core.event.events import BuyOrderCreatedEvent
from hummingbot.core.rate_oracle.rate_oracle import RateOracle
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class MATriggers(ScriptStrategyBase):


    markets = {
        "kraken": {"ETH-USD"}
    }
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0  #: removed for current script since only for long_entry
    #: [12/12/22]: Updating script with idea from today, 12/12/22. Corresponds to my idea notes on TradingView
        # 1min charts too. Out of 3 markets (ETHUSDT, DOGEUSDT, LINKUSDT), this strategy was visibly "strongest"
        # for DOGEUSDT and ETHUSDT
    de_20_ma = deque([], maxlen=1200)
    de_50_ma = deque([], maxlen=3000)
    de_100_ma = deque([], maxlen=6000)
    de_200_ma = deque([], maxlen=12000)
    de_400_ma = deque([], maxlen=24000)
    de_1000_ma = deque([], maxlen=60000)


    def on_tick(self):
        p = self.connectors["kraken"].get_price("ETH-USD", True)

        #: with every tick, the new price of the trading pair_pair will be appended to the dque and MA will be calculated
        self.de_20_ma.append(p)
        self.de_50_ma.append(p)
        self.de_100_ma.append(p)
        self.de_200_ma.append(p)
        self.de_400_ma.append(p)
        self.de_1000_ma.append(p)
        ma_20 = mean(self.de_20_ma)
        ma_50 = mean(self.de_50_ma)
        ma_100 = mean(self.de_100_ma)
        ma_200 = mean(self.de_200_ma)
        ma_400 = mean(self.de_400_ma)
        ma_1000 = mean(self.de_1000_ma)


        #: logic for long -> start entry when ALL MAs are "under" de_1000_ma
        #: I added the 'pingpong' parameters + criteria back b/c without it I think the script will keep buying every
            # 1-2 seconds as long as ma_1000 is < all other MAs
        #: Future enhancement for this -> TWAP buy for specified time or volume paramter once ma_1000 is < all other MAs
        if (ma_1000 < ma_400) & (ma_1000 < ma_200) & (ma_1000 < ma_100) & (ma_1000 < ma_50) & (ma_1000 < ma_20) \
                & (pingpong == 0):
            self.buy(
                connector_name="kraken",
                trading_pair="ETH-USD",
                amount=Decimal(0.08),   # Increase amount; small b/c not much USD on Kraken today (12/12/22)
                order_type=OrderType.MARKET,
                price=p
            )
            self.logger().info(f'{"0.08 ETH bought"}') #[12/12/22]: 0.08 is ~ $100 USDT worth
            self.pingpong = 1

        #: if I wanted to make the script for long_entry only
        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
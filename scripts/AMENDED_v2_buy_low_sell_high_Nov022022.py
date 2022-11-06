

# [11/02/22]: The purpose of this file is for scratch-work creating new Script files for my HB repository
    # PROD-ready scripts will be added directly into Github, and pasted from here (ie: not running from PyCharm)

# [11/03/22]: Strategy Idea -> 20, 50, 100 interval EMAs crossover on 1min timeframe (chart). Specifically, when 20 crosses (& closes) above 50,
    # after being below 50 and 200 lines
    # Target TP area could be based on when 20 is back above 50 & 100 lines (ie: 20 is above 50 which is above 100)
    # I'm currently looking at 100SHIBUSDTPERP (Binance) for initial research. Insufficient liquidity of SHIB/USDT pair
        # on Bybit is first concern that comes to mind
    # Any strategy should have a Stop_Loss to act as "invalidation" of the signal for that particular setup
    # For my v1 of this strategy I'm only going to enter into long positions, and use what would be short_entry signals
        # as, roughly, Long_TP signals

# Outstanding:
    # Add TP for longs (there are 2 separate buy signals in my code below)
    # Add Stop Loss for longs (for both entries)
    # Decrease buy amounts before testing; then increase back to higher levels (0.5; 1.0)

from collections import deque
from decimal import Decimal
from statistics import mean

from hummingbot.core.data_type.common import OrderType
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

# PENDING: Change 'buyLowSellHigh' to 'buyLowSellHighEMEA' to differentiate this script from original version
class buyLowSellHigh(ScriptStrategyBase):
    # long_profit_taking_spread = 0.30,  # [11/3/22]: Added long_TP parameter -> not sure if this will work w/o additional code
    markets = {"bybit_perpetual": {"ETH-USDT"}}
    #: pingpong is a variable to allow alternating between buy & sell signals
    pingpong = 0

    """
    for the sake of simplicity in testing, we will define fast MA as the 5-secondly-MA, and slow MA as the
    20-secondly-MA. User can change this as desired
    """

# [11/3/22]: Changed titles for each and added a third timeframe
# PENDING: These should reflect Exponential Moving Average (EMA) once I incorporate those calcs
    de_fast_ma = deque([], maxlen=20)
    de_medium_ma = deque([], maxlen=50)
    de_slow_ma = deque([], maxlen=200)

    def on_tick(self):
        p = self.connectors["bybit_perpetual"].get_price("ETH-USDT", True)

        #: with every tick, the new price of the trading_pair will be appended to the deque and MA will be calculated
        self.de_fast_ma.append(p)
        self.de_medium_ma.append(p)  # [11/3/22]: Added 'medium' timeframe
        self.de_slow_ma.append(p)
        fast_ma = mean(self.de_fast_ma)
        medium_ma = mean(self.de_medium_ma)  # [11/3/22]: Added 'medium' timeframe
        slow_ma = mean(self.de_slow_ma)

        # [11/3/22]: Logic for 1st bullish cross (20 crosses above 50)
        if (fast_ma > medium_ma) & (self.pingpong == 0):
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.1),
                order_type=OrderType.MARKET
                # long_profit_taking_spread=0.30  # [11/3/22]: Adding my Long_TP parameter from above; not sure if will work w/o additional code
            )
            self.logger().info(f'{"0.1 ETH bought"}')
            self.pingpong = 1

        # [11/3/22]: Logic for 2nd bullish cross (20 crosses above 200; so 50 now above 200 too)
        elif (fast_ma > slow_ma) & (self.pingpong == 0):  # [11/3/22]: I changed this to 'elif' since I added second buy signal
            self.buy(
                connector_name="bybit_perpetual",
                trading_pair="ETH-USDT",
                amount=Decimal(0.2),
                order_type=OrderType.MARKET
                # long_profit_taking_spread=0.30  # [11/3/22]: Adding my Long_TP parameter from above; not sure if will work w/o additional code
            )
            self.logger().info(f'{"0.2 ETH bought"}')
            self.pingpong = 1

        # #: logic for death cross
        # elif (slow_ma > fast_ma) & (self.pingpong == 1):
        #     self.sell(
        #         connector_name="bybit_perpetual",
        #         trading_pair="ETH-USDT",
        #         amount=Decimal(0.01),
        #         order_type=OrderType.MARKET,
        #     )
        #     self.logger().info(f'{"0.01 ETH sold"}')
        #     self.pingpong = 0

        else:
            self.logger().info(f'{"wait for a signal to be generated"}')
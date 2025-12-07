from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AlpacaExecutor:
    def __init__(self):
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found in .env")
            
        self.client = TradingClient(self.api_key, self.secret_key, paper=True)
        
    def check_connection(self):
        try:
            account = self.client.get_account()
            if account.status == 'ACTIVE':
                logger.info(f"Connected to Alpaca. Account Status: {account.status}, Cash: ${account.cash}")
                return True
            else:
                logger.error(f"Account not active. Status: {account.status}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            return False

    def submit_order(self, symbol: str, side: str, qty: float, order_type: str = 'market', limit_price: float = None):
        """
        Submits an order to Alpaca.
        side: 'buy' or 'sell'
        qty: amount
        order_type: 'market' or 'limit'
        limit_price: required if order_type is 'limit'
        """
        try:
            from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
            
            side_enum = OrderSide.BUY if side == 'buy' else OrderSide.SELL
            
            if order_type == 'limit':
                if limit_price is None:
                    raise ValueError("limit_price must be provided for limit orders.")
                
                req = LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    type='limit',
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
            else:
                 req = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    type='market',
                    time_in_force=TimeInForce.DAY
                )
            
            order = self.client.submit_order(req)
            logger.info(f"Submitted {order_type} {side} order for {qty} {symbol} at {limit_price if limit_price else 'MKT'}. ID: {order.id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            return None

    def get_positions(self):
        try:
            return self.client.get_all_positions()
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []

if __name__ == "__main__":
    # Smoke Test
    logging.basicConfig(level=logging.INFO)
    try:
        trader = AlpacaExecutor()
        trader.check_connection()
    except Exception as e:
        print(f"Error: {e}")

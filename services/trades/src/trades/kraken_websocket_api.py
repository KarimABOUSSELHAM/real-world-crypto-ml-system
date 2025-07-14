import json
from typing import List

from loguru import logger
from trade import Trade
from websocket import create_connection


class KrakenWebsocketAPI:
    URL = 'wss://ws.kraken.com/v2'

    def __init__(
        self,
        product_ids: List[str],
    ):
        self.product_ids = product_ids
        # create a websocket client
        self._ws_client = create_connection(self.URL)

        # subscribe to the websocket
        self._subscribe(self.product_ids)

    def _subscribe(self, product_ids: List[str]):
        """
        Subscribes to the websocket and waits for the initial snapshot for the given `product_ids`.
        """
        # send a subscribe message to the websocket
        self._ws_client.send(
            json.dumps(
                {
                    'method': 'subscribe',
                    'params': {
                        'channel': 'trade',
                        'symbol': self.product_ids,
                        'snapshot': False,
                    },
                }
            )
        )
        # In case of Kraken websocket you get two confirmation messages for each subscription
        # so you have to discard them as they contain no relevant data
        for _ in self.product_ids:
            _ = self._ws_client.recv()
            _ = self._ws_client.recv()

    def is_done(self) -> bool:
        """
        Returns whether the websocket API is done.
        Since Kraken Websocket API is a live stream, it never ends.
        """
        return False

    def get_trades(self) -> List[Trade]:
        """
        Fetches trades from the Kraken websocket API.

        Returns:
            List[Trade]: A list of Trade objects containing trade data.
        """
        data: str = self._ws_client.recv()
        if 'heartbeat' in data:
            logger.info('Received heartbeat, skipping...')
            return []

        # transform raw string into a JSON object
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding JSON: {e}')
            return []

        try:
            trades_data = data['data']
        except KeyError as e:
            logger.error(f'No `data` field with trades in the message {e}')
            return []

        trades = [
            Trade.from_kraken_websocket_response(
                product_id=trade['symbol'],
                price=float(trade['price']),
                quantity=float(trade['qty']),
                timestamp=trade['timestamp'],
            )
            for trade in trades_data
        ]

        return trades

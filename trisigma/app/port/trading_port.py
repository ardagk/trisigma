import asyncio
from abc import ABC, abstractmethod
from trisigma.domain.trading import OrderSignal

#Trading Port
class TradingPort(ABC):

    event_queue: asyncio.Queue

    @abstractmethod
    async def send_order_request(self, account_id, order_signal: OrderSignal) -> str:...

    @abstractmethod
    async def send_cancel_request(self, account_id, signal_id: int):...

    @abstractmethod
    async def send_modify_request(self, account_id, signal_id: int, changes: dict):...

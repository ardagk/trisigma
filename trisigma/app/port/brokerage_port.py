import asyncio
from abc import ABC, abstractmethod
from trisigma.domain.brokerage import Order

class BrokeragePort(ABC):

    quote_asset: str
    event_queue: asyncio.Queue

    @abstractmethod
    async def connect(self):...

    @abstractmethod
    async def place_order(self, asset, side, qty, method) -> Order:...

    @abstractmethod
    async def modify_order(self, order_ref: str, changes: dict):...

    @abstractmethod
    async def cancel_order(self, order_ref: str):...

    @abstractmethod
    async def quantify_asset(self, asset, quote_qty) -> float:...

    @abstractmethod
    async def get_portfolio(self) -> dict:...

    @abstractmethod
    async def get_price(self, asset) -> float:...

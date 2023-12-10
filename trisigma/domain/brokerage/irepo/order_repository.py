from abc import ABC, abstractmethod
from typing import List, Optional
from ..entity.order import Order

#Order Repository
class OrderRepository(ABC):
    
    @abstractmethod
    async def add_order(self, order: Order) -> None:...

    @abstractmethod
    async def update_order_status(
            self, order_ref: str,status: str,
            price=None) -> None:...

    @abstractmethod
    async def get_order(self, order_ref: str) -> Order:...

    @abstractmethod
    async def search_orders(
            self, instance_id: Optional[List[int]],
            order_status: Optional[List[str]]) -> List[Order]:...

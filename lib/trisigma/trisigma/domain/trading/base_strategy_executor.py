from abc import ABC, abstractmethod
import asyncio
from .base_strategy_behavior import StrategyBehavior
from trisigma.domain.brokerage import order_status
from trisigma.domain.trading import Trader
from typing import List

class StrategyExecutor(ABC):

    STRATEGY_NAME: str | None = None
    action_queue: asyncio.Queue

    def __init__ (self):
        self.instances = InstanceRegistry()
        self.order_ref_registry = {}
        self.loop = asyncio.get_event_loop()
        self.action_queue = asyncio.Queue()

    @abstractmethod
    async def start(self):...

    @abstractmethod
    def spawn_instance(self, account_id, config) -> Trader:...

    @abstractmethod
    def remove_instance(self, trader_id):...

    def recv_order_fill(self, order_ref):
        instance = self.instances.find_by_order_ref(order_ref)
        if instance:
            signal_id = instance._signal_map[order_ref]
            instance.on_order_fill(signal_id)
            del instance._signal_map[order_ref]

    def recv_order_cancel(self, order_ref):
        instance = self.instances.find_by_order_ref(order_ref)
        if instance:
            signal_id = instance._signal_map[order_ref]
            instance.on_order_cancel(signal_id)
            del instance._signal_map[order_ref]

    def recv_order_ack(self, order_signal, order_ref):
        instance = self.instances.get(order_signal.trader_id)
        instance._map_signal_id(order_signal.signal_id, order_ref)

class InstanceRegistry:
    def __init__(self):
        self.instance_map = {}

    def add_instance(self, instance, account_id):
        trader_id = instance._trader.trader_id
        self.instance_map[trader_id] = {
                'account_id': account_id,
                'instance':instance}

    def remove_instance(self, trader_id):
        if trader_id in self.instance_map:
            del self.instance_map[trader_id]

    def get(self, trader_id):
        return self.instance_map[trader_id]

    def find_by_order_ref(self, order_ref) -> StrategyBehavior | None:
        result = [
            self.instance_map[trader_id]['instance']
            for trader_id, details in self.instance_map.items()
            if order_ref in details['instance']._signal_map.keys()
            ]
        if len(result) == 0:
            return None
        return result[0]

    def find_by_account_id(self, account_id) -> List[StrategyBehavior]:
        return [
            self.instance_map[trader_id]['instance']
            for trader_id, details in self.instance_map.items()
            if self.instance_map[trader_id]['account_id'] == account_id]

    def find_by_config(self, keys) -> List[StrategyBehavior]:
        return [
            self.instance_map[trader_id]['instance']
            for trader_id, details in self.instance_map.items()
            if all([
                details['config'].get(key) == value
                for key, value in keys.items()]
                )]


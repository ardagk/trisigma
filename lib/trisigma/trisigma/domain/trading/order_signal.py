import uuid
import time as _time
from trisigma.domain.common import modelfactory
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderSignal:
    asset: str
    amount: float 
    method: dict
    trader_id: int
    partition: str
    time: float = modelfactory.curtime()
    signal_id: str = modelfactory.long_id()


from trisigma.domain.market import Instrument
from trisigma.domain.common import modelfactory
import time
from dataclasses import dataclass
from copy import deepcopy

#OrderStatusConst
class OrderStatusConst:
    INITIATED = 'INITIATED'
    SUBMITTED = 'SUBMITTED'
    CANCELLED = 'CANCELLED'
    FILLED = 'FILLED'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    REJECTED = 'REJECTED'

order_status = OrderStatusConst()

#Order
@dataclass(frozen=True)
class Order:
    instrument: Instrument
    side: str
    qty: float
    order_type: str
    account_id: int
    price: float | None = None
    tif: str | None = None
    status: str = order_status.INITIATED
    time: float = modelfactory.curtime()
    order_ref: str = modelfactory.long_id()
    meta: dict = modelfactory.metafield()


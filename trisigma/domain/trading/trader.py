from dataclasses import dataclass
from trisigma.domain.common import modelfactory

@dataclass(frozen=True)
class Trader:
    account_id: int
    strategy_uri: str
    meta: dict = modelfactory.metafield()
    start_time: float = modelfactory.curtime()
    trader_id: int = modelfactory.short_id()

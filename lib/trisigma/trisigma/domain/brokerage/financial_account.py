from dataclasses import dataclass
from trisigma.domain.common import modelfactory

@dataclass(frozen=True)
class FinancialAccount:
    portfolio_manager_id: int
    name: str
    platform: str
    paper: bool
    account_id: int = modelfactory.short_id()
    meta: dict = modelfactory.metafield()


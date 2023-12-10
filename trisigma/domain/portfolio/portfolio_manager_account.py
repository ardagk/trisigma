from dataclasses import dataclass
from trisigma.domain.common import modelfactory

@dataclass(frozen=True)
class PortfolioManager:
    name: str
    portfolio_manager_id: int = modelfactory.short_id()
    meta: dict = modelfactory.metafield()

from dataclasses import dataclass
from trisigma.domain.common import modelfactory

@dataclass
class StrategyDefinition:
    name: str
    version: str
    options: dict
    meta: dict = modelfactory.metafield()

    def to_dict(self):
        return {'name': self.name,
                'version': self.version,
                'options': self.options}
    
    @staticmethod
    def from_dict(d: dict):
        return StrategyDefinition(**d)
        

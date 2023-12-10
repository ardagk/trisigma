from collections import UserDict

#Strategy allocation
class StrategyAllocation(UserDict):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for val in self.values():
            assert isinstance(val, float)
            assert val > 0
            assert val <= 1
        assert self.total_weight() <= 1

    def total_weight(self):    
        tot_weight = 0
        for key in self.keys():
            tot_weight += self[key]
        return tot_weight

    def __setitem__(self, key, value: float):
        assert value > 0
        assert value <= 1
        assert self.total_weight() + value <= 1
        super().__setitem__(key, value)

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Exposure:

    LONG_BOUND_MAGNITUDE = 1    
    SHORT_BOUND_MAGNITUDE = 1

    alloc: dict = field(default_factory=lambda: {})
    buffer: dict = field(default_factory=lambda: {})

    def add(self, key, asset, amount, method=None, ref=None):
        method = method or {}
        assert self.within_limit(asset, amount)
        assert key not in self.buffer
        self.buffer[key] = {'asset': asset, 'filled': 0, 'total': amount, 'method': method, 'ref': ref}

    def cancel(self, key):
        assert key in self.buffer
        del self.buffer[key]

    def modify(self, key, amount):
        assert key in self.buffer
        orig_amount = self.buffer[key]['total']
        if abs(amount) > abs(orig_amount):
            diff = amount - orig_amount
            assert self.within_limit(
                self.buffer[key]['asset'],
                amount - self.buffer[key]['total'])
        self.buffer[key]['total'] = amount

    def flush(self, key):
        assert key in self.buffer
        exposure = self.buffer.pop(key)
        self.alloc.setdefault(exposure['asset'], 0)
        self.alloc[exposure['asset']] += exposure['total']

    def within_limit(self, asset, amount):
        pexp = 0
        nexp = 0
        future_alloc = self.alloc.copy()
        future_alloc.setdefault(asset, 0)
        future_alloc[asset] += amount
        for a in future_alloc.values():
            if a > 0: pexp += a
            else: nexp += abs(a)
        for a in self.buffer.values():
            if a['total'] > 0: pexp += a['total']
            else: nexp += abs(a['total'])
        return (
            pexp <= self.LONG_BOUND_MAGNITUDE and
            nexp <= self.SHORT_BOUND_MAGNITUDE)

    def _old_within_limit(self, asset, amount):
        #Deprecated
        alloc = self.alloc.copy()
        alloc.setdefault(asset, 0)
        alloc[asset] += abs(amount)
        abs_exp = 0
        for a in alloc.values():
            abs_exp += abs(a)
        for a in self.buffer.values():
            abs_exp += abs(a['total'])
        return abs_exp <= 1

    def checksum(self):    
        #return decimal
        return hashlib.sha1(
            json.dumps(
                [self.alloc, self.buffer],
                sort_keys=True
                ).encode('utf-8')).hexdigest()

    def copy(self):
        return deepcopy(self)

    def __str__(self):
        return json.dumps([self.alloc, self.buffer], indent=2, sort_keys=True)

@dataclass(frozen=True)
class ExposureTable:

    exposures: dict = field(default_factory=lambda: {})
    weights: dict = field(default_factory=lambda: {})

    def aggregate(self):
        agg_exp = Exposure()
        exposures = self.exposures.copy()
        weights = self.weights.copy()
        #XXX potential floating point arithmetic error
        for k, exp in exposures.items():
            w = self.weights[k]
            for asset, amount in exp.alloc.items():
                agg_exp.alloc.setdefault(asset, 0)
                agg_exp.alloc[asset] += amount * w
            for key, data in exp.buffer.items():
                agg_exp.buffer[key] = data.copy()
                agg_exp.buffer[key]['total'] *= w
                agg_exp.buffer[key]['filled'] *= w
        return agg_exp

    def add_partition(self, name, weight):
        assert sum(self.weights.values()) + weight <= 1
        self.weights[name] = weight
        self.exposures[name] = Exposure()

    def remove_partition(self, name): 
        exp = self.exposures.pop(name)
        w = self.weights.pop(name)
        return
        items = []
        for key, item in exposures[name].buffer.items():
            item['total'] *= w
            item['filled'] *= w
            items.append((name, item))
        return items

    def rescale_partition(self, name, weight):
        total_weight = sum(self.weights.values())
        assert total_weight - self.weights[name] + weight <= 1
        self.weights[name] = weight

    def find_partition(self, ref):
        for partition, exposure in self.exposures.items():
            if ref in exposure.buffer.keys():
                return partition


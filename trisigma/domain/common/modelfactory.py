from copy import deepcopy
import uuid
import time
import hashlib
from dataclasses import dataclass, asdict, fields, field
from typing import Type, TypeVar, Generic

T = TypeVar('T')

def deconstruct(d) -> dict:
    return asdict(d)

def construct(klass: Type[T], d) -> T:
    fieldtypes = {f.name:f.type for f in fields(klass)} #type: ignore
    _fields = {}
    for f in d:
        if f in fieldtypes:
            _fields[f] = _construct_inner(fieldtypes[f],d[f])
        else:
            raise ValueError(f'Unknown field {f}')
    return klass(**_fields)

def _construct_inner(klass, d):
    if klass in [int, float, str, bool]:
        return klass(d)
    elif klass == type(None):
        return None
    elif klass == dict: 
        dcp = deepcopy(d)
        for k in dcp:
            dcp[k] = _construct_inner(type(dcp[k]), dcp[k])
        return dcp
    elif klass == list:
        return [_construct_inner(type(e), e) for e in d]
    elif hasattr(klass, '__dataclass_fields__'):
        return klass(**d)

def _id32() -> int:
    h = hashlib.sha1(str(time.time()).encode('utf-8'))
    return int(h.hexdigest()[:8], 16)

#field wrappers
def long_id(): return field(default_factory=lambda: uuid.uuid4().hex)
def short_id(): return field(default_factory=lambda: _id32())
def metafield(): return field(default_factory=lambda: {})
def curtime(): return field(default_factory=lambda: time.time())



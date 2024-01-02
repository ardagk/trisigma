import json
import time
from collections import UserDict
import logging
from pymemcache.client.base import Client
from trisigma.domain.common import integrity
from queue import Queue

class _Memcached():

    def __init__(self, host='localhost', port=11211):
        self.host = host
        self.port = port
        self.client = Client(host)

    def __getitem__(self, key: str):
        return self.client.get(key)

    def __setitem__(self, key, value):
        self.client.set(key, value)

    def __delitem__(self, key):
        self.client.delete(key)


class CacheMemcached (UserDict):

    CACHE_KEY = lambda _, *x: integrity.hashkey(*x)

    data = {}
    _data = {}

    def __init__(self, host='localhost', port=11211):
        self.mc = _Memcached(host, port)

    def prepare_key(self, args) -> str:
        if isinstance(args, tuple):
            return integrity.hashkey(*args)
        elif isinstance(args, (str, int)):
            return str(args)
        else:
            return integrity.hashkey(args)

    def prepare_value(self, obj):
        typ = 'object'
        timestamp = int(time.time()*1000)
        value = obj
        entry = {
            "value": value,
            "checksum": integrity.dict_hash(value),
            "timestamp": timestamp,
            "type": typ
        }
        return entry

    def __getitem__(self, key):
        key = self.prepare_key(key)
        entry = self._read_mem_json(key)
        if entry is None:
            return
        if entry['type'] == 'sersync.Queue':
            value = Queue(entry['value'])
        else:
            value = entry['value']
        super().__setitem__(key, value)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        key = self.prepare_key(key)
        entry = self.prepare_value(value)
        if key in self._data:
            if integrity.dict_eq(self._data[key], entry['value']):
                return
        logging.debug("Cache: %s = %s", key, entry['value'])
        self._data[key] = entry
        self._write_mem_json(key, entry)

    def __delitem__(self, key):
        key = self.prepare_key(key)
        self._del_mem_json(key)
        super().__delitem__(key)

    def update(self, data: dict): #pyright: ignore
        for key, value in data.items():
            self[key] = value

    def _write_mem_json(self, key, value):
        s = json.dumps(value)
        self.mc[key] = s

    def _read_mem_json(self, key):
        raw = self.mc[key]
        if raw is None:
            return
        s = raw.decode('utf-8')
        s = s.replace("\'", "\"")
        value = json.loads(s)
        return value

    def _del_mem_json(self, key):
        del self.mc[key]


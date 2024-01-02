import hashlib
import time
import json

def hashkey(row):
    return hashlib.sha1(json.dumps(row, sort_keys=True).encode('utf-8')).hexdigest()

def dict_hash(d):
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode('utf-8')).hexdigest()

def dict_eq(d1, d2):
    return dict_hash(d1) == dict_hash(d2)

def generate_id() -> int:
    key = time.time()
    full_hash = int(hashlib.sha1(str(key).encode('utf-8')).hexdigest(), 16)
    trimmed_hash = int(str(full_hash)[:10])
    return trimmed_hash



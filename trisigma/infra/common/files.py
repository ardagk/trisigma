import sys
import os
import json
from pathlib import Path

# DIRECTORIES
DEFAULT_BASE = os.path.expanduser("~/.local/share/trisigma")
MARK = ".pin"
DIRS= {
    "base" : "",
    "logs" : "logs/",
    "sqlite3" : "sqlite3/",
    "blobs" : "blobs/",
    "tblobs" : "tblobs/",
    "credentials" : "credentials/",
}

def setup (base_path):
    if os.path.exists(normpath(base_path)):
        if not next(os.walk(base_path))[1]:
            base_path = os.path.join(base_path, os.path.basename(base_path))
    for p in DIRS.values():
        new_path = os.path.normpath(os.path.join(base_path, p))
        Path(new_path).mkdir(parents=True, exist_ok=True)
    pin_path = Path(os.path.join(base_path, ".pin"))
    Path(pin_path).touch()

def base_exists (base_path):
    pin_path = Path(os.path.join(base_path, ".pin"))
    return os.path.exists(pin_path)

def path (name, join=""):
    base_path = os.path.normpath(
        os.path.expanduser(
            os.getenv("BOTDATA", DEFAULT_BASE)
        )
    )
    setup(base_path) if not base_exists(base_path) else None
    output = os.path.normpath(os.path.join(base_path, DIRS[name], join))
    return output

def add_ext(filename, ext):
    fullname = filename
    if filename[-len(ext):] != ext:
        fullname = fullname + ext
    return fullname






def save(output, name, _dir="base"):
    """Save a variable in "{BOTDATA}/data/var/" as a json file.

    :param output: variable that will be saved.
    :type output: string
    :param name: file name (without extension)
    :type name: string
    """
    name = add_ext(name, '.json')
    with open(path(_dir, name), 'w') as file:
        json.dump(output, file)

def load(name, _dir="base", when_empty="_raise_"):
    """Load a variable in "{BOTDATA}/data/var" that was previously saved.

    :param name: name of the json file (without .json extension)
    :type name: string
    """
    try:
        name = add_ext(name, '.json')
        with open(path(_dir, name), 'r') as file:
            var = json.load(file)
            return var
    except FileNotFoundError as e:
        if when_empty == "_raise_":
            raise e
        else:
            return when_empty

def normpath(path): return os.path.normpath(os.path.expanduser(path))

def file_search(path):
    """Search for the given path in sys.path"""
    for p in sys.path:
        if os.path.exists(os.path.join(p, path)):
            return os.path.join(p, path)

def get_credentials(domain, account_name):
    """returns the credentials for the account"""
    cred_path = os.path.join(
        os.getenv("CREDENTIALS_DIR", "credentials"),
        f"{domain}/{account_name}",
        "key.json"
    )
    with open(cred_path) as f:
        creds = json.load(f)
        return creds





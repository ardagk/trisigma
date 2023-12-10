from trisigma.interface.common import BaseServerRabbitMQ
import asyncio
import json
import sys
import logging

null_handler = logging.NullHandler()
logging.getLogger().addHandler(null_handler)

def dict_equal(d1, d2):
    if d1.keys() != d2.keys():
        return False
    for key in d1.keys():
        if d1[key] != d2[key]:
            return False
    return True

def generic_responder(options):
    async def wrapper(**params):
        for option in options:
            if option[0]['params'] == params:
                print(json.dumps(option[1]), flush=True)
                if option[1]['status'] == 'ok':
                    return option[1]['message']
                elif option[1]['status'] == 'error':
                    raise Exception(option[1]['message'])
        raise Exception('UNKNOWN')
    return wrapper

class RMQMockServer(BaseServerRabbitMQ):
    def __init__(self, rules, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rules = rules
        self.prepare_endpoints()

    def prepare_endpoints(self):
        for endpoint in self.rules:
            self.register(endpoint)(generic_responder(self.rules[endpoint]))

if __name__ == "__main__":
    sys.argv.pop(0)
    sys.stdout.flush()
    SERVER_NAME = sys.argv[0]
    MSG_PATH = sys.argv[1]
    #MSG_PATH = 'tests/data/trading_port_messages.json'
    #SERVER_NAME = 'TESTSERVER'
    with open(MSG_PATH) as f:
        rules = json.load(f)
    server = RMQMockServer(rules, SERVER_NAME)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.start())
    loop.run_forever()




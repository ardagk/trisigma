from trisigma.infra.common import BaseClientRabbitMQ
import asyncio
import json
import sys

async def main(endpoint, params):
    try:
        resp = await client.request(endpoint, params)
        data = {'status': 'ok', 'message': resp}
        print(json.dumps(data))
    except Exception as e:
        data = {'status': 'error', 'message': str(e)}
        print(json.dumps(data))


if __name__ == "__main__":
    sys.argv.pop(0)
    SERVER_NAME = sys.argv[0]
    ENDPOINT = sys.argv[1]
    PARAMS = json.loads(sys.argv[2])
    #SERVER_NAME = 'TESTSERVER'
    #ENDPOINT = 'get_position'
    #PARAMS = {'asset': 'SPY'}
    client = BaseClientRabbitMQ(SERVER_NAME)
    loop = asyncio.get_event_loop()
    loop.create_task(client.connect())
    loop.run_until_complete(main(ENDPOINT, PARAMS))
    pass





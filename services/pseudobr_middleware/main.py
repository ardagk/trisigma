import os
import sys
import asyncio
from trisigma.infra.adapter import PseudoBrokerageAdapter
from trisigma.interface.driver import BrokerageMiddleware
from trisigma.infra.repository import OrderRepositoryMongo, PortfolioRepositoryMongo

AGENT_NAME = os.getenv('AGENT_NAME', 'pseudo-brokerage-middleware')
RABBITMQ_URI = os.getenv('RABBITMQ_URI', '')
MONGO_URI = os.getenv('MONGO_URI', '')
ACCOUNT_ID = int(sys.argv[1])
print('Starting Brokerage Middleware, account_id:', ACCOUNT_ID)

def hello():
    print(f'AGENT NAME: {AGENT_NAME}')
    print(f'RABBITMQ URI: {RABBITMQ_URI}')
    print(f'MONGO URI: {MONGO_URI}')
    assert MONGO_URI, 'MONGO_URI is not set'
    assert RABBITMQ_URI, 'RABBITMQ_URI is not set'
    assert ACCOUNT_ID is not None, 'ACCOUNT_ID is not set'

if __name__ == '__main__':
    order_repository = OrderRepositoryMongo(MONGO_URI)
    portfolio_repository = PortfolioRepositoryMongo(MONGO_URI)
    brokerage_adapter = PseudoBrokerageAdapter(
            MONGO_URI, ACCOUNT_ID, 1000000)
    driver = BrokerageMiddleware(
        uri = RABBITMQ_URI,
        account_id = ACCOUNT_ID,
        brokerage_adapter = brokerage_adapter,
        order_repository = order_repository,
        portfolio_repository = portfolio_repository)
    loop = asyncio.get_event_loop()
    loop.create_task(driver.start())
    loop.run_forever()



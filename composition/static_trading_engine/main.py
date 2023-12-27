import os
import logging
import asyncio
from strategy import StaticTradingExecutor
from trisigma.infra.adapter import TradingAdapterRabbitMQ
from trisigma.interface.driver import AlgoTradingEngine
from trisigma.infra.repository import TraderRepositoryMongo

from trisigma.infra.logger import logconfig

AGENT_NAME = os.getenv('AGENT_NAME', 'pseudo-brokerage-middleware')
RABBITMQ_URI = os.getenv('RABBITMQ_URI', '')
MONGO_URI = os.getenv('MONGO_URI', '')
ACCOUNT_ID = os.getenv('ACCOUNT_ID', '')

def hello():
    print(f'AGENT NAME: {AGENT_NAME}')
    print(f'RABBITMQ URI: {RABBITMQ_URI}')
    print(f'MONGO URI: {MONGO_URI}')
    assert MONGO_URI, 'MONGO_URI is not set'
    assert RABBITMQ_URI, 'RABBITMQ_URI is not set'
    assert ACCOUNT_ID is not None, 'ACCOUNT_ID is not set'

if __name__ == '__main__':
    trader_repository = TraderRepositoryMongo(MONGO_URI)
    trading_adapter = TradingAdapterRabbitMQ(RABBITMQ_URI)
    driver = AlgoTradingEngine(
        uri = RABBITMQ_URI,
        strategy_executor = StaticTradingExecutor(),
        trading_adapter = trading_adapter,
        trader_repository = trader_repository
        )
    loop = asyncio.get_event_loop()
    loop.create_task(driver.start())
    loop.run_forever()



import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
from trisigma.infra.adapter import (
        MarketAdapterWebull,
        TraderManagementAdapterRabbit,
        AccountManagementAdapterRabbit)
from trisigma.infra.repository import (
        OrderRepositoryMongo,
        PortfolioRepositoryMongo,
        TraderRepositoryMongo)

from trisigma.app.usecase import (
        GetStrategyAllocationUseCase,
        UpdateStrategyAllocationUseCase,
        GetStrategyDefinitionsUseCase,
        GetPortfolioPositionUseCase,
        GetReturnComparisonUseCase,
        GetTransactionsUseCase,
        GetOpenOrdersUseCase,
        GetTraderJournalUseCase,
        GetTraderObservationsUseCase,
        GetPortfolioKeyStatsUseCase,
        GetActiveBotsUseCase)

MONGO_URI = os.getenv('MONGO_URI'); assert MONGO_URI
RABBITMQ_URI = os.getenv('RABBITMQ_URI'); assert RABBITMQ_URI

portfolio_repo = PortfolioRepositoryMongo(MONGO_URI)
order_repo = OrderRepositoryMongo(MONGO_URI)
trader_repo = TraderRepositoryMongo(MONGO_URI)
market_adapter = MarketAdapterWebull()
trader_management_adapter = TraderManagementAdapterRabbit(RABBITMQ_URI)
account_management_adapter = AccountManagementAdapterRabbit(RABBITMQ_URI)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/portfolio/allocation')
async def portfolio_allocation(portfolio_manager_id: int):
    usecase = GetStrategyAllocationUseCase(
            portfolio_repo)
    resp = await usecase.run(portfolio_manager_id)
    return resp

@app.post('/portfolio/allocation')
async def portfolio_allocation_post(portfolio_manager_id: int, strategy_allocation: Dict):
    usecase = UpdateStrategyAllocationUseCase(
            portfolio_repository = portfolio_repo,
            trader_repository = trader_repo,
            trader_management_adapter = trader_management_adapter,
            account_management_adapter = account_management_adapter,
            )
    result = await usecase.run(portfolio_manager_id, strategy_allocation)
    assert result
    return {'status': 'success'}

@app.get('/strategy/definition')
async def strategy_definition():
    usecase = GetStrategyDefinitionsUseCase(trader_repo)
    resp = await usecase.run()
    return resp

@app.get('/portfolio/position')
async def portfolio_position(portfolio_manager_id: int):
    usecase = GetPortfolioPositionUseCase(portfolio_repo, market_adapter)
    resp = await usecase.run(portfolio_manager_id)
    return resp

@app.get('/portfolio/returnchart')
async def portfolio_return_chart(portfolio_manager_id: int, interval: str, benchmark: str = 'SPY'):
    usecase = GetReturnComparisonUseCase(portfolio_repo, market_adapter)
    resp = await usecase.run(portfolio_manager_id, interval, benchmark)
    return resp

@app.get('/portfolio/keystats')
async def portfolio_key_stats(portfolio_manager_id: int, interval: str):
    usecase = GetPortfolioKeyStatsUseCase(portfolio_repo)
    resp = await usecase.run(portfolio_manager_id, interval)
    return resp

@app.get('/portfolio/transactions')
async def portfolio_transactions(
        trader_id: int,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        count: int = 100):
    usecase = GetTransactionsUseCase(order_repo)
    resp = await usecase.run(trader_id, start_time, end_time, count)
    return resp

@app.get('/portfolio/openorders')
async def portfolio_open_orders(trader_id: int):
    usecase = GetOpenOrdersUseCase(order_repo)
    resp = await usecase.run(trader_id)
    return resp

@app.get('/portfolio/journal')
async def trader_journal(trader_id: int, start_time: Optional[int] = None, end_time: Optional[int] = None):
    usecase = GetTraderJournalUseCase(trader_repo)
    resp = await usecase.run(trader_id, start_time, end_time)
    return resp

@app.get('/portfolio/observations')
async def trader_observations(trader_id: int, start_time: Optional[int] = None, end_time: Optional[int] = None):
    usecase = GetTraderObservationsUseCase(trader_repo)
    resp = await usecase.run(trader_id, start_time, end_time)
    return resp

@app.get('/portfolio/bots')
async def portfolio_bots(portfolio_manager_id: int):
    usecase = GetActiveBotsUseCase(trader_repo)
    resp = await usecase.run(portfolio_manager_id)
    return resp

async def connect():
    await trader_management_adapter.connect()
    await account_management_adapter.connect()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect())

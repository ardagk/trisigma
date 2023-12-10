from datetime import timedelta
from typing import List
import time
import pandas as pd
from trisigma.domain.portfolio import PortfolioRepository
from trisigma.domain.market import Instrument
from trisigma.domain.common import duration

class GetReturnComparisonUseCase:

    portfolio_repo: PortfolioRepository

    def __init__(self, portfolio_repository, market_adapter):
        self.portfolio_repo = portfolio_repository
        self.market_adapter = market_adapter

    async def run(self, portfolio_manager_id,
            interval, benchmark_asset) -> List[dict]:

        end_time = time.time()
        start_time = end_time
        if interval == '1d':
            start_time -= timedelta(days=1).total_seconds()
        elif interval == '1w':
            start_time -= timedelta(weeks=1).total_seconds()
        elif interval == '4w':
            start_time -= timedelta(weeks=4).total_seconds()
        elif interval == '12w':
            start_time -= timedelta(weeks=12).total_seconds()
        elif interval == 'SE':
            start_time = None
        else:
            raise Exception('Invalid interval')

        snapshots = await self.portfolio_repo.get_portfolio_snapshots(
                portfolio_manager_id, start_time, end_time)
        positions = [(ss['time'], ss['positions']) for ss in snapshots]
        if not positions:
            return {'benchmark':[], 'portfolio':[], 'time':[]}
            #assert positions, 'no snapshots found in the specified time range'
        worths = []
        for t, full_pos in positions:
            t_worth = 0
            for acc_pos in full_pos.values():
                for dvalue in acc_pos.values():
                    t_worth+=dvalue['value']
            worths.append({'time':t, 'portfolio': t_worth})

        portf_value = pd.DataFrame(worths)
        portf_value['time'] = pd.to_datetime(portf_value['time'], unit='s')
        portf_value.set_index('time', inplace=True)
        #resample to daily
        portf_value = portf_value.resample('D').last()
        portf_value.index = portf_value.index.astype(int) // 10**9
        #convert float timestamp index to int timestamp
        benchmark_value = await self.market_adapter.get_candles(
            instrument=Instrument.stock(benchmark_asset, 'USD'),
            interval=duration.Interval('15m'),
            timespan=duration.TimeSpan(start_time, end_time))
        benchmark_value.index = benchmark_value.index.tz_convert('UTC')
        benchmark_value = benchmark_value.resample('D').last()
        benchmark_value.index = benchmark_value.index.astype(int) // 10**9
        comparison = benchmark_value.merge(portf_value, how='left', left_index=True, right_index=True)
        comparison.rename(columns={'close': 'benchmark'}, inplace=True)
        comparison = comparison[['benchmark', 'portfolio']]
        comparison = comparison.fillna(method='ffill')
        comparison = comparison.fillna(method='bfill')
        comparison = comparison.pct_change() * 100
        comparison = comparison.cumsum()
        comparison = comparison.dropna()
        comparison = comparison.round(2)
        comparison = comparison.reset_index()
        result = comparison.to_dict(orient='list')
        return result

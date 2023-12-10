from trisigma.domain.market import Instrument
from trisigma.domain.common import duration
from datetime import datetime
import exchange_calendars as xcals
import pandas as pd
import requests
from typing import Optional
from webull import webull
from cachetools import cached, TTLCache

QUERY='https://quotes-gw.webullfintech.com/api/quote/charts/query'

class MarketAdapterWebull():

    def __init__(self):
        self.wbo = webull()
        self.tickerid = cached(
            cache=TTLCache(maxsize=1024, ttl=86400*7)
          )(lambda ticker: self.wbo.get_ticker(ticker))

    async def get_price(self, instrument: Instrument) -> float:
        df =  await self.get_candles(
                instrument=instrument,
                interval = duration.Interval('1m'),
                limit=1)
        return df.iloc[-1]['close']

    async def get_candles(
            self,
            instrument: Instrument,
            interval: duration.Interval,
            timespan: Optional[duration.TimeSpan] = None,
            limit: Optional[int] = None):
        #Step 1: get minutes that we want to fetch
        if timespan and not limit:
            minutes = _market_minutes_between(
                    timespan.start.timestamp(),
                    timespan.end.timestamp())
        elif limit and not timespan:
            min_map = {86400: 390, 604800: 390*5, 31536000: 390*5*52}
            intv_mult = min_map.get(int(interval.unit), int(interval.unit)//60)
            count = intv_mult * interval.coef * limit
            minutes = _past_market_minutes(count)
        else:
            raise ValueError(
                    "One of timespan or limit must be provided.")
        #Step 2: Prepare requests respecting endpoint size limit of 800
        pd_intv = '15T' if int(interval) >= 15*60 else '1T'
        minutes = minutes.floor(pd_intv).drop_duplicates()
        assert isinstance(minutes, pd.DatetimeIndex) #XXX not tested might be wrong
        minutes = minutes.shift(1, freq=pd_intv)
        bucket_size = 800
        buckets = [minutes[i:i + bucket_size] #pyright: ignore
                   for i in range(0, len(minutes), bucket_size)] #pyright: ignore
        tickerid = self.tickerid(instrument.base.upper())
        reqs = [
                self._prepare_request(tickerid, bucket, pd_intv)
                for bucket in buckets]
        #Step 3: Send requests and resample to desired interval
        candles = []
        for req in reqs:
            resp = requests.Session().send(req)
            rows = process_response(resp)
            candles.extend(rows)
        df = pd.DataFrame(candles)
        df = df.drop_duplicates(subset=['time'])
        if len(df) == 0:
            return df
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df = df.set_index('time')
        df = df.resample(interval.to_pandas_str()).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'})
        df = df.dropna()
        if limit:
            df = df[-limit:]
        return df


    def _prepare_request(self, tickerid, bucket, freq):
        bucket = bucket.sort_values()
        timestamp = int(bucket[-1].timestamp())
        assert freq in ['1T', '15T'], "bucket freq must be 1T or 15T"
        intv = 'm1' if freq == '1T' else 'm15'
        headers=self.wbo.build_req_headers()
        params = {
            "tickerIds": tickerid,
            "type": intv,
            "count": len(bucket),
            "timestamp": timestamp,
            "extendTrading": 0
        }
        prepared = requests.Request(
            'GET', QUERY, params=params, headers=headers).prepare()
        return prepared

def _market_minutes_between(start: float, end: float) -> pd.DatetimeIndex:
    cal = xcals.get_calendar("NYSE")
    start_dt = datetime.fromtimestamp(start)
    end_dt = datetime.fromtimestamp(end)
    mins =  cal.minutes_in_range(start_dt, end_dt)
    return pd.DatetimeIndex(mins) # type: ignore

def _past_market_minutes(count) -> pd.DatetimeIndex:
    cal = xcals.get_calendar("NYSE")
    #get last market minute
    last_trading_minute = cal.previous_minute(
        pd.Timestamp.now(tz='America/New_York'))
    mins = cal.minutes_window(last_trading_minute, -count)
    return pd.DatetimeIndex(mins) # type: ignore

def process_response (resp):
    """Converts rows to type int,float"""
    if resp.status_code != 200:
        try: msg = resp.json()
        except: msg = resp.text
        raise Exception(f"Error fetching candles: {msg}")
    raw_data = resp.json()[0]["data"]
    rows = []
    for row_str in raw_data:
        r = [float(x) for x in row_str.split(',')[:-1]]
        rows.append(
            {
                "time": int(r[0]),
                "open": float(r[1]),
                "high": float(r[3]),
                "low": float(r[4]),
                "close": float(r[2]),
                "volume": float(r[6])
            }
        )
    sorted_rows = sorted(rows, key=lambda x: x['time'])
    return sorted_rows


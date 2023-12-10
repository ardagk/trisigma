from trisigma.domain.market import Instrument
from trisigma.domain.common import duration
import pandas as pd
from typing import Optional
from datetime import timedelta

from binance.spot import Spot
from concurrent.futures import ThreadPoolExecutor

UNITS = {60: 'm', 3600: 'h', 86400: 'd', 604800: 'w', 31536000: 'y'} #XXX no year

class MarketAdapterBinance():

    BUCKET_SIZE = 800

    def __init__(self, pool_size=1, proxies=None):
        self.client = Spot(proxies=proxies)
        self.pool_size = pool_size

    def get_candles(
            self,
            instrument: Instrument,
            interval: duration.Interval,
            timespan: Optional[duration.TimeSpan] = None,
            limit: Optional[int] = None
        ):

        assert interval.unit < duration.WEEK, "above week interval isn't supported"
        assert limit != timespan or limit is None, 'limit and timespan are mutually exclusive'

        bucket_size = self.BUCKET_SIZE

        symbol = (instrument.base + instrument.quote).upper()
        intv = interval.strf("{coef}{unit}", units=UNITS)
        base_params = {"symbol": symbol, "interval": intv, "limit": bucket_size}
        # split put requested candles into buckets
        if timespan:
            timeframes = pd.date_range(timespan.start, timespan.end, freq=interval.to_pandas_str())
            buckets = [timeframes[i:i+bucket_size] for i in range(0, len(timeframes), bucket_size)]
        else:
            limit = limit or 1
            end = pd.Timestamp.now(tz='UTC').floor(interval.to_pandas_str())
            start = end - timedelta(seconds=int(interval)*limit)
            timeframes = pd.date_range(start, end, freq=interval.to_pandas_str())
            buckets = [timeframes[i:i+bucket_size] for i in range(0, len(timeframes), bucket_size)]
        # prepare requests
        requests = []
        for bucket in buckets:
            start = int(bucket[0].timestamp()*1000)
            end = int(bucket[-1].timestamp()*1000)
            params = base_params.copy()
            params.update({"startTime": start, "endTime": end})
            requests.append(
                lambda params=params: self.client.klines(**params))
        # send requests in parallel
        with ThreadPoolExecutor(max_workers=self.pool_size) as executor:
            responses = executor.map(lambda r: r(), requests)
        df = pd.DataFrame()
        # process and merge responses
        for resp in responses:
            if not resp: continue
            candles = process_response(resp)
            buc_df = pd.DataFrame(candles)
            buc_df.set_index('time', inplace=True)
            buc_df.index = pd.to_datetime(buc_df.index, unit='s', utc=True)
            buc_df.index = buc_df.index.shift(1, freq=interval.to_pandas_str()) #pyright: ignore
            buc_df.index.name = 'time' #pyright: ignore
            df = pd.concat([df, buc_df])
        df.drop_duplicates(inplace=True)
        return df

def process_response (rows):
    """Converts rows to type int,float"""
    processed_rows = [
        {
            "time": int(r[0]/1000),
            "open": float(r[1]),
            "high": float(r[2]),
            "low": float(r[3]),
            "close": float(r[4]),
            "volume": float(r[5])
        }
        for r in rows
    ]
    return processed_rows


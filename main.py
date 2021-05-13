import json
import time

import requests
from pyprnt import prnt

CACHE = []

class CandleData:
    def __init__(self, market, candle_date_time_utc, candle_date_time_kst,
                 opening_price, high_price, low_price, trade_price, timestamp,
                 candle_acc_trade_price, candle_acc_trade_volume, unit):
        self.market = market
        self.candle_date_time_utc = candle_date_time_utc
        self.candle_date_time_kst = candle_date_time_kst
        self.opening_price = opening_price
        self.high_price = high_price
        self.low_price = low_price
        self.trade_price = trade_price
        self.timestamp = timestamp
        self.candle_acc_trade_price = candle_acc_trade_price
        self.candle_acc_trade_volume = candle_acc_trade_volume
        self.unit = unit

    def __str__(self):
        return str(self.__dict__)

def main():
    url = "https://api.upbit.com/v1/candles/minutes/1"
    querystring = {"market": "KRW-BTC", "count": "1"}

    while True:
        response = requests.get(url, params=querystring)
        if response.status_code != 200:
            time.sleep(1)
            continue

        data = json.loads(response.text)
        if data:
            data = data[0]
            cd = CandleData(**data)
            print(cd)

        time.sleep(0.5)


if __name__ == '__main__':
    main()

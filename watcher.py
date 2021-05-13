import json
import datetime
import os
import time
from decimal import Decimal
from threading import Thread

import telebot
from dotenv import load_dotenv

import requests

load_dotenv()

# DOGE TO THE MOON!
SYMBOL = os.getenv("FUTURES_SYMBOL")
WATCH_UNIT = os.getenv("WATCH_UNIT")
INTERVAL = 1
BASE_URL = "https://fapi.binance.com"
CACHE = None

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BOT = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode=None)


def fetch_price(symbol):
    path = "/fapi/v1/ticker/price"

    response = requests.get(BASE_URL + path, params={"symbol": symbol})
    data = json.loads(response.text)

    data["time"] = data["time"] // 1000
    data["datetime"] = datetime.datetime.utcfromtimestamp(data["time"])
    return data


def start_listening_thread():
    @BOT.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        BOT.reply_to(message, "Howdy, how are you doing?")


    @BOT.message_handler(commands=['interval'])
    def set_interval(message):
        commands = message.text.split()
        if len(commands) != 2:
            BOT.reply_to(message, f"command [{message.text}] invalid")
            return

        try:
            interval = int(commands[1])
            global INTERVAL
            INTERVAL = interval
        except Exception as e:
            BOT.reply_to(message, f"command [{message.text}] invalid")
            return

        BOT.reply_to(message, f"interval {INTERVAL} set")

    @BOT.message_handler(commands=['price'])
    def send_price(message):
        print("[info] price command received")

        global CACHE
        if not CACHE:
            return

        symbol = CACHE["symbol"]
        price = CACHE["price"]
        timestamp = CACHE["time"]
        t_datetime = CACHE["datetime"]
        content = f"symbol: {symbol} price: {price} at {t_datetime} ({timestamp})"
        print(f"[telegram] {content}")
        BOT.reply_to(message, content)

    while True:
        try:
            BOT.infinity_polling()
        except Exception as e:
            print("[telegram] listening error: {e}")


def main(symbol):
    t = Thread(target=start_listening_thread, daemon=True)
    t.start()

    while True:
        start = time.time()

        try:
            fetched_data = fetch_price(symbol)
        except Exception as e:
            print(f"[error] fetching price: {e}")
            time.sleep(0.2)
            continue

        symbol = fetched_data["symbol"]
        price = fetched_data["price"]
        timestamp = fetched_data["time"]
        t_datetime = fetched_data["datetime"]
        print(f"[info] symbol: {symbol} price: {price} at {t_datetime} ({timestamp})")

        global CACHE
        if not CACHE:
            CACHE = fetched_data
            continue

        price_unit = Decimal(price) // Decimal(WATCH_UNIT)
        cache_price_unit = Decimal(CACHE["price"]) // Decimal(WATCH_UNIT)
        diff_unit = price_unit - cache_price_unit

        # SIGNAL
        if abs(diff_unit) >= 1 and timestamp >= CACHE["time"]:
            diff = Decimal(price) - Decimal(CACHE["price"])  # if pos, price up, if neg, price down
            direction = "UP" if diff > 0 else "DOWN"
            content = f"{direction}\n{symbol}\n{CACHE['price']} => {price}\n{diff}\n{CACHE['datetime']} ({CACHE['time']})\n{t_datetime} ({timestamp})"
            print(f"[signal] {direction} {symbol} {CACHE['price']} => {price} {diff} {CACHE['datetime']} ({CACHE['time']}) {t_datetime} ({timestamp})")
            # DO SOMETHING
            global BOT
            global CHAT_ID
            BOT.send_message(CHAT_ID, content)

        CACHE = fetched_data

        time_to_sleep = abs(INTERVAL - (time.time() - start))
        # print(f"sleep for {time_to_sleep}s")
        time.sleep(time_to_sleep)


if __name__ == "__main__":
    try:
        main(SYMBOL)
    except Exception as e:
        print(f"[error] main function: {e}")

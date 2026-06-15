from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks.collectors.market_collector import fetch_market_candles


def main():
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(fetch_market_candles.apply_async, "interval", minutes=5, args=["BTCUSDT", "1h", 100])
    scheduler.start()


if __name__ == "__main__":
    main()


from datetime import datetime
from parser import parser
from time import sleep

from bot import send_message
from disk import init


def main():
    while True:
        try:
            config = init()

            print(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), end=' ')

            ads = parser(config)
            send_message(ads, config)
            print('.')

        except Exception as e:
            e = "main/main:" + e.__str__()
            print(e)
        finally:
            sleep(config['scrape_interval'])


if __name__ == "__main__":
    main()

from parser import parser
from time import time

from bot import send_message
from disk import init


def main():
    start_time = time()
    config = init()
    ads = parser(config)
    send_message(ads, config)
    print(f'Время выполнения: {int(time() - start_time)} сек')


if __name__ == "__main__":
    main()

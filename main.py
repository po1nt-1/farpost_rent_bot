from parser import parser

from bot import send_message
from disk import init


def main():
    config = init()
    ads = parser(config)
    send_message(ads, config)


if __name__ == "__main__":
    main()

import logging

from parser import parser
from time import sleep

from bot import send_message
from disk import init

from logging import getLogger, StreamHandler, basicConfig
from sys import stdout
from ecs_logging import StdlibFormatter

log = getLogger('main')


def main():
    while True:
        try:
            config = init()

            handler = StreamHandler()
            formatter = StdlibFormatter(
                exclude_fields=[
                    "log.original",
                    "ecs",
                    "process",
                ]
            )
            handler.setFormatter(StdlibFormatter())
            handler.setStream(stdout)
            handler.setFormatter(formatter)
            basicConfig(
                level=config['log']['level'],
                handlers=[handler]
            )

            ads = parser(config)
            send_message(ads, config)

        except Exception as e:
            log.exception('main loop exception')
        finally:
            sleep(config['scrape_interval'])


if __name__ == "__main__":
    main()

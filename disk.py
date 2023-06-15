from yaml import safe_load
from logging import getLogger


log = getLogger('main.bot')


def init():
    with open('config.yaml', 'r') as f:
        cfg = safe_load(f)
        log.debug('config loaded')
        return cfg


def ad_exists(ad_url):
    with open('ads.log', 'a') as f:
        pass

    with open('ads.log', 'r') as f:
        for line in f:
            ad = line.split("'")[1]

            if ad_url == ad:
                return True

        return False


def dump_on_disk(ad):
    with open('ads.log', 'a') as f:
        f.write(f'{ list(ad.values()) }\n')

    log.debug(f'{ len(list(ad.values())) } ads dumped on disk')

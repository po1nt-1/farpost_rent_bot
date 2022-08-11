
from yaml import safe_load


def init():
    with open('config.yaml', 'r') as f:
        return safe_load(f)


def ad_exists(ad_url):
    with open('ads.log', 'a') as f:
        pass

    with open('ads.log', 'r') as f:
        flag = False

        for line in f:
            ad = line.split("'")[1]

            if ad_url == ad:
                return True

        return False


def dump_on_disk(ad):
    with open('ads.log', 'a') as f:
        f.write(f'{ list(ad.values()) }\n')

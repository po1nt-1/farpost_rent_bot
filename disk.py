from yaml import safe_load


def init():
    with open('config.yaml', 'r') as f:
        return safe_load(f)


def dump_on_disk(ad):
    with open('ads.log', 'a') as f:
        f.write(f'{ list(ad.values()) }\n')

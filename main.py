from pprint import pprint
from time import sleep, time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from yaml import safe_load


def init():
    global config
    global filters

    with open('config.yaml', 'r') as f:
        config = safe_load(f)
        filters = config['filters']


def parser():
    service = Service('./geckodriver', log_path='/dev/null')
    opts = Options()
    opts.add_argument("--headless")
    with Firefox(service=service, options=opts) as driver:
        driver.get(
            f"https://www.farpost.ru/{filters['city']}/realty/rent_flats/?" +
            f"agentType[]={filters['agentType']}&" +
            f"areaTotal_min={filters['areaTotal_min']}&" +
            "".join([f'district[]={e}&' for e in filters['district']]) +
            "".join([f'flatType[]={e}&' for e in filters['flatType']]) +
            f"floor_min={filters['floor_min']}&" +
            f"price_max={filters['price_max']}&" +
            f"price_min={filters['price_min']}&" +
            f"rentPeriod[]={filters['rentPeriod']}"
        )
        sleep(2)

        total_start = time()

        raw_data = driver.find_element(
            By.CLASS_NAME, 'native').find_elements(By.TAG_NAME, 'td')[1:]

        ads = []
        for raw_ad in raw_data:
            ad = {"url": "", "address": "", "price": "",
                  "district": "", "type_": "", "area": ""}

            try:
                url = raw_ad.find_element(
                    By.CSS_SELECTOR, 'a[href^="/vladivostok/realty"]').get_attribute('href')
                ad.update({"url": url})
            except NoSuchElementException:
                pass

            try:
                address = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text.split(', ')
                if len(address) == 2:
                    ad.update({"address": address[1]})
            except NoSuchElementException:
                pass

            try:
                price = raw_ad.find_element(
                    By.CSS_SELECTOR, 'span.price-block__price').text
                ad.update({"price": price.replace(
                    ' ', '').replace('₽', '')})
            except NoSuchElementException:
                pass

            try:
                district = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                district = district[::-1].replace(' ,', ';', 2)[::-1]
                ad.update({"district": district.split(';')[0]})
            except NoSuchElementException:
                pass

            try:
                type_ = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text.split(', ')
                if len(type_) == 2:
                    ad.update({"type_": type_[0]})
            except NoSuchElementException:
                pass

            try:
                area = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                area = area[::-1].replace(' ,', ';', 2)[::-1]
                area = area.split(';')[-1]
                area = area.replace(',', '.')
                ad.update({"area": area.replace(' кв. м.', '')})
            except NoSuchElementException:
                pass

            if '' in ad.values():
                print(ad)
                continue

            if ad not in ads:
                ads.append(ad)
            else:
                print(f'ad skipped {ad}')

        pprint(ads)
        print(f'Найдено {len(ads)} объявлений')
        total_stop = time()

        print(
            f"Прошло {(total_stop - total_start)} с")


if __name__ == "__main__":
    init()
    parser()

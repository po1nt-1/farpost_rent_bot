from base64 import b64encode
from random import randint
from time import sleep
from urllib.parse import quote

from phonenumbers import PhoneNumberFormat, PhoneNumberMatcher, format_number
from selenium.common import exceptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth

from disk import ad_exists, init

EXPERIMENTAL_FLAG = True


def sleep_time():
    return randint(3, 5)


def url_builder(filters):
    return f"https://www.farpost.ru/{ filters.get('city', 'detroit') }" + \
        "/realty/rent_flats/?" + \
        "".join([f'agentType[]={ e }&' for e in filters.get('agentType', [])]) + \
        f"animalsAllowed={ filters.get('animalsAllowed', 0) }&" + \
        f"areaTotal_max={ filters.get('areaTotal_max', 999) }&" + \
        f"areaTotal_min={ filters.get('areaTotal_min', 0) }&" + \
        "".join([f'district[]={ e }&' for e in filters.get('district', [])]) + \
        "".join([f'flatType[]={ e }&' for e in filters.get('flatType', [])]) + \
        f"floor_max={ filters.get('floor_max', 999) }&" + \
        f"floor_min={ filters.get('floor_min', 1) }&" + \
        f"price_max={ filters.get('price_max', 999999) }&" + \
        f"price_min={ filters.get('price_min', 1) }&" + \
        "".join([f'rentPeriod[]={e}&' for e in filters.get('rentPeriod', [])])


def parser_egrp(driver, ads):
    for ad in ads:
        street, house = ad['address'].replace('улица', '').split(maxsplit=1)
        area = float(ad['area'].replace('\\', ''))
        min_area, max_area = int(area) - 1, int(area) + 1
        floor = ad['floor']

        params = '{"form":{"number":"","name":"",' + \
            f'"floor":"{ floor }","address":"",' + \
            '"region":"25","district":"Владивосток",' + \
            f'"place":"","street":"{ street }",' + \
            f'"house":"{ house }","apartment":"",' + \
            f'"min-area":"{ min_area }","max-area":"{ max_area }",' + \
            '"meta_type":"3"},"tab":2}'

        params = quote(params.encode('utf-8'))

        params = b64encode(params.encode('utf8')).decode('utf8')

        url = f'https://egrp365.org/extra/?data={params}'
        ad['egrp'] = f"[error]({ url })"

        driver.get(url)
        flag = 0

        try:
            locator = (By.CSS_SELECTOR, '.table > tbody:nth-child(2)')
            page = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(locator))

            page = page.find_elements(By.TAG_NAME, 'tr')
            tmp = []
            for line in page:
                line = line.find_elements(By.TAG_NAME, 'td')[1].text
                tmp.append(line)

            ad['egrp'] = f"[{ len(tmp) } совпадений](https://httpbin.org/get?info={ ','.join(tmp) })"

        except (exceptions.TimeoutException,
                exceptions.NoSuchElementException):
            try:
                locator = (By.CSS_SELECTOR,
                           '.alert-warning')
                page = WebDriverWait(driver, 2).until(
                    ec.presence_of_element_located(locator))
                page = page.text

                if 'Ничего не найдено' in page:
                    ad['egrp'] = "нет совпадений"

            except exceptions.TimeoutException:
                pass

    return ads


def post_parser(driver, ads):
    for ad in ads:
        driver.get(ad['url'])
        sleep(sleep_time())

        try:
            floor = driver.find_element(
                By.CSS_SELECTOR, 'div.bullViewEx:nth-child(1) '
                '> div:nth-child(7) > div:nth-child(1) > '
                'div:nth-child(2) > div:nth-child(2)'
            ).text

            floor = floor.split(sep='-', maxsplit=1,)[0]
            ad.update({'floor': floor.strip()})

        except exceptions.NoSuchElementException as e:
            print(e)

        try:
            second_price = driver.find_element(
                By.CSS_SELECTOR, 'div.inplace > div:nth-child(2)'
            ).text
            second_price = second_price.replace(
                ', иные коммунальные услуги', ' и иные')
            second_price = second_price.lower()
            ad.update({'second_price': second_price.strip()})

        except exceptions.NoSuchElementException as e:
            print(e)

        try:
            deposit = driver.find_element(
                By.CSS_SELECTOR, 'div.bullViewEx:nth-child(1) > '
                'div:nth-child(7) > div:nth-child(1) > '
                'div:nth-child(1) > div:nth-child(1) > '
                'div:nth-child(1) > div:nth-child(2) > '
                'div:nth-child(1) > span:nth-child(1)'
            ).text
            deposit = "".join(deposit.split(maxsplit=1)[1].split()[:-1])
            ad.update({'deposit': deposit.strip()})

        except exceptions.NoSuchElementException as e:
            print(e)

        try:
            date = driver.find_element(
                By.CSS_SELECTOR, '.viewbull-actual-date').text
            ad.update({'date': date.strip()})

        except exceptions.NoSuchElementException as e:
            print(e)

        try:
            photos = driver.find_element(
                By.CSS_SELECTOR, '.bulletinImages').find_elements(By.TAG_NAME, 'img')
            photos = [p.get_attribute('src') for p in photos]
            ad.update({'photos': photos})

        except exceptions.NoSuchElementException as e:
            print(e)

        try:
            driver.find_element(
                By.CSS_SELECTOR,
                '#bulletin > div > div.ownerInfo.ownerInfo_light '
                '> div > div.owner-info-layout__actions > '
                'div.subject-actions-grid > div:nth-child(1) '
                '> noindex > div > a'
            ).click()
            sleep(sleep_time())

            raw_phones = driver.find_element(
                By.CSS_SELECTOR, 'body > div.modal-window > main').text

            phones = []
            for match in PhoneNumberMatcher(raw_phones, 'RU'):
                p = format_number(match.number, PhoneNumberFormat.E164)[1:]
                if p not in phones and not p.startswith('74232'):
                    phones.append(p)

            ad.update({'phones': phones})

        except exceptions.NoSuchElementException as e:
            print(e)

    return ads


def parser(config):
    filters = config['filters']

    opts = Options()
    opts.headless = True
    opts.add_argument('user-data-dir=./driver_profile/')
    opts.add_argument("start-maximized")
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)

    service = Service('./chromedriver', log_path='/dev/null')

    with Chrome(service=service, options=opts) as driver:
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        sleep(sleep_time() / 3)
        driver.get('https://yandex.ru/')
        sleep(sleep_time() / 3)
        driver.get('https://www.farpost.ru/help/rules')
        sleep(sleep_time() / 3)

        driver.get(url_builder(filters))
        sleep(sleep_time())

        raw_data = driver.find_element(
            By.CLASS_NAME, 'native').find_elements(By.TAG_NAME, 'td')[1:]

        ads = []
        for raw_ad in raw_data:
            ad = {
                "url": "", "address": "", "price": "",
                "district": "", "type_": "", "area": "",
                "phones": [], "floor": "", "second_price": "",
                "date": "", "deposit": "", "photos": [],
                "egrp": ""
            }

            try:
                url = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    f'''a[href^="/{ filters.get('city', 'detroit') }/realty"]'''
                ).get_attribute('href')
                url = url[:23] + url.split('-')[-1].replace('.html', '')

                ad.update({"url": url.strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            if ad_exists(ad['url']):
                continue
            print('.', end='')

            try:
                address = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text
                address = address.split(', ')
                if len(address) == 2:
                    ad.update({"address": address[1].strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            try:
                price = raw_ad.find_element(
                    By.CSS_SELECTOR, 'span.price-block__price').text
                price = price.replace(' ', '').replace('₽', '')
                ad.update({"price": price.strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            try:
                district = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                district = district[::-1].replace(' ,', ';', 2)[::-1]
                district = district.split(';')[0]
                ad.update({"district": district.strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            try:
                type_ = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text.split(', ')
                if len(type_) == 2:
                    type_ = type_[0]
                    type_ = type_.replace('-', '\\-')
                    ad.update({"type_": type_.strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            try:
                area = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                area = area[::-1].replace(' ,', ';', 2)[::-1]
                area = area.split(';')[-1]
                area = area.replace(',', '\.')
                area = area.replace(' кв. м.', '')
                ad.update({'area': area.strip()})

            except exceptions.NoSuchElementException as e:
                print(e)

            ads.append(ad)
        print()

        try:
            ads = post_parser(driver, ads)

            if EXPERIMENTAL_FLAG:
                ads = parser_egrp(driver, ads)

            return ads

        except exceptions.WebDriverException as e:
            raise exceptions.WebDriverException(e)

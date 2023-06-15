from base64 import b64encode
from random import choice, randint
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
from logging import getLogger

log = getLogger('main.parser')


def sleep_time():
    return randint(3, 5)


def url_builder(filters):
    url = f"https://www.farpost.ru/{ filters.get('city', 'detroit') }" + \
        "/realty/rent_flats/?"

    if filters.get('agentType'):
        url += "".join([f'agentType[]={ e }&' for e in filters.get('agentType')])
    if filters.get('animalsAllowed'):
        url += f"animalsAllowed={ filters.get('animalsAllowed') }&"
    if filters.get('areaTotal_max'):
        url += f"areaTotal_max={ filters.get('areaTotal_max') }&"
    if filters.get('areaTotal_min'):
        url += f"areaTotal_min={ filters.get('areaTotal_min') }&"
    if filters.get('district'):
        url += "".join([f'district[]={ e }&' for e in filters.get('district')])
    if filters.get('flatType'):
        url += "".join([f'flatType[]={ e }&' for e in filters.get('flatType')])
    if filters.get('floor_max'):
        url += f"floor_max={ filters.get('floor_max') }&"
    if filters.get('floor_min'):
        url += f"floor_min={ filters.get('floor_min') }&"
    if filters.get('price_max'):
        url += f"price_max={ filters.get('price_max') }&"
    if filters.get('price_min'):
        url += f"price_min={ filters.get('price_min') }&"
    if filters.get('rentPeriod'):
        url += "".join(
            [f'rentPeriod[]={e}&' for e in filters.get('rentPeriod')])
    if url.endswith('&'):
        url = url[:-1]

    return url


def parser_egrp(driver, ads):
    ok = False
    for ad in ads:
        street = ad['address'][1]
        house = ad['address'][2]
        area = float(ad['area'])
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

            word = 'совпадени'
            n = len(tmp)
            if not (n - 1) % 10:
                word += 'е'
            elif not (n - 2) % 10 or \
                not (n - 3) % 10 or \
                    not (n - 4) % 10:
                word += 'я'
            else:
                word += 'й'

            ad['egrp'] = ad['egrp'].replace(
                'error', f'{ len(tmp) } { word }')

        except (exceptions.TimeoutException,
                exceptions.NoSuchElementException):
            try:
                locator = (By.CSS_SELECTOR,
                           '.alert-warning')
                page = WebDriverWait(driver, 2).until(
                    ec.presence_of_element_located(locator))
                page = page.text

                if 'Ничего не найдено' in page:
                    ad['egrp'] = ad['egrp'].replace('error', 'нет совпадений')

            except exceptions.TimeoutException:
                pass

        ok = True

    if ok:
        log.debug('parser_egrp done')

    return ads


def post_parser(driver, ads):
    ok = False
    for i, ad in enumerate(ads):
        try:
            driver.get(ad['url'])
            sleep(sleep_time())

            driver.find_element(
                By.CSS_SELECTOR, '#grecap-form').text
            log.info('recaptha happened')

            driver.delete_all_cookies()

            ads = ads[:i]
            log.info(f'{ len(ads) - len(ads[:i]) } ads skipped')
            break
        except exceptions.NoSuchElementException as e:
            pass

        try:
            floor = driver.find_element(
                By.CSS_SELECTOR, 'div.bullViewEx:nth-child(1) '
                '> div:nth-child(7) > div:nth-child(1) > '
                'div:nth-child(2) > div:nth-child(2)'
            ).text

            floor = floor.split(sep='-', maxsplit=1,)[0]
            ad.update({'floor': floor.strip()})

        except exceptions.NoSuchElementException:
            log.exception('floor not found')

        try:
            second_price = ''
            second_price = driver.find_element(
                By.CSS_SELECTOR, 'div.viewbull-summary-price__realty-bills'
            ).text

            second_price = second_price.lower()
            second_price = second_price.replace(
                ', иные коммунальные услуги', ' и иные')

            tmp = ''
            if 'свет' in second_price:
                tmp += '💡'
            if 'вода' in second_price:
                tmp += '💧'
            if 'иные' in second_price:
                tmp += '🗿'
            second_price = tmp

            ad.update({'second_price': second_price.strip()})

        except exceptions.NoSuchElementException:
            log.exception('second_price not found')

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

        except exceptions.NoSuchElementException:
            ad.update({'deposit': 'Нет данных'})

        try:
            date = driver.find_element(
                By.CSS_SELECTOR, '.viewbull-actual-date').text
            ad.update({'date': date.strip()})

        except exceptions.NoSuchElementException:
            log.exception('date not found')

        try:
            photos = driver.find_element(
                By.CSS_SELECTOR, '#bulletin > div > div.fieldset > ' +
                'div > div.image-gallery__small-images-grid'
            ).find_elements(By.TAG_NAME, 'img')
            photos = [p.get_attribute('src').replace(
                '_bulletin', '_default'
            ) for p in photos]
            ad.update({'photos': photos})

        except exceptions.NoSuchElementException:
            log.exception('photos not found')

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

        except exceptions.NoSuchElementException:
            log.exception('phones not found')

        ok = True

    if ok:
        log.debug('post_parser done')

    return ads


def parser(config):
    filters = config['filters']

    ok = False

    opts = Options()
    # opts.add_argument('--headless=new')
    opts.add_argument('user-data-dir=./driver_profile/')
    opts.add_argument("start-maximized")
    # opts.add_argument('--disable-blink-features=AutomationControlled')
    # opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    # opts.add_experimental_option('useAutomationExtension', False)

    service = Service('./chromedriver', log_path='/dev/null')

    ads = []
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

        random_domains = ['google.com', 'yandex.ru', 'mail.ru']
        driver.get(f'https://{ choice(random_domains) }/')
        sleep(sleep_time() / 5)
        driver.get('https://www.farpost.ru/help/rules')
        sleep(sleep_time() / 5)

        parser_url = url_builder(filters)
        log.debug(f'parser_url: { parser_url }')
        driver.get(parser_url)
        sleep(sleep_time())

        raw_data = driver.find_element(
            By.CLASS_NAME, 'native').find_elements(By.TAG_NAME, 'td')[1:]

        for raw_ad in raw_data:
            ad = {
                "url": "", "address": [], "price": "",
                "district": "", "type_": "", "area": "",
                "phones": [], "floor": "", "second_price": "",
                "date": "", "deposit": "", "photos": [],
                "egrp": ""
            }

            try:
                driver.find_element(
                    By.CSS_SELECTOR, '#grecap-form')
                log.info('recaptcha happened')

                driver.delete_all_cookies()
                log.info(f'{ len(raw_data) - len(ads) } ads skipped')
                break
            except exceptions.NoSuchElementException as e:
                pass

            try:
                hidden = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'span.private-image-marker__text'
                ).text
                if hidden == 'Скрытое объявление':
                    continue
            except exceptions.NoSuchElementException as e:
                pass

            try:
                url = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    f'''a[href^="/{ filters.get('city', 'detroit') }/realty"]'''
                ).get_attribute('href')
                url = url[:23] + url.split('-')[-1].replace('.html', '')

                ad.update({"url": url.strip()})

            except exceptions.NoSuchElementException:
                log.exception('url not found')

            if ad_exists(ad['url']):
                continue

            try:
                name = raw_ad.find_element(
                    By.CSS_SELECTOR,
                    'a[class$="bull-item__self-link '
                    'auto-shy"]').text

                name = name.split(', ')
                if len(name) >= 2:
                    type_ = name[0].strip()
                    type_ = type_.replace('-комнатная', '-комн.')
                    address = name[1].split()

                    if len(address) >= 3:
                        if len(address) == 4:
                            address = [address[0], ' '.join(
                                address[1:3]), address[3]]
                        elif len(address) == 5:
                            tmp = []

                            address[0] = address[0].replace('Ул', 'улица')
                            tmp.append(address[0])
                            tmp.append(address[1])
                            if [True for word in ['кор.', 'стр.'] if word in address]:
                                tmp.append(' '.join(address[2:5]))
                            else:
                                tmp[1] = tmp[1] + ' ' + ' '.join(address[2:4])
                                tmp.append(address[4])
                            address = [e.strip() for e in tmp]

                ad.update({"type_": type_})
                ad.update({"address": address})

            except exceptions.NoSuchElementException:
                log.exception('name not found')

            try:
                price = raw_ad.find_element(
                    By.CSS_SELECTOR, 'span.price-block__price').text
                price = price.replace(' ', '').replace('₽', '')
                ad.update({"price": price.strip()})

            except exceptions.NoSuchElementException:
                log.exception('price not found')

            try:
                district = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                district = district[::-1].replace(' ,', ';', 2)[::-1]
                district = district.split(';')[0]
                ad.update({"district": district.strip()})

            except exceptions.NoSuchElementException:
                log.exception('district not found')

            try:
                area = raw_ad.find_element(
                    By.CSS_SELECTOR, 'div.bull-item__annotation-row').text
                area = area[::-1].replace(' ,', ';', 2)[::-1]
                area = area.split(';')[-1]
                area = area.replace(',', '.')
                area = area.replace(' кв. м.', '')
                ad.update({'area': area.strip()})

            except exceptions.NoSuchElementException:
                log.exception('area not found')

            ads.append(ad)

        log.debug('parser done')

        try:
            ads = post_parser(driver, ads)

            driver.get('about:blank')

            ads = parser_egrp(driver, ads)

        except exceptions.WebDriverException as e:
            log.exception()

    return ads

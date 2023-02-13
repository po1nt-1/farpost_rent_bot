
import urllib.parse
from time import sleep

from requests import post

from disk import dump_on_disk


def send_message(ads, config):
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']

    queue = {}
    for ad in ads:
        message = ''
        wa_msg = f"Здравствуйте, заинтересовало ваше объявление { ad['url'] }"
        wa_msg = urllib.parse.quote(wa_msg.encode('utf8'))

        highlight = '*'
        x1 = 'INITxSYMx01'
        x2 = 'INITxSYMx02'

        if ad['type_'][0].isdigit():
            spc = '     '
        else:
            spc = '   '

        address = f"{ ad['address'][1] }, { ad['address'][2] }"

        message += f"{ x1 }Создано:{ x1 }    { ad['date'] }\n"
        message += f"{ x1 }Район:{ x1 }        { ad['district'] }\n"
        message += f"{ x1 }{ ad['type_'] }:{ x1 }{ spc }{ address }\n"
        message += f"{ x1 }Цена:{ x1 }          { ad['price'] } руб."
        if ad['second_price']:
            message += f" + { ad['second_price'] }"
        message += "\n"

        message += f"{ x1 }Площадь:{ x1 }  { ad['area'] } кв. м.\n"
        message += f"{ x1 }Кад. ном.:{ x1 }  { x2 }\n"
        message += f'{ x1 }Контакты:{ x1 } '

        for sym in '_][}{)*(~`>#+-=|.!':
            message = message.replace(sym, f'\\{ sym }')
        message = message.replace(x1, highlight)
        message = message.replace(x2, ad['egrp'])

        for phone in ad['phones']:
            message += f"`{phone}` \( [wa](https://wa.me/{ phone }?text={ wa_msg }) \), "
        if message.endswith(', '):
            message = message[:-2]
        message += f"\n"

        message += f'''[Ссылка на объявление]({ ad['url'] })\n'''

        id_ = ad['url'].split('farpost.ru/')[-1]
        queue.update({int(id_): (message, ad)})

    for elem in dict(sorted(queue.items())).values():
        message, ad = elem

        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {
            'chat_id': f'{chat_id}',
            'disable_web_page_preview': 'true',
            'parse_mode': 'MarkdownV2',
            'text': f'{message}'
        }

        attemps = 2
        while attemps > 0:
            response = post(url=url, data=data).json()
            if not response.get("ok", {}):
                if attemps < 2:
                    print("bot/send_message/response:", response)

                if response.get('error_code') == 429:
                    if response.get('parameters').get('retry_after'):
                        sleep(1 + response.get('parameters').get('retry_after'))
                else:
                    sleep(30)
            else:
                dump_on_disk(ad)
                break
            attemps -= 1

        sleep(0.5)

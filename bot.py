
import urllib.parse

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

        address = f"{ ad['address'][0] }, { ad['address'][1] }"

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

        response = post(
            url=f'https://api.telegram.org/bot{token}/sendMessage',
            data={
                'chat_id': f'{chat_id}',
                'disable_web_page_preview': 'true',
                'parse_mode': 'MarkdownV2',
                'text': f'{message}'
            }
        ).json()

        if not response['ok']:
            print(response)
        else:
            dump_on_disk(ad)

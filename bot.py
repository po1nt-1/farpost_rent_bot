from requests import post

from disk import dump_on_disk


def send_message(ads, config):
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']

    for ad in ads:
        message = ''
        wa_msg = f"Здравствуйте, заинтересовало ваше объявление { ad['url'] }"

        message += f"Район: { ad['district'] }\n"
        message += f"{ ad['type_'] }, { ad['address'] }\n"
        message += f"Площадь: { ad['area'] } кв\. м\.\n"
        message += f"Цена: { ad['price'] } руб\."
        message += f" \+ { ad['second_price'] }\n"

        message += 'Контакты: '
        for phone in ad['phones']:
            message += f"`{phone}` \( [wa](https://wa.me/{ phone }?text={ wa_msg }) \), "

        if message.endswith(', '):
            message = message[:-2]

        message += f"\n"
        message += f"Обновлено: { ad['date'] }\n"
        message += f'''[Ссылка на объявление]({ ad['url'] })\n'''

        payload = {
            'chat_id': f'{chat_id}',
            'disable_web_page_preview': 'true',
            'parse_mode': 'MarkdownV2',
            'text': f'{message}'
        }

        response = post(
            url=f'https://api.telegram.org/bot{token}/sendMessage',
            data=payload
        ).json()

        if not response['ok']:
            print(response)
        else:
            dump_on_disk(ad)

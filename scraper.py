import re
from decimal import Decimal
from urllib.request import urlopen

from settings import CBR_URL


def get_data_from_site() -> list:
    """"""
    page = urlopen(CBR_URL)
    html = page.read().decode('utf-8')

    return re.findall(r'<td>(.*)</td>', html)


def get_currency() -> dict:
    """"""
    data = get_data_from_site()

    offset = 0
    total_count = len(data)
    iterations = total_count // 5

    offset_increment = 5
    result = dict()
    for i in range(iterations):
        current_currency = data[offset:offset + offset_increment]
        result[current_currency[1]] = {
            'quantity': int(current_currency[2]),
            'rate': Decimal(current_currency[4].replace(',', '.'))
        }
        offset += offset_increment

    return result

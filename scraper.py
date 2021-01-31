import re
from urllib.request import urlopen

from settings import CBR_URL

page = urlopen(CBR_URL)
html = page.read().decode('utf-8')

data = re.findall(r'<td>(.*)</td>', html)

offset = 0
total_count = len(data)
iterations = total_count // 5

result = dict()
for i in range(iterations):
    current_currency = data[offset:offset + 5]
    result[current_currency[1]] = {
        'quantity': int(current_currency[2]),
        'rate': float(current_currency[4].replace(',', '.'))
    }
    offset += 5

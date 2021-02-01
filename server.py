import json
from decimal import getcontext, ROUND_HALF_UP
from http.server import HTTPServer, BaseHTTPRequestHandler

from scraper import get_currency
from settings import SERVER_ADDRESS


class PostHandler(BaseHTTPRequestHandler):
    """"""
    required_fields = {
        'currency': str,
        'quantity': int,
    }

    def convert_to_rub(self, quantity: int, currency_obj: dict):
        """
        Converts requested currency to rub
        :param quantity:
        :param currency_obj:
        :return:
        """
        currency_rate = currency_obj['rate'] / currency_obj['quantity']
        res = quantity * currency_rate
        return float(res)

    def validate(self, data: dict) -> list:
        """"""
        errors = []

        for field, field_type in self.required_fields.items():
            try:
                value = data[field]
                assert isinstance(value, field_type)
            except KeyError:
                errors.append(f'{field} doesnt exist')
            except AssertionError:
                errors.append(f'{field} isnt type {field_type}')

        return errors

    def get_request(self) -> dict:
        """"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            request = json.loads(post_data)
        except json.JSONDecodeError:
            raise Exception

        return request

    def do_POST(self):
        """"""
        request = self.get_request()

        errors = self.validate(request)
        if errors:
            print(f"\nerrors: {errors}")

        currencies = get_currency()
        currency = currencies.get(request['currency'].upper())
        if currency:
            converted_value = self.convert_to_rub(
                quantity=request['quantity'],
                currency_obj=currency
            )

            status_code = 200
            response = {
                'currency': request['currency'].upper(),
                'requested_value': request['quantity'],
                'converted_value': converted_value
            }
        else:
            status_code = 404
            response = {'error': 'Requested currency does not supported'}

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(json.dumps(response).encode('utf-8'))


if __name__ == '__main__':
    getcontext().prec = 4
    getcontext().rounding = ROUND_HALF_UP

    handler = PostHandler
    httpd = HTTPServer(SERVER_ADDRESS, handler)
    httpd.serve_forever()

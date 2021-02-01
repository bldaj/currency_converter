import json
import typing
from decimal import getcontext, ROUND_HALF_UP
from http.server import HTTPServer, BaseHTTPRequestHandler

from scraper import get_currency
from settings import SERVER_ADDRESS


class CurrencyConverterHandler(BaseHTTPRequestHandler):
    """Converts other currencies to RUB"""
    required_fields = {
        'currency': str,
        'quantity': int,
    }

    def _send_error(self, error: dict, status_code=400) -> None:
        """Sends error response and corresponding headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Connection', 'close')
        self.end_headers()

        self.wfile.write(json.dumps(error).encode('utf-8'))

    def convert_to_rub(self, quantity: int, currency_obj: dict) -> float:
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
        """Validates request"""
        errors = []

        for field, field_type in self.required_fields.items():
            try:
                value = data[field]
                assert isinstance(value, field_type)
            except KeyError:
                errors.append(f"Field '{field}' does not exist")
            except AssertionError:
                errors.append(f"Field '{field}' is not type of {field_type}")

        return errors

    def get_request(self) -> typing.Optional[dict]:
        """Gets request data and converts data to dict"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            request = json.loads(post_data)
        except json.JSONDecodeError:
            return None

        return request

    def do_POST(self) -> None:
        """Handles POST method"""
        request = self.get_request()
        if not request:
            error = {'error': 'Error was occurred during deserializing request data'}
            self._send_error(error)
            return

        errors = self.validate(request)
        if errors:
            error = {
                'error': '. '.join(errors)
            }
            self._send_error(error)
            return

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
            error = {'error': 'Requested currency does not supported'}
            self._send_error(error)
            return

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(json.dumps(response).encode('utf-8'))


if __name__ == '__main__':
    getcontext().prec = 4
    getcontext().rounding = ROUND_HALF_UP

    handler = CurrencyConverterHandler
    httpd = HTTPServer(SERVER_ADDRESS, handler)
    httpd.serve_forever()

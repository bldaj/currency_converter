import json
from http.server import HTTPServer, BaseHTTPRequestHandler

from scraper import get_currency
from settings import SERVER_ADDRESS


class PostHandler(BaseHTTPRequestHandler):
    """"""
    required_fields = {
        'currency': str,
        'quantity': int,
    }

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

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response = {
            'currency': request['currency'],
            'requested_sum': request['quantity'],
            'converted_sum': currencies.get(request['currency']).get('rate')
        }

        self.wfile.write(str(response).encode('utf-8'))


if __name__ == '__main__':
    handler = PostHandler
    httpd = HTTPServer(SERVER_ADDRESS, handler)
    httpd.serve_forever()

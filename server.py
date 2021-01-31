from http.server import HTTPServer, BaseHTTPRequestHandler

from settings import SERVER_ADDRESS


class PostHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)

        print(f"\ndata: {data}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response = {
            'currency': 'abc',
            'requested_sum': 1,
            'converted_sum': 70
        }

        self.wfile.write(str(response).encode('utf-8'))


handler = PostHandler

httpd = HTTPServer(SERVER_ADDRESS, handler)
httpd.serve_forever()

from decimal import Decimal
from http import client, HTTPStatus
from http.server import HTTPServer
import threading
import unittest
from unittest.mock import Mock

import scraper
import server


class TestScrapper(unittest.TestCase):
    """"""

    def setUp(self):
        test_data = ['840', 'USD', '1', 'Доллар США', '75,9051', '978', 'EUR', '1', 'Евро', '91,6250']
        scraper.get_data_from_site = Mock(return_value=test_data)

    def test_getting_currency(self):
        """"""
        expected_result = {
            'USD': {'quantity': 1, 'rate': Decimal('75.9051')},
            'EUR': {'quantity': 1, 'rate': Decimal('91.6250')}
        }
        res = scraper.get_currency()
        self.assertEqual(expected_result, res)


class NoLogRequestHandler:
    def log_message(self, *args):
        # don't write log messages to stderr
        pass

    def read(self, n=None):
        return ''


class TestCurrencyConverterHandler(NoLogRequestHandler, server.CurrencyConverterHandler):
    """Currency handler with disabled logging tp stderr"""
    pass


class TestServerThread(threading.Thread):
    def __init__(self, test_object):
        threading.Thread.__init__(self)
        self.test_object = test_object

    def run(self):
        self.server = HTTPServer(('localhost', 0), TestCurrencyConverterHandler)
        self.test_object.HOST, self.test_object.PORT = self.server.socket.getsockname()
        self.test_object.server_started.set()
        self.test_object = None
        try:
            self.server.serve_forever(0.05)
        finally:
            self.server.server_close()

    def stop(self):
        self.server.shutdown()
        self.join()


class TestCurrencyHandler(unittest.TestCase):

    def setUp(self):
        self.server_started = threading.Event()
        self.thread = TestServerThread(self)
        self.thread.start()
        self.server_started.wait()
        self.con = client.HTTPConnection(self.HOST, self.PORT)
        self.con.connect()

    def tearDown(self):
        self.thread.stop()
        self.thread = None

    def request(self, uri, method='GET', body=None, headers={}):
        self.connection = client.HTTPConnection(self.HOST, self.PORT)
        self.connection.request(method, uri, body, headers)
        return self.connection.getresponse()

    def test_get_not_implemented(self):
        self.con.request('GET', '/')
        res = self.con.getresponse()
        self.assertEqual(res.status, HTTPStatus.NOT_IMPLEMENTED)

    def test_post(self):
        self.con.request('POST', '/')
        res = self.con.getresponse()

        print(f"\nres.read(): {res.read()}")

from decimal import Decimal
from http import client, HTTPStatus
from http.server import HTTPServer
import json
import threading
import unittest
from unittest.mock import Mock

import scraper
import server


class TestScrapper(unittest.TestCase):
    """Tests for scrapper module"""

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
    """Mixin to disable writing log messages to stderr"""

    def log_message(self, *args):
        pass

    def read(self, n=None):
        return ''


class TestCurrencyConverterHandler(NoLogRequestHandler, server.CurrencyConverterHandler):
    """Currency handler with disabled logging tp stderr"""
    pass


class TestServerThread(threading.Thread):
    """Runs test server in a thread"""

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
    """Tests for CurrencyConverterHandler"""

    def setUp(self):
        test_data = ['840', 'USD', '1', 'Доллар США', '75,9051', '978', 'EUR', '1', 'Евро', '91,6250']
        scraper.get_data_from_site = Mock(return_value=test_data)

        self.server_started = threading.Event()
        self.thread = TestServerThread(self)
        self.thread.start()
        self.server_started.wait()
        self.con = client.HTTPConnection(self.HOST, self.PORT)
        self.con.connect()

    def tearDown(self):
        self.thread.stop()
        self.thread = None

    def test_get_not_implemented(self):
        """Tests not implemented GET method"""

        self.con.request('GET', '/')
        res = self.con.getresponse()
        self.assertEqual(res.status, HTTPStatus.NOT_IMPLEMENTED)

    def test_currency_conversion_success(self):
        """Tests currency conversion handler"""

        data = {
            'currency': 'USD',
            'quantity': 1
        }
        self.con.request('POST', '/', body=json.dumps(data))
        res = self.con.getresponse()

        expected_data = json.dumps(
            {
                'currency': 'USD',
                'requested_value': 1,
                'converted_value': 75.9051
            }
        ).encode('utf-8')

        self.assertEqual(res.status, HTTPStatus.OK)
        self.assertEqual(expected_data, res.read())

    def test_currency_conversion_failed(self):
        """Tests CurrencyConverterHandler because of empty request body"""

        self.con.request('POST', '/')
        res = self.con.getresponse()

        expected_data = json.dumps(
            {"error": "Error was occurred during deserializing request data"}
        ).encode('utf-8')
        self.assertEqual(res.status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(expected_data, res.read())

    def test_currency_does_not_supported(self):
        """Tests requested currency does not supported"""

        data = {
            'currency': 'AUD',
            'quantity': 1
        }
        self.con.request('POST', '/', body=json.dumps(data))
        res = self.con.getresponse()

        expected_data = json.dumps(
            {"error": "Requested currency does not supported"}
        ).encode('utf-8')
        self.assertEqual(res.status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(expected_data, res.read())

    def test_validation(self):
        """Tests request params validation"""

        data = {
            'abc': 'USD',
            'quantity': '1'
        }
        self.con.request('POST', '/', body=json.dumps(data))
        res = self.con.getresponse()

        expected_data = json.dumps(
            {'error': "Field 'currency' does not provided. Field 'quantity' is not type of <class 'int'>"}
        ).encode('utf-8')

        self.assertEqual(res.status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(expected_data, res.read())

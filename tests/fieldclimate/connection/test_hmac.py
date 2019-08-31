import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from freezegun import freeze_time
from parameterized import parameterized

from fieldclimate.api import ApiClient
from fieldclimate.connection.hmac import HMAC
from fieldclimate.reqresp import Request


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class TestHMAC(unittest.TestCase):
    public_key = '252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111'
    private_key = 'ce3573a8768586faddc9bb8679749920e34af1e7d0f26d6a7c61fdf298080866'

    def setUp(self):
        self.hmac = HMAC(TestHMAC.public_key, TestHMAC.private_key)
        
    @parameterized.expand([
        ('2012-01-14 12:00:01',
         Request('GET', '', None, {}),
         Request('GET', '', None, {'Date': 'Sat, 14 Jan 2012 12:00:01 GMT',
                                   'Authorization': 'hmac {}:56a8d067766921e916c111af2922e463c38fac054805deb055161f50ece7f905'.format(
                                       public_key)})
         ),
        ('2018-06-14 16:00:01',
         Request('GET', '', None, {}),
         Request('GET', '', None, {'Date': 'Thu, 14 Jun 2018 16:00:01 GMT',
                                   'Authorization': 'hmac {}:3e7cd8eb569d88f8e2b2f57395e9d7e561343472d678a2af746d0dc2307bd30a'.format(
                                       public_key)})
         ),
        ('2016-01-14 00:30:00',
         Request('GET', '', None, {}),
         Request('GET', '', None, {'Date': 'Thu, 14 Jan 2016 00:30:00 GMT',
                                   'Authorization': 'hmac {}:f65e34450718e5b888ac82c5acf2356933ceedf01d0354067154ae83b01eb27c'.format(
                                       public_key)})
         ),
        ('2013-08-25 4:15:15',
         Request('GET', '', None, {}),
         Request('GET', '', None, {'Date': 'Sun, 25 Aug 2013 04:15:15 GMT',
                                   'Authorization': 'hmac {}:29ba7ea768a3039080983acb3d4871a9c86c8475da753ede5a8186d3fa79e663'.format(
                                       public_key)})
         ),
    ])
    def test_modify_request(self, date_stamp, in_request, out_request):
        with freeze_time(date_stamp):
            self.hmac._modify_request(in_request)
            self.assertEqual(in_request, out_request)

    @parameterized.expand([
        ('2012-01-14 12:00:01', 'GET', 'station/info', None,
         {'Accept': 'application/json', 'Date': 'Sat, 14 Jan 2012 12:00:01 GMT',
          'Authorization': 'hmac {}:ca27b4017cb435c690f0724ead14c5a1b795f9fade04a80200bdc9b8cfeb1aef'.format(
              public_key)}),
        ('2018-06-14 16:00:01', 'PUT', 'station/info', None,
         {'Accept': 'application/json', 'Date': 'Thu, 14 Jun 2018 16:00:01 GMT',
          'Authorization': 'hmac {}:b17c593e2e4b20fd9bd04c62630c1bbc7f1a250be5dc5042626603dbf9763097'.format(
              public_key)}),
        ('2016-01-14 00:30:00', 'POST', 'station/info', None,
         {'Accept': 'application/json', 'Date': 'Thu, 14 Jan 2016 00:30:00 GMT',
          'Authorization': 'hmac {}:71ce6b87b40ec1123c096d35ee7012d3ebd8333ddf9cdf44a8faec15dd2e297d'.format(
              public_key)}),
        ('2013-08-25 4:15:15', 'DELETE', 'station/info', None,
         {'Accept': 'application/json', 'Date': 'Sun, 25 Aug 2013 04:15:15 GMT',
          'Authorization': 'hmac {}:a474fe28941e768eb00c4887d04c790d2f23856657748d9c080436c51efc9576'.format(
              public_key)}),
    ])
    def test_make_request(self, date_stamp, method, route, data, headers):
        with freeze_time(date_stamp):
            returned = SimpleNamespace()
            returned.status = 200
            returned.json = AsyncMock(return_value={})
            mock = AsyncMock(return_value=returned)
            self.hmac._session = SimpleNamespace()
            self.hmac._session.request = mock
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.hmac._make_request(method, route, data))
            mock.assert_called_once_with(method, '{}/{}'.format(ApiClient.api_uri, route), json=data, headers=headers)

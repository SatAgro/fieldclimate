import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from parameterized import parameterized

from fieldclimate.api import ApiClient
from fieldclimate.reqresp import Request, ResponseException

from test.support import EnvironmentVarGuard

env = EnvironmentVarGuard()
env.set('FIELDCLIMATE_CLIENT_ID', 'id')
env.set('FIELDCLIMATE_CLIENT_SECRET', 'secret')
with env:
    from fieldclimate.connection.oauth2 import OAuth2, SimpleProvider, client_secret, client_id


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class TestOAuth2(unittest.TestCase):
    auth_code = '41c6596fd58984ece81ae06c8987b4adfa2a411'

    def setUp(self):
        self.env = EnvironmentVarGuard()
        self.env.set('FIELDCLIMATE_CLIENT_ID', 'id')
        self.env.set('FIELDCLIMATE_CLIENT_SECRET', 'secret')
        self.oauth2 = OAuth2(SimpleProvider(TestOAuth2.auth_code))

    @parameterized.expand([
        ('MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3',
         Request('GET', '', None, {}),
         Request('GET', '', None, {'Authorization': 'Authorization: Bearer MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3'})
         ),
    ])
    def test_modify_request(self, access_token, in_request, out_request):
            self.oauth2._access_token = access_token
            self.oauth2._modify_request(in_request)
            self.assertEqual(in_request, out_request)

    @parameterized.expand([
        ('fdb8fdbecf1d03ce5e6125c067733c0d51de209c')
    ])
    def test_get_token_refresh_token(self, refresh_token):
        self.oauth2._refresh_token = refresh_token
        returned = SimpleNamespace()
        returned.status = 200
        returned.json = AsyncMock(return_value={
            'access_token': 'mock_response0',
            'refresh_token': 'mock_response1',
        })
        mock = AsyncMock(return_value=returned)
        self.oauth2._session = SimpleNamespace()
        self.oauth2._session.request = mock
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.oauth2._get_token())
        mock.assert_called_once_with('POST', 'https://oauth.fieldclimate.com/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        })
        self.assertEqual(self.oauth2._access_token, 'mock_response0')
        self.assertEqual(self.oauth2._refresh_token, 'mock_response1')

    def test_get_token_no_refresh_token(self):
        self.oauth2._refresh_token = None
        returned = SimpleNamespace()
        returned.status = 200
        returned.json = AsyncMock(return_value={
            'access_token': 'mock_response0',
            'refresh_token': 'mock_response1',
        })
        mock = AsyncMock(return_value=returned)
        self.oauth2._session = SimpleNamespace()
        self.oauth2._session.request = mock
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.oauth2._get_token())
        mock.assert_called_once_with('POST', 'https://oauth.fieldclimate.com/token', data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': TestOAuth2.auth_code
        })
        self.assertEqual(self.oauth2._access_token, 'mock_response0')
        self.assertEqual(self.oauth2._refresh_token, 'mock_response1')

    @parameterized.expand([
        ('MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3', 'GET', 'station/info', None, {'Accept': 'application/json', 'Authorization': 'Authorization: Bearer MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3'})
    ])
    def test_make_request_access_token(self, access_token, method, route, data, headers):
        self.oauth2._access_token = access_token
        returned = SimpleNamespace()
        returned.status = 200
        returned.json = AsyncMock(return_value={})
        mock = AsyncMock(return_value=returned)
        self.oauth2._session = SimpleNamespace()
        self.oauth2._session.request = mock
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.oauth2._make_request(method, route, data))
        mock.assert_called_once_with(method, '{}/{}'.format(ApiClient.api_uri, route), json=data, headers=headers)

    @parameterized.expand([
        ('MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3', 'GET', 'station/info', None, {'Accept': 'application/json', 'Authorization': 'Authorization: Bearer MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3'})
    ])
    def test_make_request_no_access_token(self, access_token, method, route, data, headers):
        def side_effect():
            self.oauth2._access_token = access_token

        self.oauth2._access_token = None

        returned = SimpleNamespace()
        returned.status = 200
        returned.json = AsyncMock(return_value={})

        mock_request = AsyncMock(return_value=returned)
        self.oauth2._session = SimpleNamespace()
        self.oauth2._session.request = mock_request

        mock_get_token = AsyncMock(side_effect=side_effect)
        self.oauth2._get_token = mock_get_token

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.oauth2._make_request(method, route, data))
        mock_request.assert_called_once_with(method, '{}/{}'.format(ApiClient.api_uri, route), json=data, headers=headers)
        mock_get_token.assert_called_once_with()

    @parameterized.expand([
        ('MTQ0NjJkZmQ5OTM2NDE1ZTZjNGZmZjI3', 'fdb8fdbecf1d03ce5e6125c067733c0d51de209c', 'GET', 'station/info', None, {'Accept': 'application/json', 'Authorization': 'Authorization: Bearer fdb8fdbecf1d03ce5e6125c067733c0d51de209c'})
    ])
    def test_make_request_access_token_expired(self, expired_access_token, access_token, method, route, data, headers):
        def get_token_side_effect():
            self.oauth2._access_token = access_token

        def request_side_effect(*args, **kwargs):
            if self.oauth2._access_token == expired_access_token:
                raise ResponseException(401, {})
            else:
                returned = SimpleNamespace()
                returned.status = 200
                returned.json = AsyncMock(return_value={})
                return returned

        self.oauth2._access_token = expired_access_token

        mock_request = AsyncMock(side_effect=request_side_effect)
        self.oauth2._session = SimpleNamespace()
        self.oauth2._session.request = mock_request

        mock_get_token = AsyncMock(side_effect=get_token_side_effect)
        self.oauth2._get_token = mock_get_token

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.oauth2._make_request(method, route, data))
        mock_request.assert_called_with(method, '{}/{}'.format(ApiClient.api_uri, route), json=data, headers=headers)
        mock_get_token.assert_called_once_with()

import asyncio
import webbrowser
from abc import ABC, abstractmethod

from aiohttp import web

from src.connection.base import ConnectionBase
from src.http.http import ResponseException
from src.tools.tools import get_credentials

credentials = get_credentials()
client_id = credentials['client_id']
client_secret = credentials['client_secret']
auth_url = f'https://oauth.fieldclimate.com/authorize?response_type=code&client_id={client_id}&state=xyz'


class AuthCodeProvider(ABC):

    @abstractmethod
    async def get_auth_code(self):
        pass


class SimpleProvider(AuthCodeProvider):
    def __init__(self, auth_code):
        self._auth_code = auth_code

    async def get_auth_code(self):
        return self._auth_code


class WebBasedProvider(AuthCodeProvider):
    default_port = 5555

    def __init__(self):
        self._port = self.default_port
        self._app = self._make_app()
        self._event = None
        self._auth_code = None

    async def _handle_get(self, request):
        self._auth_code = request.query.get('code', None)
        if self._auth_code is not None:
            self._event.set()
        return web.Response(text=f"Received code {self._auth_code}")

    def _make_app(self):
        app = web.Application()
        app.add_routes([web.get('/', self._handle_get)])
        app.add_routes([web.get('/oauth2/callback', self._handle_get)])
        return app

    async def get_auth_code(self):
        self._event = asyncio.Event()
        loop = asyncio.get_event_loop()
        server = await loop.create_server(self._app.make_handler(), None, self._port)
        webbrowser.open(auth_url)
        await self._event.wait()
        server.close()
        return self._auth_code


class OAuth2(ConnectionBase):
    def __init__(self, auth_code_provider):
        self._auth_code_provider = auth_code_provider
        self._access_token = None
        self._refresh_token = None

    async def _get_token(self):
        if self._refresh_token is not None:
            params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token
            }
        else:
            params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': await self._auth_code_provider.get_auth_code()
            }
        result = await self._session.post('https://oauth.fieldclimate.com/token', data=params)
        response = await result.json(
            content_type=None)
        if result.status >= 300:
            raise ResponseException(result.status, response)
        self._access_token = response['access_token']
        self._refresh_token = response['refresh_token']

    def _modify_request(self, request):
        request.headers['Authorization'] = f'Authorization: Bearer {self._access_token}'

    async def _make_request(self, method, route, body=None):
        if self._access_token is None:
            await self._get_token()
        try:
            response = await super()._make_request(method, route, body)
        except ResponseException as e:
            if e.code == 401:
                await self._get_token()
                response = await super()._make_request(method, route, body)
            else:
                raise
        return response

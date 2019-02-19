from abc import ABC, abstractmethod

import aiohttp

from src.api import ApiClient
from src.reqresp import Response, Request, ResponseException


class ConnectionBase(ABC):

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return ApiClient(self)

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._session.close()

    @abstractmethod
    def _modify_request(self, request):
        pass

    async def _make_request(self, method, route, data=None):
        request = Request(method, route, data, {'Accept': 'application/json'})
        self._modify_request(request)
        result = await self._session.request(method,
                                             '{}/{}'.format(ApiClient.api_uri, request.route),
                                             headers=request.headers,
                                             json=request.data)
        # So that we get None in case of empty server response instead of an exception
        response = await result.json(content_type=None)
        if result.status >= 300:
            raise ResponseException(result.status, response)
        else:
            return Response(result.status, response)

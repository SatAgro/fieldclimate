from abc import ABC, abstractmethod
import asyncio
import aiohttp
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256
from datetime import datetime

class UnauthorizedException(Exception):
    pass
    
class BadRequestException(Exception):
    pass
    
class ConflictException(Exception):
    pass

class ForbiddenException(Exception):
    pass
 
class ServerErrorException(Exception):
    def __init__(self, message):
        self.message = message

class ApiClient:
    apiURI = 'https://api.fieldclimate.com/v1'

    class ClientRoute:
        def __init__(self, client):
            self._client = client
        
        async def _send(self, *args):
            return await self._client._send(*args)
    
    class User(ClientRoute):
        """User routes enables you to manage information regarding user you used to authenticate with."""
        
        async def user_information(self):
            """Reading user information."""
            return await self._send('GET', 'user')
        
        # Czy wolno sprobowac przetestowac te metode? O ile pamietam mielismy pamietac by nie wywolywac metod ktore moga byc destruktywne?
        async def update_user_information(self, user_data):
            """Updating user information."""
            return await self._send('PUT', 'user', user_data)
        
        # Jak testowac te metode??
        async def delete_user_account(self):
            """User himself can remove his own account. """
            return await self._send('DELETE', 'user')
        
        async def list_of_user_devices(self):
            """Reading list of user devices. Returned value may not be used by your application."""
            return await self._send('GET', 'user/stations')
        
        async def list_of_user_licenses(self):
            """Reading all licenses that user has for each of his device."""
            return await self._send('GET', 'user/licenses')
    
    class System(ClientRoute):
        """System routes gives you all information you require to understand the system and what is supported."""
        
        async def system_status(self):
            """Checking system status."""
            return await self._send('GET', 'system/status')
        
        async def list_of_system_sensors(self):
            """Reading the list of all system sensors. Each sensor has unique sensor code and belongs to group with common specifications."""
            return await self._send('GET', 'system/sensors')
        
        async def list_of_system_sensor_groups(self):
            """Reading the list of all system groups. Each sensor belongs to a group which indicates commons specifications."""
            return await self._send('GET', 'system/groups')
        
        async def list_of_groups_and_sensors(self):
            """Reading the list of all system groups and sensors belonging to them. Each sensor belongs to a group which indicates commons specifications."""
            return await self._send('GET', 'system/group/sensors')
        
        async def types_of_devices(self):
            """Reading the list of all devices system supports."""
            return await self._send('GET', 'system/types')
        
        async def system_countries_support(self):
            """Reading the list of all countries that system supports."""
            return await self._send('GET', 'system/countries')
        
        async def system_timezones_support(self):
            """Reading the list of timezones system supports."""
            return await self._send('GET', 'system/timezones')
        
        async def system_diseases_support(self):
            """Reading the list of all disease models system currently supports."""
            return await self._send('GET', 'system/diseases')
    
    class Station(ClientRoute):
        """All the information that is related to your device."""
        
        async def station_information(self, station_id):
            """Reading station information."""
            return await self._send('GET', f'station/{station_id}')
        
        async def update_station_information(self, station_id, station_data):
            """Updating station information/settings."""
            return await self._send('PUT', f'station/{station_id}', station_data)
        
        async def station_sensors(self, station_id):
            """Reading the list of all sensors that your device has/had."""
            return await self._send('GET', f'station/{station_id}/sensors')
        
        async def station_sensor_update(self, station_id, sensor_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', f'station/{station_id}/sensors', sensor_data)
        
        async def station_nodes(self, station_id):
            """Station nodes are wireless nodes connected to base station (STATION-ID). Here you can list custom names if any of a node has custom name."""
            return await self._send('GET', f'station/{station_id}/nodes')
        
        async def change_node_name(self, station_id, node_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', f'station/{station_id}/nodes', node_data)
        
        async def station_serials(self, station_id):
            """Sensor serials settings. If there are no settings we get no content response."""
            return await self._send('GET', f'station/{station_id}/serials')
        
        async def change_serial_name(self, station_id, serial_data):
            """Updating sensor serial information."""
            return await self._send('PUT', f'station/{station_id}/serials')
        
        async def add_station_to_account(self, station_id, station_key, station_data):
            """Adding station to user account. Key 1 and Key 2 are supplied with device itself."""
            return await self._send('POST', f'station/{station_id}/{station_key}', station_data)
        
        async def remove_station_from_account(self, station_id, station_key):
            """Removing station from current account. The keys come with device itself."""
            return await self._send('DELETE', f'station/{station_id}/{station_key}')
        
        async def stations_in_proximity(self, station_id, radius):
            """Find stations in proximity of specified station."""
            return await self._send('GET', f'station/{station_id}/proximity/{radius}')
        
        async def station_last_events(self, station_id, amount, sort=None):
            """Read last X amount of station events. Optionally you can also sort them ASC or DESC."""
            uri = f'station/{station_id}/events/last/{amount}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)
        
        async def station_events_between(self, station_id, from_unix_timestamp, to_unix_timestamp, sort=None):
            """Read station events between time period you select. Optionally you can also sort them ASC or DESC."""
            uri = f'station/{station_id}/events/from/{from_unix_timestamp}/to/{to_unix_timestamp}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)
            
        #TODO: Czy poprawna składnia URI jeśli nie ma filter
        async def station_transmission_history_last(self, station_id, amount, filter_=None, sort=None):
            """Read last X amount of station transmission history. Optionally you can also sort them ASC or DESC and filter."""
            uri = f'station/{station_id}/history'
            if filter_ is not None:
                uri = uri + f'/{filter_}'
            uri = uri + f'/{last}/{amount}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)
        
        async def station_transmission_history_between(self, station_id, from_unix_timestamp, to_unix_timestamp, filter_=None, sort=None):
            """Read transmission history for specific time period. Optionally you can also sort them ASC or DESC and filter."""
            uri = f'station/{station_id}/history/'
            if filter_ is not None:
                uri = uri + f'/{filter_}'
            uri = uri + f'/from/{from_unix_timestamp}/to/{to_unix_timestamp}'
            if sort is not None:
                uri = uri + f'/{sort}'
            return await self._send('GET', uri)
        
        async def station_licenses(self, station_id):
            """Retrieve all the licenses of your device. They are separated by the service (models, forecast ...)."""
            return await self._send('GET', f'station/{station_id}/licenses')
        
     
    def __init__(self, auth):
        self._auth = auth
    
    async def _send(self, *args):
        resp = await self._auth._make_request(*args)
        return resp
    
    @property
    def user(self):
        return ApiClient.User(self)
    
    @property
    def system(self):
        return ApiClient.System(self)
    
    @property
    def station(self):
        return ApiClient.Station(self)
    

class ClientBuilder:

    class _RequestContents:
        def __init__(self, method, route, body, headers):
            self.method = method
            self.route = route
            self.headers = headers
            self.body = body
    
    class _ConnectionBase(ABC):
    
        async def __aenter__(self):
            self._session = aiohttp.ClientSession()
            return ApiClient(self)
        
        async def __aexit__(self, exc_type, exc_value, traceback):
            await self._session.close()
            
        @abstractmethod
        def _modify_request(self, requestContents):
            pass
        
        async def _make_request(self, method, route, body=None):
            requestContents = ClientBuilder._RequestContents(method, route, body, {'Accept': 'application/json'})
            self._modify_request(requestContents)
            
            args = [ApiClient.apiURI+'/'+requestContents.route]
            kwargs = {'headers': requestContents.headers}
            if requestContents.body is not None:
                kwargs['json'] = body
            
            result = await self._session.request(method, *args, **kwargs)
            if result.status == 400:
                raise BadRequestException()
            if result.status == 401:
                raise UnauthorizedException()
            if result.status == 403:
                raise ForbiddenException()
            if result.status == 409:
                raise ConflictException()
            if result.status == 500:
                error_message = await result.text()
                raise ServerErrorException(error_message)
            
            if result.status == 200:
                success = True
            if result.status == 204:
                success = False
            response = await result.json(content_type=None) # Chodzi o to, by zwrocilo None gdy odp serwera jest pusta a nie rzucalo wyjatkiem
            return {'success': success, 'response': response}
            

    class HMAC(_ConnectionBase):
        
        def __init__(self, publicKey, privateKey):
            self._publicKey = publicKey
            self._privateKey = privateKey
        
        def _modify_request(self, requestContents):
            dateStamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            requestContents.headers['Date'] = dateStamp
            msg = (requestContents.method + '/' + requestContents.route + dateStamp + self._publicKey).encode(encoding='utf-8')
            h = HMAC.new(self._privateKey.encode(encoding='utf-8'), msg, SHA256)
            signature = h.hexdigest()
            requestContents.headers['Authorization'] = 'hmac ' + self._publicKey + ':' + signature
    
    class OAuth2(_ConnectionBase):
        pass # Zdaje sie ze bedzie musialo zoverride'owac __aenter__?

# Usage example:
async def trivialTest():
    async with ClientBuilder.HMAC('', '') as client:
        user = await client.user.list_of_user_devices()
        print(user)

def runTrivialTest():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(trivialTest())

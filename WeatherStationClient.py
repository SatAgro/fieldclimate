from abc import ABC, abstractmethod
from datetime import datetime

import aiohttp
import pkg_resources
import yaml
from Crypto.Hash import HMAC
from Crypto.Hash import SHA256


def get_credentials():
    return yaml.load(pkg_resources.resource_stream(__name__, 'credentials.yml'))


class ApiResponseException(Exception):
    def __init__(self, code, response):
        self.code = code
        # Better safe than sorry? If the server returns a non-empty response with code >= 300 we should preserve it
        self.response = response


class ApiAuthorizationException(ApiResponseException):
    pass


class ApiResponse:
    def __init__(self, code, response):
        self.code = code
        self.response = response


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

        # Are we allowed to try and test this method?
        # IIRC we had to remember not to call destructive methods?
        async def update_user_information(self, user_data):
            """Updating user information."""
            return await self._send('PUT', 'user', user_data)

        # How to test this method??
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
            """Reading the list of all system sensors. Each sensor has unique sensor code and belongs to group with
            common specifications. """
            return await self._send('GET', 'system/sensors')

        async def list_of_system_sensor_groups(self):
            """Reading the list of all system groups. Each sensor belongs to a group which indicates commons
            specifications. """
            return await self._send('GET', 'system/groups')

        async def list_of_groups_and_sensors(self):
            """Reading the list of all system groups and sensors belonging to them. Each sensor belongs to a group
            which indicates commons specifications. """
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
            return await self._send('GET', 'station/{}'.format(station_id))

        async def update_station_information(self, station_id, station_data):
            """Updating station information/settings."""
            return await self._send('PUT', 'station/{}'.format(station_id), station_data)

        async def station_sensors(self, station_id):
            """Reading the list of all sensors that your device has/had."""
            return await self._send('GET', 'station/{}/sensors'.format(station_id))

        async def station_sensor_update(self, station_id, sensor_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', 'station/{}/sensors'.format(station_id), sensor_data)

        async def station_nodes(self, station_id):
            """Station nodes are wireless nodes connected to base station (station_id). Here you can list custom
            names if any of a node has custom name. """
            return await self._send('GET', 'station/{}/nodes'.format(station_id))

        async def change_node_name(self, station_id, node_data):
            """Updating station sensor name, unit ..."""
            return await self._send('PUT', 'station/{}/nodes'.format(station_id), node_data)

        async def station_serials(self, station_id):
            """Sensor serials settings. If there are no settings we get no content response."""
            return await self._send('GET', 'station/{}/serials'.format(station_id))

        async def change_serial_name(self, station_id, serial_data):
            """Updating sensor serial information."""
            return await self._send('PUT', 'station/{}/serials'.format(station_id), serial_data)

        async def add_station_to_account(self, station_id, station_key, station_data):
            """Adding station to user account. Key 1 and Key 2 are supplied with device itself."""
            return await self._send('POST', 'station/{}/{}'.format(station_id, station_key), station_data)

        async def remove_station_from_account(self, station_id, station_key):
            """Removing station from current account. The keys come with device itself."""
            return await self._send('DELETE','station/{}/{}'.format(station_id, station_key))

        async def stations_in_proximity(self, station_id, radius):
            """Find stations in proximity of specified station."""
            return await self._send('GET', 'station/{}/proximity/{}'.format(station_id, radius))

        async def station_last_events(self, station_id, amount, sort=None):
            """Read last X amount of station events. Optionally you can also sort them ASC or DESC."""
            uri = 'station/{}/events/last/{}'.format(station_id, amount)
            if sort is not None:
                uri = uri + '/{}'.format(sort)
            return await self._send('GET', uri)

        async def station_events_between(self, station_id, from_unix_timestamp, to_unix_timestamp, sort=None):
            """Read station events between time period you select. Optionally you can also sort them ASC or DESC."""
            uri = 'station/{}/events/from/{}/to/{}'.format(station_id, from_unix_timestamp, to_unix_timestamp)
            if sort is not None:
                uri = uri + '/{}'.format(sort)
            return await self._send('GET', uri)

        async def station_transmission_history_last(self, station_id, amount, filter=None, sort=None):
            """Read last X amount of station transmission history. Optionally you can also sort them ASC or DESC and
            filter. """
            uri = 'station/{}/history'.format(station_id)
            if filter is not None:
                uri = uri + '/{}'.format(filter)
            uri = uri + '/last/{}'.format(amount)
            if sort is not None:
                uri = uri + '/{}'.format(sort)
            return await self._send('GET', uri)

        async def station_transmission_history_between(self, station_id, from_unix_timestamp, to_unix_timestamp,
                                                       filter=None, sort=None):
            """Read transmission history for specific time period. Optionally you can also sort them ASC or DESC and
            filter. """
            uri = 'station/{}/history'.format(station_id)
            if filter is not None:
                uri = uri + '/{}'.format(filter)
            uri = uri + '/from/{}/to/{}'.format(from_unix_timestamp, to_unix_timestamp)
            if sort is not None:
                uri = uri + '/{}'.format(sort)
            return await self._send('GET', uri)

        async def station_licenses(self, station_id):
            """Retrieve all the licenses of your device. They are separated by the service (models, forecast ...)."""
            return await self._send('GET', 'station/{}/licenses'.format(station_id))

    class Data(ClientRoute):

        async def min_max_date_of_data(self, station_id):
            """Retrieve min and max date of device data availability."""
            return await self._send('GET', 'data/{}'.format(station_id))

        async def get_last_data(self, station_id, data_group, time_period, format=None):
            """Retrieve last data that device sends."""
            if format is not None:
                uri = 'data/{}/{}/{}/last/{}'.format(format, station_id, data_group, time_period)
            else:
                uri = 'data/{}/{}/last/{}'.format(station_id, data_group, time_period)
            return await self._send('GET', uri)

        async def get_data_between_period(self, station_id, data_group, from_unix_timestamp, to_unix_timestamp=None,
                                          format=None):
            """Retrieve data between specified time periods."""
            if format is not None:
                uri = 'data/{}/{}/{}/from/{}'.format(format, station_id, data_group, from_unix_timestamp)
            else:
                uri = 'data/{}/{}/from/{}'.format(station_id, data_group, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('GET', uri)

        async def get_last_data_customized(self, station_id, data_group, time_period, custom_data, format=None):
            """Retrieve last data that device sends in your liking."""
            if format is not None:
                uri = 'data/{}/{}/{}/last/{}'.format(format, station_id, data_group, time_period)
            else:
                uri = 'data/{}/{}/last/{}'.format(station_id, data_group, time_period)
            return await self._send('POST', uri, custom_data)

        async def get_data_between_period_customized(self, station_id, data_group, from_unix_timestamp, custom_data,
                                                     to_unix_timestamp=None, format=None):
            """Retrieve data between specified time periods in your liking."""
            if format is not None:
                uri = 'data/{}/{}/{}/from/{}'.format(format, station_id, data_group, from_unix_timestamp)
            else:
                uri = 'data/{}/{}/from/{}'.format(station_id, data_group, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('POST', uri, custom_data)

    class Forecast(ClientRoute):

        async def get_forecast_data(self, station_id, forecast_option):
            """Retrieving forecast from your device."""
            return await self._send('GET', 'forecast/{}/{}'.format(station_id, forecast_option))

        async def get_forecast_image(self, station_id, forecast_option):
            """Getting forecast image."""
            return await self._send('GET', 'forecast/{}/{}'.format(station_id, forecast_option))

    class Disease(ClientRoute):

        async def get_last_eto(self, station_id, time_period):
            """Retrieve last Evapotranspiration."""
            return await self._send('GET', 'disease/{}/last/{}'.format(station_id, time_period))

        async def get_eto_between(self, station_id, from_unix_timestamp, to_unix_timestamp=None):
            """Retrieve Evapotranspiration data between specified time periods."""
            uri = 'disease/{}/from/{}'.format(station_id, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('GET', uri)

        async def get_last_disease(self, station_id, time_period, disease_data):
            """Retrieve last disease model data or calculation."""
            return await self._send('POST', 'disease/{}/last/{}'.format(station_id, time_period), disease_data)

        async def get_disease_between(self, station_id, from_unix_timestamp, disease_data, to_unix_timestamp=None):
            """Retrieve disease model data or calculation between specified time periods."""
            uri = 'disease/{}/from/{}'.format(station_id, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('POST', uri, disease_data)

    class Dev(ClientRoute):

        async def list_of_applications(self):
            """Reading the list of applications."""
            return await self._send('GET', 'dev/applications')

        async def application_users(self, app_id):
            """Reading list users in the specified application."""
            return await self._send('GET', 'dev/users/{}'.format(app_id))

        async def application_stations(self, app_id):
            """Reading list of station in the Application."""
            return await self._send('GET', 'dev/stations/{}'.format(app_id))

        async def user_stations(self, user_id):
            """Reading list of station in the Application."""
            return await self._send('GET', 'dev/user/{}/stations'.format(user_id))

        async def add_station_to_user(self, username, station_id, station_key, station_data):
            """Adding station to user account that belongs to your application."""
            return await self._send('POST', 'dev/user/{}/{}/{}'.format(username, station_id, station_key), station_data)

        async def remove_station_from_user(self, username, station_id):
            """Removing station from account that belongs to your application."""
            return await self._send('DELETE', 'dev/user/{}/{}'.format(username, station_id))

        async def register_user_to_application(self, app_id, user_data):
            """Register a new user to your application."""
            return await self._send('POST', 'dev/user/{}'.format(app_id), user_data)

        async def activate_registered_user_account(self, activation_key):
            """Activate registered user account."""
            return await self._send('GET', 'dev/user/activate/{}'.format(activation_key))

        async def new_password_request(self, app_id, password_data):
            """Requesting application to change password of a user that belongs to your application."""
            return await self._send('POST', 'dev/user/{}/password-reset'.format(app_id), password_data)

        async def setting_new_password(self, app_id, password_key, password_data):
            """Changing password of user account."""
            return await self._send('POST', 'dev/user/{}/password-update/{}'.format(app_id, password_key), password_data)

    class Chart(ClientRoute):

        async def charting_last_data(self, station_id, data_group, time_period, type=None):
            """Retrieve chart from last data that device sends."""
            if type is not None:
                uri = 'chart/{}/{}/{}/last/{}'.format(type, station_id, data_group, time_period)
            else:
                uri = 'chart/{}/{}/last/{}'.format(station_id, data_group, time_period)
            return await self._send('GET', uri)

        async def charting_period(self, station_id, data_group, from_unix_timestamp, to_unix_timestamp=None, type=None):
            """Charting data between specified time periods."""
            if type is not None:
                uri = 'chart/{}/{}/{}/from/{}'.format(type, station_id, data_group, from_unix_timestamp)
            else:
                uri = 'chart/{}/{}/from/{}'.format(station_id, data_group, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('GET', uri)

        async def charting_last_data_customized(self, station_id, data_group, time_period, custom_data, type=None):
            """Retrieve customized chart from last data that device sends."""
            if type is not None:
                uri = 'chart/{}/{}/{}/last/{}'.format(type, station_id, data_group, time_period)
            else:
                uri = 'chart/{}/{}/last/{}'.format(station_id, data_group, time_period)
            return await self._send('POST', uri, custom_data)

        async def charting_period_data_customized(self, station_id, data_group, from_unix_timestamp, custom_data,
                                                  to_unix_timestamp=None, type=None):
            """Charting customized data between specified time periods."""
            if type is not None:
                uri = 'chart/{}/{}/{}/from/{}'.format(type, station_id, data_group, from_unix_timestamp)
            else:
                uri = 'chart/{}/{}/from/{}'.format(station_id, data_group, from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            return await self._send('POST', uri, custom_data)

    class Cameras(ClientRoute):

        async def min_max_date_of_data(self, station_id):
            """Retrieve min and max date of device data availability."""
            return await self._send('GET', 'camera/{}/photos/info'.format(station_id))

        async def get_last_photos(self, station_id, amount, camera=None):
            """Retrieve last data that device sends."""
            uri = 'camera/{}/photos/last/{}'.format(station_id, amount)
            if camera is not None:
                uri += '/{}'.format(camera)
            return await self._send('GET', uri)

        async def get_photos_between_period(self, station_id, from_unix_timestamp=None, to_unix_timestamp=None,
                                            camera=None):
            """Retrieve photos between specified period that device sends."""
            uri = 'camera/{}/photos'.format(station_id)
            if from_unix_timestamp is not None:
                uri += '/from/{}'.format(from_unix_timestamp)
            if to_unix_timestamp is not None:
                uri += '/to/{}'.format(to_unix_timestamp)
            if camera is not None:
                uri += '/{}'.format(camera)
            return await self._send('GET', uri)

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

    @property
    def data(self):
        return ApiClient.Data(self)

    @property
    def forecast(self):
        return ApiClient.Forecast(self)

    @property
    def disease(self):
        return ApiClient.Disease(self)

    @property
    def dev(self):
        return ApiClient.Dev(self)

    @property
    def chart(self):
        return ApiClient.Chart(self)

    @property
    def cameras(self):
        return ApiClient.Cameras(self)


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
        def _modify_request(self, request_contents):
            pass

        async def _make_request(self, method, route, body=None):
            request_contents = ClientBuilder._RequestContents(method, route, body, {'Accept': 'application/json'})
            self._modify_request(request_contents)

            args = [ApiClient.apiURI + '/' + request_contents.route]
            kwargs = {'headers': request_contents.headers}
            if request_contents.body is not None:
                kwargs['json'] = body

            result = await self._session.request(method, *args, **kwargs)
            response = await result.json(
                content_type=None)  # So that we get None in case of empty server response instead of an exception

            if result.status >= 300:
                raise ApiResponseException(result.status, response)
            else:
                return ApiResponse(result.status, response)

    class HMAC(_ConnectionBase):

        def __init__(self, public_key, private_key):
            self._publicKey = public_key
            self._privateKey = private_key

        def _modify_request(self, request_contents):
            date_stamp = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            request_contents.headers['Date'] = date_stamp
            msg = '{}/{}{}{}'.format(request_contents.method, request_contents.route, date_stamp, self._publicKey).encode(
                encoding='utf-8')
            h = HMAC.new(self._privateKey.encode(encoding='utf-8'), msg, SHA256)
            signature = h.hexdigest()
            request_contents.headers['Authorization'] = 'hmac {}:{}'.format(self._publicKey, signature)

    class OAuth2(_ConnectionBase):

        credentials = get_credentials()
        client_id = credentials['client_id']
        client_secret = credentials['client_secret']

        def __init__(self, authorization_code):
            self._authorization_code = authorization_code
            self._access_token = None
            self._refresh_token = None

        async def _get_token(self):
            if self._refresh_token is not None:
                params = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': self._refresh_token
                }
            else:
                params = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'authorization_code',
                    'code': self._authorization_code
                }
            response = await self._session.post('https://oauth.fieldclimate.com/token', data=params)
            result = await response.json(
                content_type=None)
            if response.status >= 300:
                raise ApiAuthorizationException(response.status, result)
            self._access_token = result['access_token']
            self._refresh_token = result['refresh_token']

        def _modify_request(self, request_contents):
            request_contents.headers['Authorization'] = 'Authorization: Bearer {}'.format(self._access_token)

        async def _make_request(self, method, route, body=None):
            if self._access_token is None:
                await self._get_token()
            try:
                response = await super()._make_request(method, route, body)
            except ApiResponseException as e:
                if e.code == 401:
                    await self._get_token()
                    response = await super()._make_request(method, route, body)
                else:
                    raise
            return response

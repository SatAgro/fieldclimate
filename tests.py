import asyncio
import unittest

from WeatherStationClient import ClientBuilder, ApiClient


class MockSession:
    class MockResponse:
        def __init__(self, method, url, json, headers):
            self.method = method
            self.url = url
            self.body = json
            self.headers = headers
            self.status = 200

        async def json(self, content_type=None):
            return vars(self)

    async def request(self, method, url, json=None, headers=None):
        return MockSession.MockResponse(method, url, json, headers)


class MockConnection(ClientBuilder._ConnectionBase):
    async def __aenter__(self):
        self._session = MockSession()
        return ApiClient(self)

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    def _modify_request(self, requestContents):
        pass


class TestApiCalls(unittest.TestCase):

    @property
    def some_data(self):
        return {'foo': 1, 'bar': 'two'}

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        self.assertEqual(mock_response['method'], expected_method)
        self.assertEqual(mock_response['url'], f'{ApiClient.apiURI}/{expected_route}')
        self.assertEqual(mock_response['body'], expected_body)
        self.assertEqual(mock_response['headers'], {'Accept': 'application/json'})

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        # Jesli tego nie zawołam, 14. w kolejnosci test (a nie inny??) rzuci warningiem ze unclosed event loop
        # TODO: Uczciwie przyznaje: nie wiem, dlaczego
        self.loop.close()

    async def get_response(self, section, method, *args, **kwargs):
        async with MockConnection() as client:
            section_obj = getattr(client, section)
            method_obj = getattr(section_obj, method)
            result = await method_obj(*args, **kwargs)
            return result.response

    def call(self, section, method, *args, **kwargs):
        return self.loop.run_until_complete(self.get_response(section, method, *args, **kwargs))


class TestUserCalls(TestApiCalls):
    def call(self, method, *args, **kwargs):
        return super().call('user', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'user' + expected_route, expected_body)

    def test_user_information(self):
        self.assertCall(self.call('user_information'), 'GET', '')

    def test_update_user_information(self):
        self.assertCall(self.call('update_user_information', self.some_data), 'PUT', '', self.some_data)

    def test_delete_user_account(self):
        self.assertCall(self.call('delete_user_account'), 'DELETE', '')

    def test_list_of_user_devices(self):
        self.assertCall(self.call('list_of_user_devices'), 'GET', '/stations')

    def test_list_of_user_licenses(self):
        self.assertCall(self.call('list_of_user_licenses'), 'GET', '/licenses')


class TestSystemCalls(TestApiCalls):
    def call(self, method, *args, **kwargs):
        return super().call('system', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'system' + expected_route, expected_body)

    def test_system_status(self):
        self.assertCall(self.call('system_status'), 'GET', '/status')

    def test_list_of_system_sensors(self):
        self.assertCall(self.call('list_of_system_sensors'), 'GET', '/sensors')

    def test_list_of_system_sensor_groups(self):
        self.assertCall(self.call('list_of_system_sensor_groups'), 'GET', '/groups')

    def test_list_of_groups_and_sensors(self):
        self.assertCall(self.call('list_of_groups_and_sensors'), 'GET', '/group/sensors')

    def test_types_of_devices(self):
        self.assertCall(self.call('types_of_devices'), 'GET', '/types')

    def test_system_countries_support(self):
        self.assertCall(self.call('system_countries_support'), 'GET', '/countries')

    def test_system_timezones_support(self):
        self.assertCall(self.call('system_timezones_support'), 'GET', '/timezones')

    def test_system_diseases_support(self):
        self.assertCall(self.call('system_diseases_support'), 'GET', '/diseases')


class TestStationCalls(TestApiCalls):
    def call(self, method, *args, **kwargs):
        return super().call('station', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'station' + expected_route, expected_body)

    def test_station_information(self):
        self.assertCall(self.call('station_information', 'station-id'), 'GET', '/station-id')

    def test_update_station_information(self):
        self.assertCall(self.call('update_station_information', 'station-id', self.some_data), 'PUT', '/station-id',
                        self.some_data)

    def test_station_sensors(self):
        self.assertCall(self.call('station_sensors', 'station-id'), 'GET', '/station-id/sensors')

    def test_station_sensor_update(self):
        self.assertCall(self.call('station_sensor_update', 'station-id', self.some_data), 'PUT', '/station-id/sensors',
                        self.some_data)

    def test_station_nodes(self):
        self.assertCall(self.call('station_nodes', 'station-id'), 'GET', '/station-id/nodes')

    def test_change_node_name(self):
        self.assertCall(self.call('change_node_name', 'station-id', self.some_data), 'PUT', '/station-id/nodes',
                        self.some_data)

    def test_station_serials(self):
        self.assertCall(self.call('station_serials', 'station-id'), 'GET', '/station-id/serials')

    def test_change_serial_name(self):
        self.assertCall(self.call('change_serial_name', 'station-id', self.some_data), 'PUT', '/station-id/serials',
                        self.some_data)

    def test_add_station_to_account(self):
        self.assertCall(self.call('add_station_to_account', 'station-id', 'station-key', self.some_data), 'POST',
                        '/station-id/station-key', self.some_data)

    def test_remove_station_from_account(self):
        self.assertCall(self.call('remove_station_from_account', 'station-id', 'station-key'), 'DELETE',
                        '/station-id/station-key')

    def test_stations_in_proximity(self):
        self.assertCall(self.call('stations_in_proximity', 'station-id', '5m'), 'GET', '/station-id/proximity/5m')

    def test_station_last_events(self):
        self.assertCall(self.call('station_last_events', 'station-id', 5), 'GET', '/station-id/events/last/5')

    def test_station_last_events_sorted(self):
        self.assertCall(self.call('station_last_events', 'station-id', 5, 'asc'), 'GET',
                        '/station-id/events/last/5/asc')

    def test_station_events_between(self):
        self.assertCall(self.call('station_events_between', 'station-id', 1543524622, 1543524623), 'GET',
                        '/station-id/events/from/1543524622/to/1543524623')

    def test_station_events_between_sorted(self):
        self.assertCall(self.call('station_events_between', 'station-id', 1543524622, 1543524623, 'asc'), 'GET',
                        '/station-id/events/from/1543524622/to/1543524623/asc')

    def test_station_transmission_history_last(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5), 'GET',
                        '/station-id/history/last/5')

    def test_station_transmission_history_last_sorted(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, sort='asc'), 'GET',
                        '/station-id/history/last/5/asc')

    def test_station_transmission_history_last_filtered(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, filter='resync'), 'GET',
                        '/station-id/history/resync/last/5')

    def test_station_transmission_history_last_filtered_sorted(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, 'resync', 'asc'), 'GET',
                        '/station-id/history/resync/last/5/asc')

    def test_station_transmission_history_between(self):
        self.assertCall(self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623), 'GET',
                        '/station-id/history/from/1543524622/to/1543524623')

    def test_station_transmission_history_between_sorted(self):
        self.assertCall(
            self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, sort='asc'), 'GET',
            '/station-id/history/from/1543524622/to/1543524623/asc')

    def test_station_transmission_history_between_filtered(self):
        self.assertCall(
            self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, 'resync'), 'GET',
            '/station-id/history/resync/from/1543524622/to/1543524623')

    def test_station_transmission_history_between_filtered_sorted(self):
        self.assertCall(
            self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, 'resync', 'asc'),
            'GET', '/station-id/history/resync/from/1543524622/to/1543524623/asc')

    def test_station_licenses(self):
        self.assertCall(self.call('station_licenses', 'station-id'), 'GET', '/station-id/licenses')


class TestDataCalls(TestApiCalls):

    @property
    def some_data(self):
        return {'foo': 1, 'bar': 'two'}

    def call(self, method, *args, **kwargs):
        return super().call('data', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'data' + expected_route, expected_body)

    def test_min_max_date_of_data(self):
        self.assertCall(self.call('min_max_date_of_data', 'station-id'), 'GET', '/station-id')

    def test_get_last_data(self):
        self.assertCall(self.call('get_last_data', 'station-id', 'raw', 5, 'image'), 'GET',
                        '/image/station-id/raw/last/5')
        self.assertCall(self.call('get_last_data', 'station-id', 'raw', 5), 'GET', '/station-id/raw/last/5')

    def test_get_data_between_period(self):
        self.assertCall(self.call('get_data_between_period', 'station-id', 'raw', 1543524622), 'GET',
                        '/station-id/raw/from/1543524622')
        self.assertCall(self.call('get_data_between_period', 'station-id', 'raw', 1543524622, 1543524622), 'GET',
                        '/station-id/raw/from/1543524622/to/1543524622')
        self.assertCall(self.call('get_data_between_period', 'station-id', 'raw', 1543524622, None, 'image'), 'GET',
                        '/image/station-id/raw/from/1543524622')

    def test_get_last_data_customized(self):
        self.assertCall(self.call('get_last_data_customized', 'station-id', 'raw', 5, self.some_data, 'normal'),
                        'POST', '/normal/station-id/raw/last/5', self.some_data)
        self.assertCall(self.call('get_last_data_customized', 'station-id', 'raw', 5, self.some_data), 'POST',
                        '/station-id/raw/last/5', self.some_data)

    def test_get_data_between_period_customized(self):
        self.assertCall(
            self.call('get_data_between_period_customized', 'station-id', 'raw', 1543524622, self.some_data),
            'POST', '/station-id/raw/from/1543524622', self.some_data)
        self.assertCall(
            self.call('get_data_between_period_customized', 'station-id', 'raw', 1543524622, self.some_data,
                      1543524622),
            'POST', '/station-id/raw/from/1543524622/to/1543524622', self.some_data)
        self.assertCall(
            self.call('get_data_between_period_customized', 'station-id', 'raw', 1543524622, self.some_data, None,
                      'normal'), 'POST', '/normal/station-id/raw/from/1543524622', self.some_data)


class TestForecastCalls(TestApiCalls):

    def call(self, method, *args, **kwargs):
        return super().call('forecast', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'forecast' + expected_route, expected_body)

    def test_get_forecast_data(self):
        self.assertCall(self.call('get_forecast_data', 'station-id', 'basic-1h'), 'GET', '/station-id/basic-1h')

    def test_get_forecast_image(self):
        self.assertCall(self.call('get_forecast_image', 'station-id', 'pictoprint'), 'GET', '/station-id/pictoprint')


class TestDiseaseCalls(TestApiCalls):

    @property
    def some_data(self):
        return {'foo': 1, 'bar': 'two'}

    def call(self, method, *args, **kwargs):
        return super().call('disease', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'disease' + expected_route, expected_body)

    def test_get_last_eto(self):
        self.assertCall(self.call('get_last_eto', 'station-id', 5), 'GET', '/station-id/last/5')

    def test_get_eto_between(self):
        self.assertCall(self.call('get_eto_between', 'station-id', 1543524622), 'GET', '/station-id/from/1543524622')
        self.assertCall(self.call('get_eto_between', 'station-id', 1543524622, 1543524622), 'GET',
                        '/station-id/from/1543524622/to/1543524622')

    def test_get_last_disease(self):
        self.assertCall(self.call('get_last_disease', 'station-id', 5, self.some_data), 'POST', '/station-id/last/5',
                        self.some_data)

    def test_get_disease_between(self):
        self.assertCall(self.call('get_disease_between', 'station-id', 1543524622, self.some_data), 'POST',
                        '/station-id/from/1543524622', self.some_data)
        self.assertCall(self.call('get_disease_between', 'station-id', 1543524622, self.some_data, 1543524622), 'POST',
                        '/station-id/from/1543524622/to/1543524622', self.some_data)


class TestDevCalls(TestApiCalls):

    @property
    def some_data(self):
        return {'foo': 1, 'bar': 'two'}

    def call(self, method, *args, **kwargs):
        return super().call('dev', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'dev' + expected_route, expected_body)

    def test_list_of_applications(self):
        self.assertCall(self.call('list_of_applications'), 'GET', '/applications')

    def test_application_users(self):
        self.assertCall(self.call('application_users', 'app-id'), 'GET', '/users/app-id')

    def test_application_stations(self):
        self.assertCall(self.call('application_stations', 'app-id'), 'GET', '/stations/app-id')

    def test_user_stations(self):
        self.assertCall(self.call('user_stations', 'user-id'), 'GET', '/user/user-id/stations')

    def test_add_station_to_user(self):
        self.assertCall(self.call('add_station_to_user', 'username', 'station-id', 'station-key', self.some_data),
                        'POST', '/user/username/station-id/station-key', self.some_data)

    def test_remove_station_from_user(self):
        self.assertCall(self.call('remove_station_from_user', 'username', 'station-id'), 'DELETE',
                        '/user/username/station-id')

    def test_register_user_to_application(self):
        self.assertCall(self.call('register_user_to_application', 'app-id', self.some_data), 'POST', '/user/app-id',
                        self.some_data)

    def test_activate_registered_user_account(self):
        self.assertCall(self.call('activate_registered_user_account', 'activation-key'), 'GET',
                        '/user/activate/activation-key')

    def test_new_password_request(self):
        self.assertCall(self.call('new_password_request', 'app-id', self.some_data), 'POST',
                        '/user/app-id/password-reset', self.some_data)

    def test_setting_new_password(self):
        self.assertCall(self.call('setting_new_password', 'app-id', 'password-key', self.some_data), 'POST',
                        '/user/app-id/password-update/password-key', self.some_data)


class TestChartCalls(TestApiCalls):

    @property
    def some_data(self):
        return {'foo': 1, 'bar': 'two'}

    def call(self, method, *args, **kwargs):
        return super().call('chart', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'chart' + expected_route, expected_body)

    def test_charting_last_data(self):
        self.assertCall(self.call('charting_last_data', 'station-id', 'raw', 5, 'image'), 'GET',
                        '/image/station-id/raw/last/5')
        self.assertCall(self.call('charting_last_data', 'station-id', 'raw', 5), 'GET', '/station-id/raw/last/5')

    def test_charting_period(self):
        self.assertCall(self.call('charting_period', 'station-id', 'raw', 1543524622), 'GET',
                        '/station-id/raw/from/1543524622')
        self.assertCall(self.call('charting_period', 'station-id', 'raw', 1543524622, 1543524622), 'GET',
                        '/station-id/raw/from/1543524622/to/1543524622')
        self.assertCall(self.call('charting_period', 'station-id', 'raw', 1543524622, None, 'image'), 'GET',
                        '/image/station-id/raw/from/1543524622')

    def test_charting_last_data_customized(self):
        self.assertCall(self.call('charting_last_data_customized', 'station-id', 'raw', 5, self.some_data, 'image'),
                        'POST', '/image/station-id/raw/last/5', self.some_data)
        self.assertCall(self.call('charting_last_data_customized', 'station-id', 'raw', 5, self.some_data), 'POST',
                        '/station-id/raw/last/5', self.some_data)

    def test_charting_period_data_customized(self):
        self.assertCall(self.call('charting_period_data_customized', 'station-id', 'raw', 1543524622, self.some_data),
                        'POST', '/station-id/raw/from/1543524622', self.some_data)
        self.assertCall(
            self.call('charting_period_data_customized', 'station-id', 'raw', 1543524622, self.some_data, 1543524622),
            'POST', '/station-id/raw/from/1543524622/to/1543524622', self.some_data)
        self.assertCall(
            self.call('charting_period_data_customized', 'station-id', 'raw', 1543524622, self.some_data, None,
                      'image'), 'POST', '/image/station-id/raw/from/1543524622', self.some_data)


class TestCamerasCalls(TestApiCalls):

    def call(self, method, *args, **kwargs):
        return super().call('cameras', method, *args, **kwargs)

    def assertCall(self, mock_response, expected_method, expected_route, expected_body=None):
        super().assertCall(mock_response, expected_method, 'camera' + expected_route, expected_body)

    def test_min_max_date_of_data(self):
        self.assertCall(self.call('min_max_date_of_data', 'station-id'), 'GET', '/station-id/photos/info')

    def test_get_last_photos(self):
        self.assertCall(self.call('get_last_photos', 'station-id', 1000), 'GET', '/station-id/photos/last/1000')
        self.assertCall(self.call('get_last_photos', 'station-id', 1000, 0), 'GET', '/station-id/photos/last/1000/0')

    def test_get_photos_between_period(self):
        self.assertCall(self.call('get_photos_between_period', 'station-id'), 'GET', '/station-id/photos')
        self.assertCall(self.call('get_photos_between_period', 'station-id', 1543524622), 'GET',
                        '/station-id/photos/from/1543524622')
        self.assertCall(self.call('get_photos_between_period', 'station-id', None, 1543524622), 'GET',
                        '/station-id/photos/to/1543524622')
        self.assertCall(self.call('get_photos_between_period', 'station-id', 1543524622, 1543524622), 'GET',
                        '/station-id/photos/from/1543524622/to/1543524622')
        self.assertCall(self.call('get_photos_between_period', 'station-id', 1543524622, 1543524622, 0), 'GET',
                        '/station-id/photos/from/1543524622/to/1543524622/0')

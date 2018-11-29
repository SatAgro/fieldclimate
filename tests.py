import unittest
import asyncio

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
        super().assertCall(mock_response, expected_method, 'user'+ expected_route, expected_body)
    
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
        super().assertCall(mock_response, expected_method, 'system'+ expected_route, expected_body)
    
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
        super().assertCall(mock_response, expected_method, 'station'+ expected_route, expected_body)
    
    def test_station_information(self):
        self.assertCall(self.call('station_information', 'station-id'), 'GET', '/station-id')
    
    def test_update_station_information(self):
        self.assertCall(self.call('update_station_information', 'station-id', self.some_data), 'PUT', '/station-id', self.some_data)
    
    def test_station_sensors(self):
        self.assertCall(self.call('station_sensors', 'station-id'), 'GET', '/station-id/sensors')
    
    def test_station_sensor_update(self):
        self.assertCall(self.call('station_sensor_update', 'station-id', self.some_data), 'PUT', '/station-id/sensors', self.some_data)
    
    def test_station_nodes(self):
        self.assertCall(self.call('station_nodes', 'station-id'), 'GET', '/station-id/nodes')
    
    def test_change_node_name(self):
        self.assertCall(self.call('change_node_name', 'station-id', self.some_data), 'PUT', '/station-id/nodes', self.some_data)
    
    def test_station_serials(self):
        self.assertCall(self.call('station_serials', 'station-id'), 'GET', '/station-id/serials')
    
    def test_change_serial_name(self):
        self.assertCall(self.call('change_serial_name', 'station-id', self.some_data), 'PUT', '/station-id/serials', self.some_data)
    
    def test_add_station_to_account(self):
        self.assertCall(self.call('add_station_to_account', 'station-id', 'station-key', self.some_data), 'POST', '/station-id/station-key', self.some_data)
    
    def test_remove_station_from_account(self):
        self.assertCall(self.call('remove_station_from_account', 'station-id', 'station-key'), 'DELETE', '/station-id/station-key')
    
    def test_stations_in_proximity(self):
        self.assertCall(self.call('stations_in_proximity', 'station-id', '5m'), 'GET', '/station-id/proximity/5m')
    
    def test_station_last_events(self):
        self.assertCall(self.call('station_last_events', 'station-id', 5), 'GET', '/station-id/events/last/5')
    
    def test_station_last_events_sorted(self):
        self.assertCall(self.call('station_last_events', 'station-id', 5, 'asc'), 'GET', '/station-id/events/last/5/asc')
    
    def test_station_events_between(self):
        self.assertCall(self.call('station_events_between', 'station-id', 1543524622, 1543524623), 'GET', '/station-id/events/from/1543524622/to/1543524623')
    
    def test_station_events_between_sorted(self):
        self.assertCall(self.call('station_events_between', 'station-id', 1543524622, 1543524623, 'asc'), 'GET', '/station-id/events/from/1543524622/to/1543524623/asc')
    
    def test_station_transmission_history_last(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5), 'GET', '/station-id/history/last/5')
    
    def test_station_transmission_history_last_sorted(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, sort='asc'), 'GET', '/station-id/history/last/5/asc')
    
    def test_station_transmission_history_last_filtered(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, filter='resync'), 'GET', '/station-id/history/resync/last/5')
    
    def test_station_transmission_history_last_filtered_sorted(self):
        self.assertCall(self.call('station_transmission_history_last', 'station-id', 5, 'resync', 'asc'), 'GET', '/station-id/history/resync/last/5/asc')
    
    def test_station_transmission_history_between(self):
        self.assertCall(self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623), 'GET', '/station-id/history/from/1543524622/to/1543524623')
    
    def test_station_transmission_history_between_sorted(self):
        self.assertCall(self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, sort='asc'), 'GET', '/station-id/history/from/1543524622/to/1543524623/asc')
    
    def test_station_transmission_history_between_filtered(self):
        self.assertCall(self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, 'resync'), 'GET', '/station-id/history/resync/from/1543524622/to/1543524623')
    
    def test_station_transmission_history_between_filtered_sorted(self):
        self.assertCall(self.call('station_transmission_history_between', 'station-id', 1543524622, 1543524623, 'resync', 'asc'), 'GET', '/station-id/history/resync/from/1543524622/to/1543524623/asc')
    
    def test_station_licenses(self):
        self.assertCall(self.call('station_licenses', 'station-id'), 'GET', '/station-id/licenses')
    

import csv
from collections import defaultdict

from fieldclimate.tools import flatten, find


class CSVSerializer:
    class CSV:

        def __init__(self, headers, rows):
            self.headers = headers
            self.rows = rows

        def write(self, path, **kwargs):
            with open(path, 'w') as csv_file:
                kwargs['fieldnames'] = self.headers
                writer = csv.DictWriter(csv_file, **kwargs)
                writer.writeheader()
                writer.writerows(self.rows)

    class User:
        @staticmethod
        def user_information(path, user, users=None, **kwargs):
            """Serialize user(/users) to csv. User is data type returned by User.user_information."""
            company_headers = [
                'name',
                'profession',
                'department'
            ]
            address_headers = [
                'street',
                'city',
                'district',
                'zip',
                'country'
            ]
            info_headers = [
                'name',
                'lastname',
                'email',
                'phone',
                'cellphone',
                'fax'
            ]
            settings_headers = [
                'language',
                'newsletter',
                'unit_system'
            ]
            headers = [
                'username',
                'created_by',
                'create_time',
                'last_access'
            ]
            headers += ['company {}'.format(header) for header in company_headers]
            headers += ['address {}'.format(header) for header in address_headers]
            headers += ['info {}'.format(header) for header in info_headers]
            headers += ['settings {}'.format(header) for header in settings_headers]

            if users is None:
                users = [user]

            def rows():
                for user in users:
                    user_flat = flatten(user, sep=' ')
                    row = {key: user_flat.get(key, None) for key in headers}
                    yield row

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    class System:
        @staticmethod
        def list_of_system_sensors(path, sensors, **kwargs):
            """Serialize sensors to csv. Sensors is data type returned by System.sensors, Station.sensors"""
            aggrs_headers = [
                'time',
                'last',
                'sum',
                'min',
                'max',
                'avg',
                'user']
            vals_headers = [
                'min',
                'max']
            headers = [
                'name',
                'name_custom',
                'color',
                'decimals',
                'divider',
                'unit',
                'units',
                'ch',
                'code',
                'group',
                'mac',
                'serial',
                'registered',
                'isActive']
            headers += ['aggr {}'.format(header) for header in aggrs_headers]
            headers += ['vals {}'.format(header) for header in vals_headers]

            def rows():
                for sensor in sensors:
                    sensor_flat = flatten(sensor, sep=' ')
                    row = {key: sensor_flat.get(key, None) for key in headers}
                    yield row

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    class Station:
        @staticmethod
        def station_sensors(path, sensors, **kwargs):
            return CSVSerializer.System.list_of_system_sensors(path, sensors, **kwargs)

    class Data:
        @staticmethod
        def data(path, data, **kwargs):
            """Serialize data to csv. Data is data type returned by Data.get_last_data, Data.get_data_between_period(normal format),"""
            headers = ['date',
                       'sensor',
                       'aggr',
                       'value']

            def rows():
                for entry in data['data']:
                    date = entry['date']
                    for measure, value in entry.items():
                        if measure != 'date':
                            delimiter = measure.rfind('_')
                            row = {
                                'date': date,
                                'sensor': measure[:delimiter],
                                'aggr': measure[delimiter + 1:],
                                'value': value
                            }
                            yield row

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    class Forecast:
        @staticmethod
        def forecast(path, forecast, **kwargs):
            """Serialize forecast to csv. Data is data type returned by Forecast.get_forecast_data format),"""
            headers = ['date',
                       'precipitation',
                       'snowfraction',
                       'rainspot',
                       'temperature']

            def rows():
                entries_key = find(forecast, lambda x: 'metadata' not in x and 'units' not in x)
                entries = forecast[entries_key]
                dates = entries.get('time', [])
                precipitations = entries.get('precipitation', defaultdict(lambda: None))
                snowfractions = entries.get('snowfraction', defaultdict(lambda: None))
                rainspots = entries.get('rainspot', defaultdict(lambda: None))
                temperatures = entries.get('temperature', defaultdict(lambda: None))
                for index, date in enumerate(dates):
                    row = {
                        'date': date,
                        'precipitation': precipitations[index],
                        'snowfraction': snowfractions[index],
                        'rainspot': rainspots[index],
                        'temperature': temperatures[index]
                    }
                    yield row

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    class Disease:
        @staticmethod
        def eto(path, eto, **kwargs):
            """Serialize eto to csv. Eto is data type returned by Disease.get_last_eto, Disease.get_eto_between format,"""
            headers = ['date',
                       'ETo[mm]']

            def rows():
                yield from (entry for entry in eto)

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

        @staticmethod
        def disease(path, disease, **kwargs):
            """Serialize disease to csv. Disease is data type returned by Disease.get_last_disease, Disease.get_disease_between format,"""
            headers = ['date',
                       'Blight',
                       'T Sum 3',
                       'Risk Sum']

            def rows():
                yield from (entry for entry in disease)

            return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    class Dev:
        pass

    class Chart:
        pass

    class Cameras:
        pass

    @property
    def user(self):
        return CSVSerializer.User()

    @property
    def system(self):
        return CSVSerializer.System()

    @property
    def station(self):
        return CSVSerializer.Station()

    @property
    def data(self):
        return CSVSerializer.Data()

    @property
    def forecast(self):
        return CSVSerializer.Forecast()

    @property
    def disease(self):
        return CSVSerializer.Disease()

    @property
    def dev(self):
        return CSVSerializer.Dev()

    @property
    def chart(self):
        return CSVSerializer.Chart()

    @property
    def cameras(self):
        return CSVSerializer.Cameras()

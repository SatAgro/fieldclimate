import csv

from fieldclimate.tools import flatten


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

    @staticmethod
    def write_users(path, users, **kwargs):
        """Serialize users to csv. User is data type returned by User.user_information"""
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

        def rows():
            for user in users:
                user_flat = flatten(user, sep=' ')
                row = {key: user_flat.get(key, None) for key in headers}
                yield row

        return CSVSerializer.CSV(headers, rows()).write(path, **kwargs)

    @staticmethod
    def write_sensors(path, sensors, **kwargs):
        # TODO: poprawic doc string
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

    @staticmethod
    def write_data(path, data, **kwargs):
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

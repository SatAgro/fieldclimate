import csv

from fieldclimate.tools import flatten, get_few


class CSVSerializer:

    class CSV:

        def __init__(self, headers, rows):
            self.headers = headers
            self.rows = rows

        def write(self, path, **kwargs):
            with open(path, 'w') as csv_file:
                kwargs['fieldnames'] = self.headers
                writer = csv.writer(csv_file, **kwargs)
                writer.write_header()
                for row in self.rows:
                    writer.write_row(row)

    def write_users(self, path, users, **kwargs):
        """Serialize users to csv. User is data type returned by User.user_information"""
        headers = ['username',
                   'name',
                   'lastname',
                   'email',
                   'phone',
                   'cellphone',
                   'fax',
                   'company name',
                   'company profession',
                   'company department',
                   'address street'
                   'address city',
                   'address district'
                   'address zip',
                   'address district']

        def prettify_user(user):
            return flatten(user)

        rows = (get_few(prettify_user(user), headers, '')for user in users)
        return CSVSerializer.CSV(headers, rows).write(path, **kwargs)

    def write_sensors(self, path, sensors, **kwargs):
        """Serialize sensors to csv. Sensors is data type returned by System.sensors, Station.sensors"""
        headers = ['No.',
                   'name',
                   'unit',
                   'units',
                   'code',
                   'group',
                   'decimal',
                   'divider',
                   'vals',
                   'aggr time',
                   'aggr last',
                   'aggr sum',
                   'aggr min',
                   'aggr max',
                   'aggr avg',
                   'aggr user']

        def prettify_sensor(number, sensor):
            units = sensor.get('units', [])
            result = flatten(sensor, ['aggr', 'vals'])
            result['No.'] = number
            result[units] = units.join()
            return result

        rows = (get_few(prettify_sensor(index, sensor), headers, '') for index, sensor in enumerate(sensors))
        return CSVSerializer.CSV(headers, rows).write(path, **kwargs)

    def write_data(self, path, data, **kwargs):
        """Serialize data to csv. Data is data type returned by Data.get_last_data, Data.get_data_between_period(normal format),"""
        headers = ['date',
                   'sensor'
                   'aggr'
                   'value']

        def readings(data):
            for entry in data['data']:
                date = entry['dare']
                for measure, value in entry.items():
                    if measure is not 'date':
                        delimiter = measure.rfind('_')
                        reading = {
                            'date': date,
                            'sensor': measure[:delimiter],
                            'aggr': measure[delimiter:],
                            'value': value
                        }
                        yield reading

        rows = (get_few(reading, headers, '') for reading in readings(data))
        return CSVSerializer.CSV(headers, rows).write(path, **kwargs)

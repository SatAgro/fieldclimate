# fieldclimate
A Python client for the Pessl Instruments GmbH RESTful API.

# Installation
Download repository and run below command in its root folder.

``
pip install .
``

# Requirements
This package is compatible with python 3.5.6+.

# Examples:
Source codes can be found [here](example).

1. **Establishing connection**:

```py
async with HMAC(public_key, private_key) as client:
    # do all your stuff here, within this connection
```

It is also possible to pass an existing `aiohttp` client session in this way:

```py
async with aiohttp.ClientSession() as session:
    client = HMAC(public_key, private_key).with_client_session(session)
    # do all your stuff here, within this connection
```

Methods corresponding to API endpoints return `ApiResponse` objects, whose fields include:
* `code` - the HTTP response code returned by the server;
* `response` - the response returned by the server, parsed from JSON into Python data types.

Therefore:

2. **Obtaining your username**:

```py
async with HMAC(public_key, private_key) as client:
    user_response = await client.user.user_information()
    if user_response.code == 200:
        print(user_response.response['username'])
```

3. **Retrieving all devices attached to your account**:

```py
async with HMAC(public_key, private_key) as client:
    devices = await client.user.list_of_user_devices()
    for device in devices.response:
        print('Station type: {:13} Station id: {}'.format(device['info']['device_name'], device['name']['original']))
```

4. **Obtaining measurement data from a station**:

The relevant methods include `data.get_last_data()` or, if we want data from an arbitrary range of time, `data.get_data_between_period()`. Their arguments include:

* `station_id`
* `data_group` - either of: `'raw'`, `'hourly'`, `'daily'`, `'monthly'`. `raw` returns data with the greatest granulation possible; the other possible values aggregate it hourly, daily or monthly.
* `time_period` (for `get_last_data()`) - possible values:
  * `'Xh'`, where `X` is a number: Return data from last `X` hours;
  * `'Xd'` - return data from last `X` days;
  * `'Xw'` - last `X` weeks;
  * `'Xm'` - last `X` months;
  * `'X'` - last `X` measurements.
* `from_unix_timestamp`, `to_unix_timestamp` (for `get_data_between_period()`) - Return data in the specified range of time.

Both methods also support one additional argument: `format` - whose value determines the format of the response. Examples below will use `format='optimized'`.

Let's say we are interested in the daily average temperature from the last week. We can obtain the list of sensors that return data for a given time period in the following manner:

```py
async with HMAC(public_key, private_key) as client:
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
    for (sensor_tag, sensor) in station_data.response['data'].items():
        print ('Sensor {} has tag {} and supports the following aggregations: {}'.format(
            sensor['name'], sensor_tag, list(sensor['aggr'].keys())
        ))
```

Let's say that in the output of the above script we see this line, corresponding to the sensor we're interested in:

```
Sensor HC Air temperature has tag 14_X_X_506 and supports the following aggregations: ['min', 'max', 'avg']
```

We can now print out the values we're interested in like this:

```py
async with HMAC(public_key, private_key) as client:
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
    dates = station_data.response['dates']
    sensor_tag = '18_X_X_506'
    unit = station_data.response['data'][sensor_tag]['unit']
    average_temperatures = station_data.response['data'][sensor_tag]['aggr']['avg']
    for (date, average_temperature) in zip(dates, average_temperatures):
        print('On day {} the average temperature was {} {}.'.format(
            date, average_temperature, unit
        ))
```

(The sensor's tag is always constructed in the following manner: CHAIN_MAC_SERIAL_CODE. Therefore, if we know our station's configuration, we can skip manually looking for the sensor we need and instead construct its tag straight off.)

Alternatively, let's say we're rather interested in monthly precipitation sums from last year. Since our second station has a sensor with tag `5_X_X_6` that supports it, we can obtain these values like this:

```py
async with HMAC(public_key, private_key) as client:
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[1]['name']['original']
    station_data = await client.data.get_last_data(station_id, 'monthly', '12m', 'optimized')
    dates = station_data.response['dates']
    sensor_tag = '5_X_X_6'
    unit = station_data.response['data'][sensor_tag]['unit']
    precipitation_sums = station_data.response['data'][sensor_tag]['aggr']['sum']
    for (date, precipitation_sum) in zip(dates, precipitation_sums):
        print('On month {} the precipitation sum was {} {}.'.format(
            date, precipitation_sum, unit
        ))
```

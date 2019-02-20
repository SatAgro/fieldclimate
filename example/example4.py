import asyncio

from fieldclimate.connection.hmac import HMAC

# You have to fill in these values.
public_key = None
private_key = None


async def func():
    async with HMAC(public_key, private_key) as client:
        stations = await client.user.list_of_user_devices()
        station_id = stations.response[0]['name']['original']
        station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
        for (sensor_tag, sensor) in station_data.response['data'].items():
            print('Sensor {} has tag {} and supports the following aggregations: {}'.format(
                sensor['name'], sensor_tag, list(sensor['aggr'].keys())
            ))

loop = asyncio.get_event_loop()
loop.run_until_complete(func())

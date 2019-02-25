import asyncio
import os

from fieldclimate.connection.hmac import HMAC
from fieldclimate.connection.oauth2 import OAuth2, WebBasedProvider
from fieldclimate.schemas.user import UserSchema

public_key = os.environ['FIELDCLIMATE_HAMAC_PUBLIC']
private_key = os.environ['FIELDCLIMATE_HAMAC_PRIVATE']


async def hmac():
    async with HMAC(public_key, private_key) as client:
        stations = await client.user.list_of_user_devices()
        station_id = stations.response[0]['name']['original']
        station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
        for (sensor_tag, sensor) in station_data.response['data'].items():
            print('Sensor {} has tag {} and supports the following aggregations: {}'.format(
                sensor['name'], sensor_tag, list(sensor['aggr'].keys())
            ))


async def oauth2():
    async with OAuth2(WebBasedProvider()) as client:
        stations = await client.user.list_of_user_devices()
        station_id = stations.response[0]['name']['original']
        station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
        for (sensor_tag, sensor) in station_data.response['data'].items():
            print('Sensor {} has tag {} and supports the following aggregations: {}'.format(
                sensor['name'], sensor_tag, list(sensor['aggr'].keys())
            ))


async def sub0():
    print('0 in')
    await asyncio.sleep(10)
    print('0 out')


async def sub1():
    print('1 in')
    print('1 out')


async def concurrency():
    task0 = asyncio.get_event_loop().create_task(sub0())
    task1 = asyncio.get_event_loop().create_task(sub1())
    await asyncio.sleep(20)
    print('wait')
    await task0
    await task1
    print('done')


async def noconcurrency():
    print('wait')
    await sub0()
    await sub1()
    print('done')


async def schema():
    async with HMAC(public_key, private_key) as client:
        user_response = await client.user.user_information()
        response = user_response.response
        schema = UserSchema()
        result = schema.load(response)
        print(result.data)


loop = asyncio.get_event_loop()

#loop.run_until_complete(hmac())
#loop.run_until_complete(oauth2())
#loop.run_until_complete(concurrency())
#loop.run_until_complete(noconcurrency())
loop.run_until_complete(schema())

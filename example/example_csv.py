import asyncio


from fieldclimate.connection.oauth2 import OAuth2, WebBasedProvider
from fieldclimate.export.csv import CSVSerializer


async def users(client):
    user = await client.user.user_information()
    CSVSerializer.write_users('user.csv', [user.response])


async def sensors(client):
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_sensors = await client.station.station_sensors(station_id)
    CSVSerializer.write_sensors('sensors.csv', station_sensors.response)


async def data(client):
    stations = await client.user.list_of_user_devices()
    station_id = stations.response[0]['name']['original']
    station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'normal')
    CSVSerializer.write_data('data.csv', station_data.response)


async def func():
    async with OAuth2(WebBasedProvider()) as client:
        await data(client)
        await sensors(client)
        await users(client)


loop = asyncio.get_event_loop()
loop.run_until_complete(func())

import asyncio

from fieldclimate.connection.hmac import HMAC

# You have to fill in these values.
from fieldclimate.export.csv import CSVSerializer
from fieldclimate.tools import get_user_credentials

credentials = get_user_credentials()
public_key = credentials['public_key']
private_key = credentials['private_key']

print(private_key)
async def func():
    async with HMAC(public_key, private_key) as client:
        stations = await client.user.list_of_user_devices()
        station_id = stations.response[0]['name']['original']
        station_data = await client.data.get_last_data(station_id, 'daily', '1w', 'optimized')
        CSVSerializer.write_data('data.csv', station_data)


loop = asyncio.get_event_loop()
loop.run_until_complete(func())

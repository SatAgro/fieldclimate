import asyncio

from fieldclimate.connection.hmac import HMAC

# You have to fill in these values.
public_key = None
private_key = None


async def func():
    async with HMAC(public_key, private_key) as client:
        devices = await client.user.list_of_user_devices()
        for device in devices.response:
            print('Station type: {:13} Station id: {}'
                  .format(device['info']['device_name'], device['name']['original']))

loop = asyncio.get_event_loop()
loop.run_until_complete(func())

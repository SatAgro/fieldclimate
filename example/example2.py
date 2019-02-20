import asyncio

from fieldclimate.connection.hmac import HMAC

# You have to fill in these values.
public_key = None
private_key = None


async def func():
    async with HMAC(public_key, private_key) as client:
        user_response = await client.user.user_information()
        if user_response.code == 200:
            print(user_response.response['username'])

loop = asyncio.get_event_loop()
loop.run_until_complete(func())

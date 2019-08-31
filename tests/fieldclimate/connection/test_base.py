import unittest
import asyncio

from tests.fieldclimate.test_api import MockSession, MockConnection

class TestOneSession(unittest.TestCase):
    def test_session_can_be_passed_to_many_instances(self):
        async def actual_test():
            async with MockSession() as session:
                connection1 = MockConnection().with_client_session(session)
                connection2 = MockConnection().with_client_session(session)
                
                self.assertTrue(connection1._auth._session._aentered)
                self.assertTrue(connection2._auth._session._aentered)
                
                responses = await asyncio.gather(
                    connection1.user.user_information(),
                    connection2.user.list_of_user_devices()
                )
                
                self.assertEqual(responses[0].response['url'],
                                 'https://api.fieldclimate.com/v1/user')
                self.assertEqual(responses[1].response['url'],
                                 'https://api.fieldclimate.com/v1/user/stations')

        asyncio.get_event_loop().run_until_complete(actual_test())

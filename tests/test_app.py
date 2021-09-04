import asyncio
import time

import pytest

from textual.app import App


@pytest.mark.asyncio
async def test_execute_in_thread():

    sleep_time = 0.1

    def blocking(*args, **kwargs) -> None:
        assert args == ("test_arg",)
        assert kwargs == {"kwarg": "expected"}
        time.sleep(sleep_time)


    class Beeper(App):
        success: bool = False
        async def testme(self):
            start = time.time()
            task = asyncio.create_task(
                self.execute_in_thread(
                    blocking, "test_arg", kwarg="expected"
                )
            )
            # if we didn't use execute_in_thread here,
            # calling sleep() would block the event loop
            # such that the background task would be paused
            # and total execution would take >= sleep_time * 2
            await self.execute_in_thread(
                blocking, "test_arg", kwarg="expected"
            )
            await task
            end  = time.time()
            # test that both calls were made concurrently
            # this could be (end-start) <= sleep_time
            # but there is some overhead from creating tasks
            # creating the threadpool, etc.
            # such that we'd have to herusitcally determine a number
            # like (end-start) < sleep_time * 1.0123
            assert (end-start) < sleep_time * 2
            self.success = True

    b = Beeper()
    await b.testme()
    assert b.success

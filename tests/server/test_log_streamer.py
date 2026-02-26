import asyncio
import logging
import pytest
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler


@pytest.mark.asyncio
async def test_handler_puts_message_in_queue():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    handler = ThreadSafeQueueHandler(queue, loop)

    logger = logging.getLogger("test_streamer_unique")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    logger.info("hello from thread")

    await asyncio.sleep(0.05)
    assert not queue.empty()
    msg = await queue.get()
    assert msg["level"] == "INFO"
    assert "hello from thread" in msg["msg"]
    assert "ts" in msg

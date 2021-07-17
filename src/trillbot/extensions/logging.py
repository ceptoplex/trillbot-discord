from asyncio import Queue, ensure_future
from logging import StreamHandler, getLogger, WARNING
from typing import Optional

from discord import Guild, TextChannel
from discord.ext.commands import Bot


class _LoggingHandler(StreamHandler):
    def __init__(self, queue):
        super().__init__()
        self._queue = queue

    def emit(self, record):
        if 'guild' not in record.__dict__:
            return
        guild = record.__dict__['guild']
        self._queue.put_nowait((guild, record.message))


class Logging:
    LOG_CHANNEL_NAME_PARTS = [
        'bot-log'
    ]

    def __init__(self):
        self._running = True

    def start(self, bot):
        queue = Queue()

        logging_handler = _LoggingHandler(queue)
        logging_handler.setLevel(WARNING)
        logger = getLogger()
        logger.addHandler(logging_handler)

        async def run():
            while self._running:
                (guild, message) = await queue.get()
                channel = Logging._get_log_channel(guild)
                if channel is None:
                    continue
                await channel.send(message)

        ensure_future(run(), loop=bot.loop)

    def stop(self):
        self._running = False

    @staticmethod
    def _get_log_channel(guild: Guild) -> Optional[TextChannel]:
        for channel in guild.text_channels:
            for channel_name_part in Logging.LOG_CHANNEL_NAME_PARTS:
                if channel_name_part in channel.name:
                    return channel
        return None


logging = Logging()


def setup(bot: Bot):
    logging.start(bot)


def teardown(bot: Bot):
    logging.stop()

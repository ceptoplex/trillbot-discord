from asyncio import Queue
from logging import StreamHandler, getLogger, WARNING
from typing import Optional

from discord import Guild, TextChannel
from discord.ext import tasks
from discord.ext.commands import Bot, Cog


class _LoggingHandler(StreamHandler):
    def __init__(self, queue):
        super().__init__()
        self._queue = queue

    def emit(self, record):
        if 'guild' not in record.__dict__:
            return
        guild = record.__dict__['guild']
        self._queue.put_nowait((guild, record.message))


class Logging(Cog):
    LOG_CHANNEL_NAME_PARTS = [
        'bot-log'
    ]

    def __init__(self, bot: Bot):
        self._bot = bot
        self._queue = Queue()

        logging_handler = _LoggingHandler(self._queue)
        logging_handler.setLevel(WARNING)
        logger = getLogger()
        logger.addHandler(logging_handler)

        self._run.start()

    def cog_unload(self):
        self._run.cancel()

    @tasks.loop()
    async def _run(self):
        (guild, message) = await self._queue.get()
        channel = Logging._get_log_channel(guild)
        if channel is None:
            return
        await channel.send(message)

    @staticmethod
    def _get_log_channel(guild: Guild) -> Optional[TextChannel]:
        for channel in guild.text_channels:
            for channel_name_part in Logging.LOG_CHANNEL_NAME_PARTS:
                if channel_name_part in channel.name:
                    return channel
        return None


async def setup(bot: Bot):
    await bot.add_cog(Logging(bot))


async def teardown(bot: Bot):
    await bot.remove_cog(Logging.__name__)

import sys
from logging import StreamHandler, INFO, DEBUG, getLogger, Formatter

from discord import Intents
from discord.ext.commands import Bot

from trillbot.config import Config
from trillbot.extensions import elasticvoice, logging, reactionchannel


class _GuildFormatter(Formatter):
    def __init__(self):
        super().__init__()
        self._formatter = Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z')
        self._guild_formatter = Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] [Guild: %(guild)s] %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z')

    def format(self, record):
        if 'guild' in record.__dict__:
            return self._guild_formatter.format(record)
        else:
            return self._formatter.format(record)


class _Bot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.load_extension(elasticvoice.__name__)
        await self.load_extension(logging.__name__)
        #await self.load_extension(membermonitoring.__name__)
        #await self.load_extension(messagemonitoring.__name__)
        await self.load_extension(reactionchannel.__name__)


class App:
    def __init__(self):
        logger = getLogger()
        logger.setLevel(DEBUG)
        console_handler = StreamHandler(sys.stdout)
        console_handler.setLevel(INFO)
        console_handler.setFormatter(_GuildFormatter())
        logger.addHandler(console_handler)

    async def run(self):
        intents = Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True

        async with _Bot('!', intents=intents) as bot:
            await bot.start(Config.get_discord_token())

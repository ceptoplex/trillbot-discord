import sys
from logging import StreamHandler, INFO, DEBUG, getLogger, Formatter

from discord import Intents
from discord.ext.commands import Bot

from trillbot.config import Config
from trillbot.extensions import elasticvoice, logging, membermonitoring


class App:
    def __init__(self):
        class GuildFormatter(Formatter):
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

        logger = getLogger()
        logger.setLevel(DEBUG)
        console_handler = StreamHandler(sys.stdout)
        console_handler.setLevel(INFO)
        console_handler.setFormatter(GuildFormatter())
        logger.addHandler(console_handler)

        intents = Intents.all()
        self.bot = Bot('!', intents=intents)
        self.bot.load_extension(elasticvoice.__name__)
        self.bot.load_extension(logging.__name__)
        self.bot.load_extension(membermonitoring.__name__)

    def run(self):
        self.bot.run(Config.get_discord_token())

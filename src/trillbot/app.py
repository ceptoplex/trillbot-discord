import logging
import sys

from discord import Intents
from discord.ext.commands import Bot

from trillbot.config import Config
from trillbot.extensions import membermonitoring, elasticvoice


class App:
    def __init__(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        intents = Intents.all()
        self.bot = Bot('!', intents=intents)
        self.bot.load_extension(elasticvoice.__name__)
        self.bot.load_extension(membermonitoring.__name__)

    def run(self):
        self.bot.run(Config.get_discord_token())

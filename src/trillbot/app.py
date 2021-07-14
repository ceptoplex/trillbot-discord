import logging
import sys

import discord

from trillbot.config import Config


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

        self.client = discord.Client()

    def run(self):
        self.client.run(Config.get_discord_token())

import discord

from config import Config


class App:
    def __init__(self):
        self.client = discord.Client()

    def run(self):
        self.client.run(Config.get_discord_token())

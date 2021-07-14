import discord


class App:
    def __init__(self):
        self.client = discord.Client()

    def run(self):
        # TODO: Insert token.
        self.client.run('your token here')

        @self.client.event
        async def on_ready():
            print(f"We have logged in as '{self.client.user}'.")

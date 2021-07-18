import os


class Config:
    @staticmethod
    def get_discord_token():
        env_name = 'TRILLBOT_DISCORD_TOKEN'

        value = os.environ.get(env_name)
        if value is None:
            raise ConfigEnvironmentVariableUnsetException(env_name)

        return value


class ConfigEnvironmentVariableUnsetException(Exception):
    def __init__(self, name):
        super().__init__(f"Environment variable '{name}' is not set.")

import logging
from typing import Union

from discord import Guild, VoiceChannel, VoiceState, Member
from discord.abc import GuildChannel
from discord.ext import commands
from discord.ext.commands import Bot, Cog


class ElasticVoice(Cog):
    MAX_CHANNEL_COUNT_PER_GROUP = 10

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_guild_available(self, guild: Guild):
        await self._update_channel_groups(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        await self._update_channel_groups(guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, _: Member, before: VoiceState, after: VoiceState):
        if before.channel is not None and after.channel is not None and before.channel == after.channel:
            return
        channel = before.channel if before.channel is not None else after.channel
        await self._update_channel_groups(channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: GuildChannel):
        if not isinstance(channel, VoiceChannel):
            return
        await self._update_channel_groups(channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, _: GuildChannel, after: GuildChannel):
        if not isinstance(after, VoiceChannel):
            return
        await self._update_channel_groups(after.guild)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        if not isinstance(channel, VoiceChannel):
            return
        await self._update_channel_groups(channel.guild)

    async def _update_channel_groups(self, guild: Guild):
        # This method will just create or delete a single channel before returning.
        # Eventually, each such modification will trigger an event that will result in this method being called again
        # to check whether additional steps have to be taken.

        # Get a list of all relevant channels, sorted by their position.

        def should_exclude_channel(x: VoiceChannel) -> bool:
            return 'Lobby' in x.name

        channels = guild.voice_channels
        channels = [x for x in channels if not should_exclude_channel(x)]
        channels.sort(key=lambda x: x.position)

        # Logically group channels that are "equal".

        def are_channels_equal(x: VoiceChannel, y: VoiceChannel) -> bool:
            return (
                x.name == y.name and
                x.bitrate == y.bitrate and
                x.category_id == y.category_id and
                x.user_limit == y.user_limit
            )

        channel_group_channels = None
        previous_channel: Union[VoiceChannel, None] = None
        channel_groups = []
        for channel in channels:
            if previous_channel is None or are_channels_equal(previous_channel, channel) is False:
                if channel_group_channels is not None:
                    channel_groups.append(channel_group_channels)
                channel_group_channels = [channel]
            else:
                channel_group_channels.append(channel)
            previous_channel = channel
        if len(channel_group_channels) > 0:
            channel_groups.append(channel_group_channels)

        # Remove the first found channel that is unnecessary in some group.

        for channel_group in channel_groups:
            empty_channels = [x for x in channel_group if len(x.members) == 0]
            if len(empty_channels) <= 1:
                continue

            await empty_channels[-1].delete()
            self._logger.info(f"Inside guild '{guild}', voice channel '{empty_channels[-1]}' was removed.")
            return

        # Add one channel to the first group found that misses a channel.

        for channel_group in channel_groups:
            empty_channels = [x for x in channel_group if len(x.members) == 0]
            if len(empty_channels) > 0:
                continue
            if len(channel_group) >= ElasticVoice.MAX_CHANNEL_COUNT_PER_GROUP:
                self._logger.info(
                    f"Inside guild '{guild}', a new voice channel was not created after '{channel_group[-1]}' "
                    f"because the limit of {ElasticVoice.MAX_CHANNEL_COUNT_PER_GROUP} channels "
                    f"was reached for this group.")
                continue

            new_channel = await guild.create_voice_channel(
                channel_group[-1].name,
                overwrites=channel_group[-1].overwrites,
                category=channel_group[-1].category,
                bitrate=channel_group[-1].bitrate,
                user_limit=channel_group[-1].user_limit,
                rtc_region=channel_group[-1].rtc_region,
                position=channel_group[-1].position)
            self._logger.info(f"Inside guild '{guild}', a new voice channel '{new_channel}' was created.")
            return


def setup(bot: Bot):
    bot.add_cog(ElasticVoice())


def teardown(bot: Bot):
    bot.remove_cog(ElasticVoice.__name__)

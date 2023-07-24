from discord import Guild, Member
from discord.ext import commands
from discord.ext.commands import Bot, Cog


class MinecraftSync(Cog):
    def __init__(self, bot: Bot):
        self._bot = bot

    @commands.Cog.listener()
    async def on_guild_available(self, guild: Guild):
        for member in guild.members:
            await MinecraftSync._check_member_roles(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        for member in guild.members:
            await MinecraftSync._check_member_roles(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        await MinecraftSync._check_member_roles(after)

    @staticmethod
    async def _check_member_roles(member: Member):
        twitch_sub_roles = [x for x in await member.guild.fetch_roles() if 'Twitch Sub' in x.name and 'Minecraft' not in x.name]
        minecraft_role = next((x for x in await member.guild.fetch_roles() if 'Minecraft' in x.name), None)
        if len(twitch_sub_roles) == 0 or minecraft_role is None:
            return
        if len(set(twitch_sub_roles).intersection(member.roles)) > 0 and minecraft_role not in member.roles:
            await member.add_roles(minecraft_role)
            return
        if len(set(twitch_sub_roles).intersection(member.roles)) == 0 and minecraft_role in member.roles:
            await member.remove_roles(minecraft_role)
            return


async def setup(bot: Bot):
    await bot.add_cog(MinecraftSync(bot))


async def teardown(bot: Bot):
    await bot.remove_cog(MinecraftSync.__name__)

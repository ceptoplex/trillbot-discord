import logging
from datetime import datetime, timedelta

from confusables import is_confusable
from discord import Guild, Member
from discord.ext import commands
from discord.ext.commands import Bot, Cog

NOT_VALIDATED_MEMBER_IDS = [
    177726019959128065,  # TrilluXe
    294882584201003009  # GiveawayBot (https://discord.bots.gg/bots/294882584201003009)
]


class _JoinedMember:
    def __init__(self, member: Member, joined_at: datetime):
        self.member = member
        self.joined_at = joined_at
        self.kicked = False


class MemberMonitoring(Cog):
    FORBIDDEN_NAME_PARTS = [
        'trill',
        'giveaway'
    ]
    MAXIMUM_JOIN_COUNT_PER_TIMEFRAME = (20, timedelta(minutes=10))

    def __init__(self, bot: Bot):
        self._logger = logging.getLogger(__name__)
        self._bot = bot
        self._joined_members_per_timeframe: list[_JoinedMember] = []

    @commands.Cog.listener()
    async def on_guild_available(self, guild: Guild):
        for member in guild.members:
            await self._validate_member(member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        for member in guild.members:
            await self._validate_member(member)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        if not await self._validate_member(member):
            return
        await self._validate_joined_member(member)

    @commands.Cog.listener()
    async def on_member_update(self, _: Member, after: Member):
        await self._validate_member(after)

    async def _validate_member(self, member: Member):
        if not self._is_validated_member(member):
            return True

        forbidden_name_part = self._has_name_part_similar_to_forbidden_name_parts(member)
        if forbidden_name_part is not None:
            reason = f"Part of the member's name is too similar to '{forbidden_name_part}'."
            await member.kick(reason=reason)
            name = member.display_name if member.display_name is not None else member.name
            self._logger.warning(
                f"Kicked member {member.mention} with displayed name '{name}'. Reason: {reason}",
                extra={'guild': member.guild})
            return False

        return True

    async def _validate_joined_member(self, member: Member):
        if not self._is_validated_member(member):
            return

        now = datetime.utcnow()
        self._joined_members_per_timeframe.append(_JoinedMember(member, now))

        maximum_join_count_per_timeframe, timeframe = MemberMonitoring.MAXIMUM_JOIN_COUNT_PER_TIMEFRAME
        oldest_joined_at = now - timeframe

        # Check timeframe constraint.

        self._joined_members_per_timeframe = [
            x
            for x
            in self._joined_members_per_timeframe
            if x.joined_at >= oldest_joined_at
        ]
        if len(self._joined_members_per_timeframe) > maximum_join_count_per_timeframe:
            for joined_member in self._joined_members_per_timeframe:
                if joined_member.kicked:
                    continue
                joined_member.kicked = True
                reason = (
                    f"Joined too fast. "
                    f"(Limit is {maximum_join_count_per_timeframe} member(s) per timeframe {timeframe}.)"
                )
                await joined_member.member.kick(reason=reason)
                name = member.display_name if member.display_name is not None else member.name
                self._logger.warning(
                    f"Kicked member {joined_member.member.mention} with displayed name '{name}'. "
                    f"Reason: {reason}",
                    extra={'guild': joined_member.member.guild})
            return

        # Check name constraint.

        joined_members_per_name = {}
        for joined_member in self._joined_members_per_timeframe:
            name = joined_member.member.display_name \
                if joined_member.member.display_name is not None \
                else joined_member.member.name
            if name not in joined_members_per_name:
                joined_members_per_name[name] = []
            joined_members_per_name[name].append(joined_member)
        joined_members_per_name = [y for x in joined_members_per_name.values() if len(x) > 1 for y in x]
        for joined_member in joined_members_per_name:
            if joined_member.kicked:
                continue
            joined_member.kicked = True
            reason = (
                f"Joined with a name that is equal to the name of a member "
                f"that joined within the timeframe {timeframe}."
            )
            await joined_member.member.kick(reason=reason)
            name = member.display_name if member.display_name is not None else member.name
            self._logger.warning(
                f"Kicked member {joined_member.member.mention} with displayed name '{name}'. "
                f"Reason: {reason}",
                extra={'guild': joined_member.member.guild})

    def _is_validated_member(self, member: Member):
        if member == self._bot.user:
            return False
        if member.id in NOT_VALIDATED_MEMBER_IDS:
            return False
        return True

    @staticmethod
    def _has_name_part_similar_to_forbidden_name_parts(member: Member):
        for forbidden_name_part in MemberMonitoring.FORBIDDEN_NAME_PARTS:
            name = member.display_name if member.display_name is not None else member.name
            if len(name) < len(forbidden_name_part):
                continue
            for i in range(len(name) - len(forbidden_name_part) + 1):
                name_part = name[i:i + len(forbidden_name_part)]
                if is_confusable(name_part, forbidden_name_part):
                    return forbidden_name_part
        return None


def setup(bot: Bot):
    bot.add_cog(MemberMonitoring(bot))


def teardown(bot: Bot):
    bot.remove_cog(MemberMonitoring.__name__)

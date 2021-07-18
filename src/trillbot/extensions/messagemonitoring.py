import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse

from discord import Message, Member
from discord.ext import commands
from discord.ext.commands import Bot, Cog
from rapidfuzz import string_metric


class _CaughtMember:
    def __init__(self, member: Member, caught_at: datetime):
        self.member = member
        self.caught_at = caught_at


class MessageMonitoring(Cog):
    NOT_VALIDATED_ROLE_IDS = [
        315456917785018378,  # Admin
        323334369534148610,  # Weltherrschaft
        315497366872522753,  # Crew
        315497300237615125,  # Twitch Mod (TrilluXe)
        431583263560171521,  # Twitch Mod (fELIXSAn)
        780849541179506688,  # Discord Mod
        321980255281741834  # VIP
    ]
    PHISHING_TARGET_DOMAINS = [
        'steamcommunity.com'
    ]
    CAUGHT_TIMEFRAME = timedelta(minutes=10)

    def __init__(self, bot: Bot):
        self._logger = logging.getLogger(__name__)
        self._bot = bot
        self._caught_members_per_timeframe = []

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        await self._validate_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, _: Message, after: Message):
        await self._validate_message(after)

    async def _validate_message(self, message: Message):
        if not self._is_validated_message(message):
            return

        phishing_target_domain = self._contains_phishing_url(message)
        if phishing_target_domain is None:
            return

        member = message.author
        await message.delete()
        reason = (
            f"Message `{message.content}` contains a potential phishing URL "
            f"that targets the domain `{phishing_target_domain}`."
        )
        self._logger.warning(
            f"Removed message of member {member.mention} "
            f"from channel {message.channel.mention}. "
            f"Reason: {reason}",
            extra={'guild': member.guild})

        # Track and ban repeat offenders.

        now = datetime.utcnow()
        oldest_caught_at = now - MessageMonitoring.CAUGHT_TIMEFRAME
        self._caught_members_per_timeframe = [
            x
            for x
            in self._caught_members_per_timeframe
            if x.caught_at >= oldest_caught_at
        ]

        if len([x for x in self._caught_members_per_timeframe if x.member == member]) > 0:
            reason = (
                f"Member sent two messages containing potential phishing URLs "
                f"within the timeframe {MessageMonitoring.CAUGHT_TIMEFRAME}."
            )
            await member.ban(reason=reason, delete_message_days=7)
            self._logger.warning(
                f"Banned member {member.mention} and "
                f"removed the messages sent by the member within the last 7 days. "
                f"Reason: {reason}",
                extra={'guild': member.guild})
            return

        self._caught_members_per_timeframe.append(_CaughtMember(member, now))

        # Warn first offenders.

        await message.channel.send(
            content=(
                f"{member.mention} I've deleted your message because "
                f"it contains a potentially malicious URL. "
                f"If it was just a typo, please make sure to correct it before sending the same message again - "
                f"or you will be permanently banned."
            ),
            delete_after=60)

    def _is_validated_message(self, message: Message):
        if message.author == self._bot.user:
            return False
        if len([x for x in message.author.roles if x.id in MessageMonitoring.NOT_VALIDATED_ROLE_IDS]) > 0:
            return False
        return True

    @staticmethod
    def _contains_phishing_url(message: Message):
        content = message.content
        for phishing_target_domain in MessageMonitoring.PHISHING_TARGET_DOMAINS:
            url_strings = re.findall(
                r'https?://[\w_-]+(?:(?:\.[\w_-]+)+)[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-]?',
                content)
            for url_string in url_strings:
                url = urlparse(url_string)
                domain = str.join('.', url.netloc.split('.')[-2:])
                # Result can be 0% to 100% similarity.
                result = string_metric.normalized_levenshtein(domain, phishing_target_domain)
                if result == 100:
                    # Exclude target domain.
                    continue
                if result >= 75:
                    return phishing_target_domain
        return None


def setup(bot: Bot):
    bot.add_cog(MessageMonitoring(bot))


def teardown(bot: Bot):
    bot.remove_cog(MessageMonitoring.__name__)

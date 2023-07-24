import re
from typing import Union

from discord import ButtonStyle, DMChannel, GroupChannel, Interaction, Message, PartialMessageable, StageChannel, TextChannel, TextStyle, Thread, VoiceChannel
from discord.ui import Button, Modal, TextInput, View
from discord.ext import commands
from discord.ext.commands import Bot, Cog


URL_PATTERN = re.compile(r'([a-zA-Z0-9]+://)?([a-zA-Z0-9_]+:[a-zA-Z0-9_]+@)?([a-zA-Z0-9.-]+\.[A-Za-z]{2,4})(:[0-9]+)?(/.*)?')


class ReactionChannel(Cog):
    def __init__(self, bot: Bot):
        self._bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        author = message.author
        if author.id == self._bot.user.id:
            return
        channel = message.channel
        if not ReactionChannel._is_reaction_channel(channel):
            return

        if (
            not URL_PATTERN.search(message.content) and
            len(message.attachments) == 0):
            await message.delete()
            return

        files = [await x.to_file() for x in message.attachments]

        class ReportModal(Modal, title='Meldung (NICHT ANONYM!)'):
            reason = TextInput(label='Begründung', style=TextStyle.paragraph, placeholder='Begründung, die MIT DEINEM NAMEN und FÜR JEDEN SICHTBAR angezeigt werden soll.')

            def __init__(self, logger: ReactionChannel, *args, **kwargs):
                super().__init__(*args, **kwargs)

            async def on_submit(self, interaction: Interaction):
                user = interaction.user
                if len(interaction.message.attachments) > 0:
                    content_suffix = '\n'.join([x.url for x in interaction.message.attachments])
                    content_suffix = f'\n\n {content_suffix}'
                else:
                    content_suffix = ''
                new_message = await interaction.message.edit(content=interaction.message.content + content_suffix, embeds=interaction.message.embeds[-1:], view=view)
                while len(new_message.attachments) > 0:
                    new_message = await new_message.remove_attachments(new_message.attachments[0])
                mod_role_mentions = ' '.join([x.mention for x in await message.guild.fetch_roles() if x.permissions.manage_messages and not x.permissions.administrator])
                thread = channel.get_thread(new_message.id)
                if thread is None:
                    thread = await new_message.create_thread(name='Meldung')
                await thread.send(
                    f'{mod_role_mentions} Meldung von {user.mention}: {self.reason.value}')
                await interaction.response.send_message(
                    f'{user.mention} Deine Meldung wurde in einem Thread an die Nachricht angehängt.',
                    ephemeral=True)

        class ReportButton(Button):
            def __init__(self):
                emoji = next((x for x in message.guild.emojis if x.name == 'monkaTOS'), '\N{NO ENTRY}')
                super().__init__(label='Melden', emoji=emoji, style=ButtonStyle.danger)

            async def callback(self, interaction: Interaction):
                await interaction.response.send_modal(ReportModal(self))

        view = View(timeout=None)
        view.add_item(ReportButton())

        new_message = await channel.send(content=message.content + f'\n⎯⎯⎯⎯⎯\nvon {author.mention}', files=files, view=view)

        emoji = '\N{UPWARDS BLACK ARROW}'
        await new_message.add_reaction(emoji)
        emoji = '\N{DOWNWARDS BLACK ARROW}'
        await new_message.add_reaction(emoji)

        await message.delete()

    @commands.Cog.listener()
    async def on_message_delete(self, message: Message):
        channel = message.channel
        if not ReactionChannel._is_reaction_channel(channel):
            return
        thread = channel.get_thread(message.id)
        if thread is None:
            return
        await thread.delete()

    @staticmethod
    def _is_reaction_channel(channel: Union[TextChannel, StageChannel, VoiceChannel, Thread, DMChannel, GroupChannel, PartialMessageable]):
        if not isinstance(channel, TextChannel):
            return False
        return channel.name.startswith('reaction')


async def setup(bot: Bot):
    await bot.add_cog(ReactionChannel(bot))


async def teardown(bot: Bot):
    await bot.remove_cog(ReactionChannel.__name__)

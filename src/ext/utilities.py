from __future__ import annotations
from typing import TYPE_CHECKING

import colorsys
import random

import discord
from discord import Embed, File
from discord import app_commands
from discord.app_commands import checks
from discord.app_commands import command, describe, Range, Transform
from discord.ext import commands

from utils import Color, ColorTransformer, Emoji, EmojiTransformer, MessageTransformer
from utils.reminders import Reminder
from utils.role_menus import RoleMenuView

if TYPE_CHECKING:
    from tau import Tau


class Utilities(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.wait_until_synced()

        await self.bot.reminders.remove_user(member)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.bot.wait_until_synced()

        await self.bot.reminders.remove_channel(channel)

    @command(name='color')
    async def color(self, interaction: discord.Interaction, color: Transform[discord.Color, ColorTransformer]):
        '''Display info on a color'''
        r, g, b = color.to_rgb()
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        _, s_, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

        embed = (
            Embed(description='**[Color picker](https://www.google.com/search?q=color+picker)**', color=color)
            .set_author(name=color)
            .add_field(name='RGB', value=f'{r}, {g}, {b}')
            .add_field(name='HSL', value=f'{round(h*360)}°, {s:.0%}, {l:.0%}')
            .add_field(name='HSV', value=f'{round(h*360)}°, {s_:.0%}, {v:.0%}')
            .set_image(url='attachment://unknown.png')
        )
        await interaction.response.send_message(embed=embed)

    @command(name='emoji')
    @checks.bot_has_permissions(external_emojis=True)
    async def emoji(self, interaction: discord.Interaction, *, emoji: Transform[discord.PartialEmoji, EmojiTransformer]):
        '''Display info on an emoji'''
        embed = (
            Embed(description=f'{emoji} **[{emoji.name}]({emoji.url})\n`{emoji}`**', color=Color.primary)
            .set_thumbnail(url=emoji.url)
            .add_field(name='Animated', value=Emoji.on if emoji.animated else Emoji.off)
            .set_footer(text=f'ID: {emoji.id}, created')
        )
        embed.timestamp = emoji.created_at

        await interaction.response.send_message(embed=embed)

    @command(name='random')
    @describe(lower='lower bound (inclusive)')
    @describe(upper='upper bound (inclusive)')
    @checks.bot_has_permissions(external_emojis=True)
    async def random(self, interaction: discord.Interaction, lower: Range[int, 0], upper: Range[int, 0]):
        '''Randomly generate an integer'''
        embed = (
            Embed(color=random.choice(tuple(Color)))
            .set_author(name=f'You got {random.randint(lower, upper)}!')
        )
        await interaction.response.send_message(embed=embed)

    @command(name='remind')
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def remind(self, interaction: discord.Interaction, days: Range[int, 0, 60], hours: Range[int, 0, 23], minutes: Range[int, 0, 59], reminder: str):
        '''Set a reminder (maximum 60 days)'''
        reminder = Reminder.from_relative(interaction.user, interaction.channel, days, hours, minutes, reminder)

        await self.bot.reminders.add(reminder)

        embed = (
            Embed(description=f'>>> {reminder}', color=Color.primary)
            .set_author(name='Reminder', icon_url='attachment://unknown.png')
            .set_footer(text='\u200b', icon_url='attachment://unknown1.png')
        )
        embed.timestamp = reminder.time

        files = [File('assets/dot.png', 'unknown.png'), File('assets/clock.png', 'unknown1.png')]
        await interaction.response.send_message(embed=embed, files=files)

    @command(name='resend')
    @checks.has_permissions(manage_guild=True)
    @checks.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def resend(self, interaction: discord.Interaction, message: Transform[discord.Message, MessageTransformer]):
        '''Resend a message sent from this bot'''
        if message.author != self.bot.user:
            raise app_commands.AppCommandError

        files: list[discord.File] = []
        for attachment in message.attachments:
            file = await attachment.to_file()
            files.append(file)

        role_menu = RoleMenuView.from_message(message)
        if role_menu is not None:
            self.bot.role_menus.add(message)

        await interaction.response.send_message(message.content, embeds=message.embeds, files=files)

        await message.delete()


async def setup(bot: Tau):
    await bot.add_cog(Utilities(bot))

from __future__ import annotations
from typing import TYPE_CHECKING

import random

import aiohttp
import discord
from discord import app_commands
from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown

from utils import Color, Emoji
from utils.xp import Score

if TYPE_CHECKING:
    from tau import Tau


class Social(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 86400.0, commands.BucketType.user)

    async def fetch_gif(self, query: str) -> str:
        async with aiohttp.ClientSession() as session:
            query = query.replace(' ', '%20')
            filters = 'contentfilter=medium&mediafilter=minimal&limit=1'
            async with session.get(f'https://api.tenor.com/v1/random?q={query}&key={self.bot.conf.tenor_api_key}&{filters}') as response:
                content = await response.json()
                url = content['results'][0]['media'][0]['gif']['url']

            return url

    @app_commands.command(name='boop')
    async def boop(self, interaction: discord.Interaction, user: discord.User):
        '''Boop someone!'''
        gif = await self.fetch_gif('anime boop nose')

        recipient = 'themselves' if interaction.user == user else user.display_name
        embed = (
            Embed(color=Color.secondary)
            .set_author(name=f'{interaction.user.display_name} booped {recipient}!', icon_url=interaction.user.avatar)
            .set_image(url=gif)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='hug')
    async def hug(self, interaction: discord.Interaction, user: discord.User):
        '''Hug someone!'''
        gif = await self.fetch_gif('anime hug cute')

        recipient = 'themselves' if interaction.user == user else user.display_name
        embed = (
            Embed(color=Color.secondary)
            .set_author(name=f'{interaction.user.display_name} hugged {recipient}!', icon_url=interaction.user.avatar)
            .set_image(url=gif)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='kiss')
    async def kiss(self, interaction: discord.Interaction, user: discord.User):
        '''Kiss someone!'''
        gif = await self.fetch_gif('anime kiss')

        recipient = 'themselves' if interaction.user == user else user.display_name
        embed = (
            Embed(color=Color.pink)
            .set_author(name=f'{interaction.user.display_name} kissed {recipient}!', icon_url=interaction.user.avatar)
            .set_image(url=gif)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='pat')
    async def pat(self, interaction: discord.Interaction, user: discord.User):
        '''Headpat someone!'''
        gif = await self.fetch_gif('anime headpat')

        recipient = 'themselves' if interaction.user == user else user.display_name
        embed = (
            Embed(color=Color.secondary)
            .set_author(name=f'{interaction.user.display_name} patted {recipient}!', icon_url=interaction.user.avatar)
            .set_image(url=gif)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='slap')
    async def slap(self, interaction: discord.Interaction, user: discord.User):
        '''Slap someone! (not too hard tho)'''
        gif = await self.fetch_gif('anime slap')

        recipient = 'themselves' if interaction.user == user else user.display_name
        embed = (
            Embed(color=Color.red)
            .set_author(name=f'{interaction.user.display_name} slapped {recipient}!', icon_url=interaction.user.avatar)
            .set_image(url=gif)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='profile')
    @app_commands.checks.bot_has_permissions(external_emojis=True)
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction, member: discord.Member | None = None):
        '''View user profile'''
        member = member if member is not None else interaction.user
        if member not in self.bot.members:
            member_stats = await self.bot.members.add(member)
        else:
            member_stats = self.bot.members(member)
        embed = (
            Embed(color=Color.secondary)
            .set_author(name=member.display_name, icon_url=member.display_avatar.url)
            .add_field(name='Level', value=f'{member_stats.xp.levels} {Emoji.xp}')
            .add_field(name='Credits', value=f'{member_stats.credits} {Emoji.credits}')
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='server')
    @app_commands.checks.bot_has_permissions(external_emojis=True)
    @app_commands.guild_only()
    async def server(self, interaction: discord.Interaction):
        '''Display server info'''
        guild = interaction.guild

        bots = 0
        for member in guild.members:
            if member.bot:
                bots += 1

        emoji_count = len(guild.emojis)
        sample = random.sample(guild.emojis, 10 if emoji_count > 10 else emoji_count)
        emojis = ''.join(str(emoji) for emoji in sample)

        banner_url = guild.banner.url if guild.banner is not None else None
        embed = (
            Embed(color=Color.primary)
            .set_author(name=guild.name, icon_url=guild.icon.url)
            .add_field(name=f'Owner {Emoji.owner}', value=f'`{guild.owner}`')
            .add_field(name=f'Server Boosts {Emoji.boost}', value=f'`{len(guild.premium_subscribers)}`')
            .add_field(name=f'Members `{guild.member_count}`', value=f'Users: `{guild.member_count-bots}`\nBots: `{bots}`')
            .add_field(name=f'Emoji `{emoji_count}`', value=emojis)
            .set_footer(text=f'ID: {guild.id}, created')
            .set_image(url=banner_url)
        )
        embed.timestamp = guild.created_at

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='leaderboard')
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction):
        '''Display leaderboard'''
        highscores: tuple[Score] = await self.bot.members.fetch_highscores()
        embed = (
            Embed(color=Color.primary)
            .set_author(name='Leaderboard', icon_url='attachment://unknown.png')
        )
        for i, score in enumerate(highscores):
            name = escape_markdown(str(score.member))
            embed.add_field(name=f'{i+1}. {name}', value=f'**```yml\nLevel: {score.xp.levels}\nXP: {score.xp.points}```**', inline=i == 0)

        await interaction.response.send_message(embed=embed, file=File('assets/dot.png', 'unknown.png'))


async def setup(bot: Tau):
    await bot.add_cog(Social(bot))

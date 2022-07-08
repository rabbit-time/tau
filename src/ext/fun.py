from __future__ import annotations
from typing import TYPE_CHECKING

import random

import aiohttp
import discord
from discord import Embed
from discord.app_commands import checks
from discord.app_commands import command, describe, Range
from discord.ext import commands

from utils import Color, Emoji

if TYPE_CHECKING:
    from tau import Tau


class Fun(commands.Cog):
    def __init__(self, bot: Tau):
        self.bot = bot

    async def image_embed(self, path: str, name: str | None = None) -> Embed:
        name = name if name else path.title()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://some-random-api.ml/img/{path}') as response:
                content = await response.json()
                url = content['link']

        embed = (
            Embed(description=f'{Emoji.link} **[{name}]({url})**', color=random.choice(tuple(Color)))
            .set_image(url=url)
        )
        return embed

    @command(name='8ball')
    async def _8ball(self, interaction: discord.Interaction, question: str):
        '''Ask the magic 8-ball a question'''
        responses = [
            'It is certain.', 'It is decidedly so.', 'Without a doubt.',
            'Yes – definitely.', 'You may rely on it.', 'As I see it, yes.',
            'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.',
            'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.',
            'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.',
            'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.'
        ]
        res = random.choice(responses)
        i = responses.index(res)
        if i < 10:
            color = Color.green
        elif i < 15:
            color = Color.gold
        else:
            color = Color.red

        embed = (
            Embed(color=color)
            .add_field(name=':8ball: magic 8-ball', value=f'> *"{res}"*')
        )

        await interaction.response.send_message(embed=embed)

    @command(name='bird')
    async def bird(self, interaction: discord.Interaction):
        '''Get a random bird'''
        embed = await self.image_embed('birb', 'Bird')
        await interaction.response.send_message(embed=embed)

    @command(name='cat')
    async def cat(self, interaction: discord.Interaction):
        '''Get a random cat'''
        embed = await self.image_embed('cat')
        await interaction.response.send_message(embed=embed)

    @command(name='dog')
    async def dog(self, interaction: discord.Interaction):
        '''Get a random dog'''
        embed = await self.image_embed('dog')
        await interaction.response.send_message(embed=embed)

    @command(name='fox')
    async def fox(self, interaction: discord.Interaction):
        '''Get a random fox'''
        embed = await self.image_embed('fox')
        await interaction.response.send_message(embed=embed)

    @command(name='koala')
    async def koala(self, interaction: discord.Interaction):
        '''Get a random koala'''
        embed = await self.image_embed('koala')
        await interaction.response.send_message(embed=embed)

    @command(name='panda')
    async def panda(self, interaction: discord.Interaction):
        '''Get a random panda'''
        embed = await self.image_embed('panda')
        await interaction.response.send_message(embed=embed)

    @command(name='redpanda')
    async def red_panda(self, interaction: discord.Interaction):
        '''Get a random red panda'''
        embed = await self.image_embed('red_panda', 'Red panda')
        await interaction.response.send_message(embed=embed)

    @command(name='ping')
    async def ping(self, interaction: discord.Interaction):
        '''Display the latency'''
        embed = (
            Embed(color=Color.gold)
            .set_author(name='Ping?')
            .add_field(name='Latency', value=f'**--.--**ms')
        )
        await interaction.response.send_message(embed=embed)

        embed.color = Color.green
        embed.set_author(name='Pong!') \
            .set_field_at(0, name='Latency', value=f'**{self.bot.latency*1000:.2f}**ms')

        message = await interaction.original_message()

        await message.edit(embed=embed)

    @command(name='coin')
    @describe(amount='the amount of coins to flip')
    @checks.bot_has_permissions(external_emojis=True)
    async def coin(self, interaction: discord.Interaction, amount: Range[int, 1, 84] = 1):
        '''Flip coins'''
        val = random.choices(range(2), k=amount)
        coin = Emoji.coin0, Emoji.coin1
        embed = Embed(description=f'{coin[val[0]]} **You got {["tails", "heads"][val[0]]}!**', color=Color.gold)
        if amount != 1:
            coins = ''
            for i, v in enumerate(val):
                coins += coin[v]
                if (i + 1) % 10 == 0:
                    coins += '\n'

            embed.description = f'**You got:\n\n{coins}**'
            embed.add_field(name='\u200b', value=f'**Heads: {val.count(1)}\nTails: {val.count(0)}**')

        await interaction.response.send_message(embed=embed)

    @command(name='dice')
    @describe(amount='the amount of dice to roll')
    @checks.bot_has_permissions(external_emojis=True)
    async def dice(self, interaction: discord.Interaction, amount: Range[int, 1, 84] = 1):
        '''Roll dice'''
        val = random.choices(range(6), k=amount)
        die = Emoji.dice[val[0]]
        embed = Embed(description=f'{die} **You got {val[0]}!**', color=Color.red)
        if amount != 1:
            dice = ''
            for i, v in enumerate(val):
                dice += Emoji.dice[v]
                if (i + 1) % 10 == 0:
                    dice += '\n'

            embed.description = f'**You got:\n\n{dice}**'
            for i in range(6):
                embed.add_field(name=Emoji.dice[i], value=f'**{val.count(i)}**')

        await interaction.response.send_message(embed=embed)


async def setup(bot: Tau):
    await bot.add_cog(Fun(bot))

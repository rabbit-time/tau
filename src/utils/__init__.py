from __future__ import annotations
from typing import TYPE_CHECKING

from collections import deque
from dataclasses import dataclass
import json

import aiohttp
import discord
from discord import Embed, File
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from tau import Tau


class aobject:
    '''inheriting this class allows for async constructors.'''
    async def __new__(cls, *args, **kwargs) -> aobject:
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)

        return instance


class CustomCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        bot: Tau = interaction.client

        if interaction.guild is not None and interaction.user not in bot.members:
            await bot.members.add(interaction.user)

        return True

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = Embed(color=Color.red)
        caught = False
        if isinstance(error, app_commands.CommandInvokeError):
            if isinstance(error.original, aiohttp.ClientError):
                embed.set_author(name='Server error - please try again later', icon_url='attachment://unknown.png')
                caught = True
        elif isinstance(error, app_commands.MissingPermissions):
            bulleted = '\n'.join(['• ' + perm for perm in error.missing_permissions])
            embed.set_author(name='You are missing the following permissions required to run this command:', icon_url='attachment://unknown.png')
            embed.description = bulleted
            caught = True
        elif isinstance(error, app_commands.BotMissingPermissions):
            bulleted = '\n'.join(['• ' + perm for perm in error.missing_permissions])
            embed.set_author(name=f'{self.client.conf.name} is missing the following permissions required to run this command:', icon_url='attachment://unknown.png')
            embed.description = bulleted
            caught = True

        if not caught:
            return await super().on_error(interaction, error)
        else:
            await interaction.response.send_message(embed=embed, file=File('assets/reddot.png', 'unknown.png'))


class Color:
    primary: int = 0x83b4ff
    secondary: int = 0xd9a8ff
    red: int = 0xf94a4a
    yellow: int = 0xffc20c
    gold: int = 0xffc669
    green: int = 0x65db80
    cyan: int = 0x68dbff
    pink: int = 0xffb0e6

    def __iter__(self) -> list[int]:
        attr: list[str] = []
        for anno in self.__annotations__:
            attr.append(getattr(self, anno))

        return attr


class ColorTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> discord.Color:
        return discord.Color.from_str(value)


class GuildTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: int) -> discord.Guild:
        # Faking a Context object
        ctx = discord.Object(id=0)
        ctx.bot = interaction.client

        try:
            # Using discord.py's guild converter implementation
            converter = commands.GuildConverter()
            guild = await converter.convert(ctx, value)
        except (commands.CommandError, commands.BadArgument):
            raise app_commands.TransformerError

        return guild


class MessageTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: int) -> discord.Message:
        # Faking a Context object
        ctx = discord.Object(id=0)
        ctx.bot = interaction.client
        ctx.guild = interaction.guild
        ctx.channel = interaction.channel

        try:
            # Using discord.py's message converter implementation
            converter = commands.MessageConverter()
            message = await converter.convert(ctx, value)
        except (commands.CommandError, commands.BadArgument):
            raise app_commands.TransformerError

        return message


class EmojiTransformer(app_commands.Transformer):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str) -> discord.PartialEmoji:
        # Faking a Context object
        ctx = discord.Object(id=0)
        ctx.bot = interaction.client

        try:
            # Using discord.py's guild converter implementation
            converter = commands.PartialEmojiConverter()
            emoji = await converter.convert(ctx, value)
        except (commands.CommandError, commands.BadArgument):
            raise app_commands.TransformerError

        return emoji


@dataclass
class Config:
    filename: str
    name: str
    repository: str
    version: str
    id: int
    passwd: str
    token: str
    tenor_api_key: str
    developer_guild_id: int

    @classmethod
    def from_json(cls, filename: str) -> Config:
        with open(f'./src/{filename}') as file:
            config = json.load(file)
            return cls(filename, *config.values())

    def as_dict(self) -> dict:
        return dict(
            name=self.name,
            repository=self.repository,
            version=self.version,
            id=self.id,
            passwd=self.passwd,
            token=self.token,
            tenor_api_key=self.tenor_api_key,
            developer_guild_id=self.developer_guild_id
        )

    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.as_dict(), file, indent=4)


class Emoji:
    credits = '<:credits:994851568174248016>'
    xp = '<:xp:993767283015028796>'
    sound = '<:sound:702809258974249011>'
    mute = '<:mute:702809258915397672>'
    hammer = '<:hammer:702793803677040692>'
    warn = '<:warn:706214120151711844>'
    on = '<:toggleon:686105837294452736>'
    off = '<:toggleoff:686105824065880150>'
    owner = '<:owner:697338812971483187>'
    boost = '<:boost:708098202339115119>'
    coin0 = '<:0_:784503048566210573>'
    coin1 = '<:1_:784503048453095485>'
    trash = '<:trashcan:797688643987701820>'
    link = '<:link:797723082134650900>'
    level_up = '<:level_up:992260045083508776>'
    rank_up = '<:rank_up:992260045972721664>'
    dice = (
        '<:d1:703190416606101535>',
        '<:d2:703190416820011049>',
        '<:d3:703190416924606484>',
        '<:d4:703190416962355252>',
        '<:d5:703190416987783269>',
        '<:d6:703190416933257232>'
    )


class DigitEmoji:
    '''A wrapper class for a list with a 1-1 equivalence between the index and the element. e.g. num[x] returns emoji for the digit x'''
    _emoji: list[str] = [
        '<:zero:992205986574114856>',
        '<:one:992205987396210788>',
        '<:two:992205988612550726>',
        '<:three:992205989937946624>',
        '<:four:992205991137509396>',
        '<:five:992205992311931003>',
        '<:six:992205993507295343>',
        '<:seven:992205995117924382>',
        '<:eight:992205996162293760>',
        '<:nine:992205997621903481>'
    ]

    @classmethod
    def from_int(cls, n: int) -> list[str]:
        emoji = []
        digits = cls._digits(n)
        for digit in digits:
            emoji.append(cls._emoji[digit])

        return emoji

    @staticmethod
    def _digits(n: int) -> deque[int]:
        digits = deque([])
        while n != 0:
            digits.appendleft(n % 10)
            n //= 10

        return digits

    def __len__(self):
        return len(self._emoji)

    def __getitem__(self, index: int):
        return self._emoji[index]

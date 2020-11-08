import time

import discord
from discord import Game, Object, Permissions
from discord.ext import commands
from discord.utils import oauth_url

import ccp
import utils

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        prefix = self.bot.guilds_.default['prefix']
        await self.bot.change_presence(activity=Game(name=f'{prefix}tau'))
        
        ccp.ready(f'Logged in as {self.bot.user.name}')
        ccp.ready(f'ID: {self.bot.user.id}')
        self.bot.url = oauth_url(client_id=self.bot.user.id, permissions=Permissions(permissions=8))
        ccp.ready(f'URL: \u001b[1m\u001b[34m{self.bot.url}\u001b[0m')

        for guild in self.bot.guilds:
            if guild.id not in self.bot.guilds_.keys():
                await self.bot.guilds_.insert(guild.id)
                if guild.system_channel:
                   await self.bot.guilds_.update(guild.id, 'system_channel', guild.system_channel.id)

def setup(bot):
    bot.add_cog(OnReady(bot))
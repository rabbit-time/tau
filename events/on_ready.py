import asyncio
import time

import discord
from discord import Game, Object, Permissions
from discord.ext import commands
from discord.utils import oauth_url

import ccp
import utils
from utils import automute

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        prefix = self.bot.guilds_.default['prefix']
        await self.bot.change_presence(activity=Game(name=f'{prefix}tau'))
        
        if not self.bot.boot:
            return

        self.bot.boot = False
        
        ccp.ready(f'Logged in as {self.bot.user.name}')
        ccp.ready(f'ID: {self.bot.user.id}')
        self.bot.url = oauth_url(client_id=self.bot.user.id, permissions=Permissions(permissions=8))
        ccp.ready(f'URL: \u001b[1m\u001b[34m{self.bot.url}\u001b[0m')

        for guild in self.bot.guilds:
            if guild.id not in self.bot.guilds_.keys():
                await self.bot.guilds_.insert(guild.id)
                if guild.system_channel:
                   await self.bot.guilds_.update(guild.id, 'system_channel', guild.system_channel.id)

        records = await self.bot.con.fetch('SELECT user_id, guild_id, muted FROM members WHERE muted != -1')
        for record in records:
            user_id, guild_id, muted = record.values()
            self.bot.mute_tasks[user_id, guild_id] = self.bot.loop.create_task(automute(self.bot, user_id, guild_id, muted))
        
        records = await self.bot.con.fetch('SELECT * FROM reminders')
        for record in records:
            user_id, remind_time, channel_id, reminder = record.values()
            chan = self.bot.get_channel(channel_id)
            if chan:
                member = chan.guild.get_member(user_id)
                if member:
                    self.bot.loop.create_task(utils.remind(self.bot, member, chan, reminder, remind_time))
                else:
                    await self.bot.reminders.delete((user_id, remind_time))

def setup(bot):
    bot.add_cog(OnReady(bot))
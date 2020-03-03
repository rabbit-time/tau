import asyncio
import time

import discord
from discord import Game, Object, Permissions
from discord.ext import commands
from discord.utils import oauth_url

import ccp
from utils import automute, autodetain

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.id not in self.bot.guilds_.keys():
                await self.bot.guilds_.insert(guild.id)
                if guild.system_channel:
                   await self.bot.guilds_.update(guild.id, 'system_channel', guild.system_channel.name)

        prefix = self.bot.guilds_.default['prefix']
        await self.bot.change_presence(activity=Game(name=f'{prefix}help'))
        ccp.ready(f'Logged in as {self.bot.user.name}')
        ccp.ready(f'ID: {self.bot.user.id}')
        self.bot.url = oauth_url(client_id=self.bot.user.id, permissions=Permissions(permissions=8))
        ccp.ready(f'URL: \u001b[1m\u001b[34m{self.bot.url}\u001b[0m')

        cur = await self.bot.con.execute('SELECT * FROM mutes WHERE muted != -1')
        records = await cur.fetchall()
        for user_id, guild_id, muted in records:
            self.bot.mute_tasks[user_id, guild_id] = self.bot.loop.create_task(automute(self.bot, user_id, guild_id, muted))

        cur = await self.bot.con.execute('SELECT * FROM detains')
        records = await cur.fetchall()
        for user_id, guild_id, channel_id, msg_id, timeout in records:
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(user_id)
            channel = guild.get_channel(channel_id)
            msg = await channel.fetch_message(msg_id)
            if not member:
                await guild.ban(Object(id=user_id))
                await self.bot.detains.delete((user_id, guild_id))
                continue
            
            self.bot.loop.create_task(autodetain(self.bot, member, guild, msg, timeout))

def setup(bot):
    bot.add_cog(OnReady(bot))
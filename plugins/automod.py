import datetime
import re

import discord
from discord import Embed
from discord.ext import commands

import ccp
from utils import automute, emoji

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def automod_enabled(self, guild):
        if not self.bot.guilds_[guild.id]['automod']:
            return

    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.guild:
            return

        member = msg.author
        guild = msg.guild

        self.automod_enabled(msg.guild)

        pattern = r'(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li|sg)|discordapp\.com\/invite)\/.+[a-z]'
        match = re.search(pattern, msg.content)
        if match:
            bind = guild.get_role(self.bot.guilds_[guild.id]['bind_role'])
            mod = guild.get_role(self.bot.guilds_[guild.id]['mod_role'])
            admin = guild.get_role(self.bot.guilds_[guild.id]['admin_role'])

            if not bind or mod in member.roles or admin in member.roles:
                return

            await msg.delete()
            await member.add_roles(bind, reason='Sent an invite URL')

            await self.bot.members.update((member.id, guild.id), 'muted', str(datetime.datetime.utcnow()))
            
            embed = Embed(description=f'**{emoji["mute"]} You have been muted by `Automod`.**')
            embed.set_author(name=guild, icon_url=guild.icon_url)
            embed.add_field(name='Reason', value='*Sent an invite URL*')
            embed.set_footer(text='Muted')
            embed.timestamp = datetime.datetime.utcnow()

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

            embed.description = f'**{emoji["mute"]} {member.mention} has been muted.**'
            embed.set_author(name='Automod', icon_url=self.bot.user.avatar_url)

            await msg.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Automod(bot))
import datetime

import discord
from discord import Embed, File
from discord.ext import commands

import ccp
import utils

class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            await member.guild.fetch_ban(member)
        except (discord.Forbidden, discord.NotFound):
            pass
        else:
            return

        ccp.event(f'{str(member)} has left {str(member.guild)}', event='MEMBER_REM')

        if member.bot:
            return

        cache = self.bot.guilds_
        guild = member.guild
        if cache[guild.id]['goodbye_messages'] and (chan := member.guild.get_channel(cache[guild.id]['system_channel'])):
            msg = cache[guild.id]['goodbye_message'].replace('@user', str(member)).replace('@name', member.display_name).replace('@mention', member.mention).replace('@guild', guild.name)
            embed = Embed(description=msg, color=utils.Color.red)
            embed.set_author(name=member, icon_url=member.avatar_url)
            embed.set_footer(text='Leave', icon_url='attachment://unknown.png')
            embed.timestamp = datetime.datetime.utcnow()
            
            await chan.send(file=File('assets/leave.png', 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(OnMemberRemove(bot))
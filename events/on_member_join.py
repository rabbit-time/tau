import time

from discord import Embed
from discord.ext import commands

import ccp

class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        ccp.event(f'{str(member)} has joined {str(member.guild)}', event='MEMBER_ADD')

        if member.bot:
            return

        cache = self.bot.guilds_
        guild = member.guild
        if cache[guild.id]['welcome_messages'] and (chan := guild.get_channel(cache[guild.id]['system_channel'])):
            await chan.send(cache[guild.id]['welcome_message'].replace('@user', member.display_name).replace('@mention', member.mention).replace('@guild', guild.name))

        if self.bot.members.get((member.id, guild.id)):
            muted = self.bot.members[member.id, guild.id]['muted']
            if muted > int(time.time()):
                role = member.guild.get_role(self.bot.guilds_[guild.id]['bind_role'])
                await member.add_roles(role)

        autorole = self.bot.guilds_[member.guild.id]['autorole']
        if role := guild.get_role(autorole):
            await member.add_roles(role)

        if self.bot.ranks.get(guild.id) and (role_ids := self.bot.ranks[guild.id]['role_ids']):
            role_ids = role_ids.split()
            if role := guild.get_role(int(role_ids[0])):
                await member.add_roles(role)

def setup(bot):
    bot.add_cog(OnMemberJoin(bot))
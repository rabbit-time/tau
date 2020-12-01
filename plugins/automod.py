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

    @commands.Cog.listener()
    async def on_message(self, msg):
        if not msg.guild:
            return

        member = msg.author
        guild = msg.guild

        if not self.bot.guilds_[guild.id]['automod']:
            return

        pattern = r'(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li|sg)|discordapp\.com\/invite)\/.+[a-z]'
        match = re.search(pattern, msg.content)
        if match:
            mute_role = guild.get_role(self.bot.guilds_[guild.id]['mute_role'])

            perms = member.guild_permissions
            if perms.kick_members or perms.ban_members:
                return

            await msg.delete()
            
            muted = self.bot.members[member.id, guild.id]['muted']
            if not muted:
                reason = 'Sent an invite URL'
                await member.add_roles(mute_role, reason=reason)

                await self.bot.members.update((member.id, guild.id), 'muted', str(datetime.datetime.utcnow()))
                
                embed = Embed(description=f'**{emoji["mute"]} You have been muted by `Automod`.**')
                embed.set_author(name=guild, icon_url=guild.icon_url)
                embed.add_field(name='Reason', value=f'*{reason}*')
                embed.set_footer(text='Muted')
                embed.timestamp = datetime.datetime.utcnow()

                try:
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass

                embed.description = f'**{emoji["mute"]} {member.mention} has been muted.**'
                embed.set_author(name='Automod', icon_url=self.bot.user.avatar_url)

                msg = await msg.channel.send(embed=embed)

                await self.bot.cogs['Moderation']._log(member, guild, msg, 'mute', reason)
                await self.bot.cogs['Logging'].on_member_mute(guild.me, member, reason)

def setup(bot):
    bot.add_cog(Automod(bot))
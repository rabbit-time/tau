import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import find

import utils
from utils import emoji

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_webhook(self, guild):
        if not guild:
            return

        chan = guild.get_channel(self.bot.guilds_[guild.id]['log_channel'])
        if chan:
            webhooks = await chan.webhooks()
            webhook = find(lambda w: w.user.id == self.bot.user.id, webhooks)
            if not webhook:
                await self.bot.guilds_.update(guild.id, 'log_channel', 0)
        elif self.bot.guilds_[guild.id]['log_channel'] != 0:
            await self.bot.guilds_.update(guild.id, 'log_channel', 0)
            return
        else:
            return

        return webhook
    
    async def on_member_kick(self, kicker, kicked, reason):
        webhook = await self.get_webhook(kicker.guild)
        if webhook:
            embed = Embed(title='Kick', description=f'**{emoji["hammer"]} Kicked `{kicked}`.**', color=utils.Color.red)
            embed.set_author(name=kicker, icon_url=kicker.avatar_url)
            if reason:
                embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)
    
    async def on_member_warn(self, warner, warned, reason):
        webhook = await self.get_webhook(warner.guild)
        if webhook:
            embed = Embed(title='Warn', description=f'**{emoji["warn"]} Warned `{warned}`.**', color=utils.Color.gold)
            embed.set_author(name=warner, icon_url=warner.avatar_url)
            embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)

    async def on_member_mute(self, muter, muted, reason):
        webhook = await self.get_webhook(muter.guild)
        if webhook:
            embed = Embed(title='Mute', description=f'**{emoji["mute"]} Muted `{muted}`.**', color=utils.Color.red)
            embed.set_author(name=muter, icon_url=muter.avatar_url)
            if reason:
                embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)
    
    async def on_member_unmute(self, unmuter, unmuted, reason):
        webhook = await self.get_webhook(unmuter.guild)
        if webhook:
            embed = Embed(title='Unmute', description=f'**{emoji["sound"]} Unmuted `{unmuted}`.**', color=utils.Color.green)
            embed.set_author(name=unmuter, icon_url=unmuter.avatar_url)
            if reason:
                embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)

    async def on_member_ban(self, banner, banned, reason):
        webhook = await self.get_webhook(banner.guild)
        if webhook:
            embed = Embed(title='Ban', description=f'**{emoji["hammer"]} Banned `{banned}`.**', color=utils.Color.red)
            embed.set_author(name=banner, icon_url=banner.avatar_url)
            if reason:
                embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)

    async def on_member_unban(self, unbanner, unbanned, reason):
        webhook = await self.get_webhook(unbanner.guild)
        if webhook:
            embed = Embed(title='Unban', description=f'**{emoji["hammer"]} Unbanned `{unbanned}`.**', color=utils.Color.green)
            embed.set_author(name=unbanner, icon_url=unbanner.avatar_url)
            if reason:
                embed.add_field(name='Reason', value=f'*{reason}*')

            await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        invites = self.bot.invites_
        if invites.get(invite.guild.id):
            invites[invite.guild.id].append(invite)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        invites = self.bot.invites_
        if invites.get(invite.guild.id):
            for i, inv in enumerate(invites[invite.guild.id]):
                if inv.code == invite.code:
                    del invites[i]
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        guild = member.guild
        webhook = await self.get_webhook(guild)
        if webhook:
            try:
                old = self.bot.invites_[guild.id]
                new = self.bot.invites_[guild.id] = await guild.invites()
                if 'VANITY_URL' in guild.features:
                    vanity = await guild.vanity_invite()
                    new.append(vanity)
            except:
                return

            invite = None
            missing = []
            for inv in old:
                cor = find(lambda i: i.url == inv.url, new)
                if cor:
                    if cor.uses > inv.uses:
                        invite = cor
                        break
                else:
                    missing.append(inv)

            if not invite:
                for inv in new:
                    cor = find(lambda i: i.url == inv.url, old)
                    if not cor and inv.uses > 0:
                        invite = inv
                        break
                
                if missing and not invite:
                    for m in missing:
                        if m.max_uses - m.uses == 1:
                            invite = m

            embed = Embed(title='Member join', color=utils.Color.green)
            embed.set_author(name=member, icon_url=member.avatar_url)
            if invite:
                embed.add_field(name='Invite', value=f'**[{invite.code}]({invite.url})**')

            await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        prefix = self.bot.guilds_[msg.guild.id]['prefix']
        if not msg.content.startswith(prefix) and (msg.author not in self.bot.suppressed.keys() or self.bot.suppressed.get(msg.author) != msg.channel):
            webhook = await self.get_webhook(msg.guild)
            if webhook:
                embed = Embed(title='Message delete', description=f'> {msg.content}', color=utils.Color.red)
                embed.set_author(name=msg.author, icon_url=msg.author.avatar_url)

                await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot or before.content == after.content:
            return

        webhook = await self.get_webhook(before.guild)
        if webhook:
            if len(before.content) > 1024 or len(after.content) > 1024:
                embed = Embed(title='Message edit', description=f'**Before**\n> {before.content}', color=utils.Color.gold)
                embed.set_author(name=after.author, icon_url=after.author.avatar_url)

                await webhook.send(embed=embed)

                embed.remove_author()
                embed.title = Embed.Empty
                embed.description = f'**After**\n> {after.content}'
                embed.add_field(name='Source', value=f'**[Jump!]({after.jump_url})**')

                await webhook.send(embed=embed)
            else:
                embed = Embed(title='Message edit', color=utils.Color.gold)
                embed.set_author(name=after.author, icon_url=after.author.avatar_url)
                embed.add_field(name='Before', value=f'> {before.content}', inline=False)
                embed.add_field(name='After', value=f'> {after.content}', inline=False)
                embed.add_field(name='Source', value=f'**[Jump!]({after.jump_url})**')

                await webhook.send(embed=embed)

def setup(bot):
    bot.add_cog(Logging(bot))
import asyncio
import datetime
import time
import re

import discord
from discord import Embed, File, Object, PermissionOverwrite
from discord.ext import commands
from discord.utils import escape_markdown

import perms
import utils
from utils import automute, emoji, findrole

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='ban', aliases=[], usage='ban <member> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        '''Ban a member.
        `reason` will show up in the audit log\n
        **Example:```yml\n.ban @Tau#4272\n.ban 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be banned.', delete_after=5)

        await member.ban(reason=reason, delete_message_days=0)

        desc = f'**{emoji["hammer"]} {member} has been banned.**'
        if reason:
            desc += f'\nReason: *{reason}*'

        embed = Embed(description=desc, color=0xff4e4e)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='blacklist', aliases=[], usage='blacklist <id> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def blacklist(self, ctx, id: int, *, reason=None):
        '''Blacklist a user.
        This is also known as hackbanning. Use the `ban` command for ordinary bans.
        `reason` will show up in the audit log\n
        **Example:```yml\n.blacklist 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        try:
            ban = await ctx.guild.fetch_ban(Object(id=id))
            return await ctx.send(f'**{ban.user}** has already been blacklisted.', delete_after=5)
        except discord.NotFound:
            pass
        
        user = Object(id=id)
        await ctx.guild.ban(user, reason=reason, delete_message_days=0)
        ban = await ctx.guild.fetch_ban(user)

        desc = f'**{emoji["hammer"]} {ban.user} has been blacklisted.**'
        if reason:
            desc += f'\nReason: *{reason}*'

        embed = Embed(description=desc, color=0xff4e4e)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='delete', aliases=['del', 'purge'], usage='delete [quantity=1] [members]')
    @commands.bot_has_permissions(manage_messages=True)
    async def delete(self, ctx, n: int = 1, *members: discord.Member):
        '''Delete messages from a channel.
        Specify `quantity` to delete multiple messages. The command message will not be included in this amount.
        `quantity` cannot be greater than 100 and messages that are more than 14 days old cannot be deleted.
        You can filter messages by member with `members`. Multiple members may be mentioned.\n
        **Example:```yml\n.delete 5\n.del 8 @Tau#4272```**
        '''
        await ctx.message.delete()

        if not 0 < n <= 100:
            raise commands.BadArgument

        messages = []
        async for msg in ctx.channel.history(limit=None):
            if msg.author in members or not members:
                messages.append(msg)
                if len(messages) == n:
                    break

        await ctx.channel.delete_messages(messages)

        content = f'Deleted {n} message'
        if n != 1:
            content += 's'

        embed = Embed(description=f'**```diff\n- {content}!```**', color=0xff4e4e)
        
        await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='kick', aliases=[], usage='kick <member> [reason]')
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        '''Kick a member.
        `reason` will show up in the audit log\n
        **Example:```yml\n.kick @Tau#4272\n.kick 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be kicked.', delete_after=5)

        await member.kick(reason=reason)

        desc = f'**{emoji["hammer"]} {member} has been kicked.**'
        if reason:
            desc += f'\nReason: *{reason}*'

        embed = Embed(description=desc, color=0xff4e4e)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='mute', aliases=['hush'], usage='mute <member> [limit] [reason]')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def mute(self, ctx, member: discord.Member, limit=None, *, reason=None):
        '''Mute a user.
        `limit` is how long to mute the user for.
        `reason` is a reason that will show up in the audit log.
        Suffix with *`m`*, *`d`*, or *`h`* to specify unit of time.
        If `limit` is omitted, the user will be muted indefinitely.
        Mute limits are capped at 6 months to prevent memory leaks.\n
        **Example:```yml\n.mute @Tau#4272 10m\n.hush 608367259123187741 1h being a baddie```**
        '''
        await ctx.message.delete()

        if member.bot:
            return

        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)
        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be muted.', delete_after=5)

        if not self.bot.members.get((member.id, ctx.guild.id)):
            await self.bot.members.insert((member.id, ctx.guild.id))
        elif self.bot.members[member.id, ctx.guild.id]['muted'] != -1:
            return await ctx.send(f'**{member.display_name}** has already been muted.', delete_after=5)

        try:
            time_, delay = utils.parse_time(limit)
        except:
            delay = None

        if delay:
            SEMIYEAR = 1555200
            if delay > SEMIYEAR:
                raise commands.BadArgument

            total = delay + int(time.time())
            self.bot.mute_tasks[member.id, ctx.guild.id] = self.bot.loop.create_task(automute(self.bot, member.id, ctx.guild.id, total))
        else:
            total = 0
            if reason:
                reason = f'{limit} {reason}'
            elif limit:
                reason = limit

        await member.add_roles(bind, reason=reason)
        await self.bot.members.update((member.id, ctx.guild.id), 'muted', total)

        desc = f'**{emoji["mute"]} {member.mention} has been muted.**'
        if reason:
            desc += f'\nReason: *{reason}*'
        
        embed = Embed(description=desc)
        embed.set_author(name=escape_markdown(ctx.author.display_name), icon_url=ctx.author.avatar_url)
        if total != 0:
            file = File('assets/clock.png', 'unknown.png')
            embed.set_footer(text=time_, icon_url='attachment://unknown.png')
            embed.timestamp = datetime.datetime.fromtimestamp(total).astimezone(tz=datetime.timezone.utc)
        else:
            file = None
            embed.set_footer(text='Muted')
            embed.timestamp = datetime.datetime.utcnow()

        await ctx.send(file=file, embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='softban', aliases=[], usage='softban <member> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        '''Softban a member.
        This will ban and then immediately unban a member to delete their messages.
        `reason` will show up in the audit log\n
        **Example:```yml\n.softban @Tau#4272\n.softban 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be banned.', delete_after=5)

        await member.ban(reason=reason, delete_message_days=7)
        await member.unban(reason=reason)

        desc = f'**{emoji["hammer"]} {member} has been softbanned.**'
        if reason:
            desc += f'\nReason: *{reason}*'

        embed = Embed(description=desc, color=0xff4e4e)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='unban', aliases=[], usage='unban <id> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def unban(self, ctx, id: int, *, reason=None):
        '''Unban a member.
        `reason` will show up in the audit log\n
        **Example:```yml\n.unban 608367259123187741 being a good boi```**
        '''
        await ctx.message.delete()

        try:
            ban = await ctx.guild.fetch_ban(Object(id=id))
            user = ban.user
        except discord.NotFound:
            return await ctx.send(f'**`{id}`** has not been banned.', delete_after=5)

        await ctx.guild.unban(user, reason=reason)

        desc = f'**{emoji["hammer"]} {user} has been unbanned.**'
        if reason:
            desc += f'\nReason: *{reason}*'

        embed = Embed(description=desc, color=0x2aa198)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='unmute', usage='unmute <member>')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def unmute(self, ctx, *, member: discord.Member):
        '''Unmute a user.\n
        **Example:```yml\n.unmute @Tau#4272\n.unmute 608367259123187741```**
        '''
        await ctx.message.delete()
        
        if member == ctx.author or member.bot:
            return

        if not self.bot.members.get((member.id, ctx.guild.id)) or self.bot.members[member.id, ctx.guild.id]['muted'] == -1:
            return await ctx.send(f'**{member.display_name}** has not been muted.', delete_after=5)

        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)
        await member.remove_roles(bind)

        await self.bot.members.update((member.id, ctx.guild.id), 'muted', -1)
        if task := self.bot.mute_tasks.get((member.id, ctx.guild.id)):
            task.cancel()
            del self.bot.mute_tasks[member.id, ctx.guild.id]

        embed = Embed(description=f'**{emoji["sound"]} {member.mention} has been unmuted.**')
        embed.set_author(name=escape_markdown(ctx.author.display_name), icon_url=ctx.author.avatar_url)
        embed.timestamp = datetime.datetime.utcnow()

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderation(bot))
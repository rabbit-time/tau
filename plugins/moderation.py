import asyncio
import datetime
import time
import re
from typing import Union

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

    async def _log(self, user: Union[discord.Member, discord.User], guild: discord.Guild, action: str, reason: str):
        async with self.bot.pool.acquire() as con:
            sql = 'INSERT INTO modlog VALUES ($1, $2, $3, $4, $5)'
            await con.execute(sql, user.id, guild.id, action, int(time.time()), reason)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='ban', aliases=[], usage='ban <member> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        '''Ban a member.
        `reason` will show up in the audit log\n
        **Example:```yml\n.ban @Tau#4272\n.ban 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be banned.', delete_after=5)

        embed = Embed(description=f'**{emoji["hammer"]} You have been banned by `{ctx.author}`.**', color=utils.Color.red)
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.ban(reason=reason, delete_message_days=0)

        await self._log(member, ctx.guild, 'ban', reason if reason else '')

        embed.description = f'**{emoji["hammer"]} {member} has been banned.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='blacklist', aliases=[], usage='blacklist <id> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def blacklist(self, ctx, id: int, *, reason: str = None):
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
        
        try:
            user = Object(id=id)
            await ctx.guild.ban(user, reason=reason, delete_message_days=0)
            ban = await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            return await ctx.send(f'User with **`{id}`** could not be found.', delete_after=5)

        await self._log(user, ctx.guild, 'ban', reason if reason else '')

        embed = Embed(description=f'**{emoji["hammer"]} {ban.user} has been blacklisted.**', color=utils.Color.red)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

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

        embed = Embed(description=f'**```diff\n- {content}!```**', color=utils.Color.red)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        
        await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='kick', aliases=[], usage='kick <member> [reason]')
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        '''Kick a member.
        `reason` will show up in the audit log\n
        **Example:```yml\n.kick @Tau#4272\n.kick 608367259123187741 being a baddie```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be kicked.', delete_after=5)

        embed = Embed(description=f'**{emoji["hammer"]} You have been kicked by `{ctx.author}`.**', color=utils.Color.red)
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')
        
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.kick(reason=reason)

        await self._log(member, ctx.guild, 'kick', reason if reason else '')

        embed.description = f'**{emoji["hammer"]} {member} has been kicked.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='mute', aliases=['hush'], usage='mute <member> [limit] [reason]')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def mute(self, ctx, member: discord.Member, limit=None, *, reason: str = None):
        '''Mute a member.
        `limit` is how long to mute the member for.
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
        elif self.bot.members[member.id, ctx.guild.id]['muted']:
            return await ctx.send(f'**{member.display_name}** has already been muted.', delete_after=5)

        try:
            time_, delta = utils.parse_time(limit)
        except:
            delta = None

        now = datetime.datetime.utcnow()
        if delta:
            SEMIYEAR = 1555200
            if delta.total_seconds() > SEMIYEAR:
                raise commands.BadArgument

            timeout = now + delta
            self.bot.mute_tasks[member.id, ctx.guild.id] = self.bot.loop.create_task(automute(self.bot, member.id, ctx.guild.id, timeout))
        else:
            timeout = now
            if reason:
                reason = f'{limit} {reason}'
            elif limit:
                reason = limit
        
        await member.add_roles(bind, reason=reason)
        await self.bot.members.update((member.id, ctx.guild.id), 'muted', str(timeout))

        await self._log(member, ctx.guild, 'mute', reason if reason else '')

        embed = Embed(description=f'**{emoji["mute"]} You have been muted by `{ctx.author}`.**')
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

        if timeout != now:
            file = File('assets/clock.png', 'unknown.png')
            embed.set_footer(text=time_, icon_url='attachment://unknown.png')
            embed.timestamp = timeout
        else:
            file = None
            embed.set_footer(text='Muted')
            embed.timestamp = datetime.datetime.utcnow()

        try:
            await member.send(file=file, embed=embed)
        except discord.Forbidden:
            pass

        embed.description = f'**{emoji["mute"]} {member.mention} has been muted.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(file=File('assets/clock.png', 'unknown.png') if file else None, embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='record', aliases=['history'], usage='record <member> [index]')
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, external_emojis=True)
    async def record(self, ctx, member: Union[discord.Member, discord.User], i: int = None):
        '''View a user's moderation record.
        Use `index` to view details on a log.\n
        **Example:```yml\n.record @Tau#4272```**
        '''
        async with self.bot.pool.acquire() as con:
            query = 'SELECT action, time, reason FROM modlog WHERE user_id = $1 AND guild_id = $2 ORDER BY time DESC'
            records = await con.fetch(query, member.id, ctx.guild.id)

        plural = 's' if len(records) != 1 else ''
        embed = Embed(title=f'Mod record: {len(records)} result{plural}')
        embed.set_author(name=member, icon_url=member.avatar_url)

        if not records:
            embed.description = 'This user does not have a mod record.'
            return await ctx.send(embed=embed)

        if i != None:
            try:
                action, time_, reason = records[i-1].values()
            except IndexError:
                return await ctx.send(f'{ctx.author.mention} Record with index `{i}` does not exist.`', delete_after=5)

            date = time.strftime('%d.%m.%Y %H:%M:%S UTC', time.gmtime(time_))
            embed.title = f'Record #{i}'
            embed.description = f'**Action: `{action}`**'
            embed.add_field(name='Reason', value=reason if reason else 'n/a')
            embed.set_footer(text=date)

            return await ctx.send(embed=embed)

        i = 1
        pages = []
        logs = []
        for record in records:
            action, time_, _ = record.values()
            align = ' ' if i < 10 else ''
            space = ' ' * (7-len(action))
            date = datetime.date.fromtimestamp(time_)
            log = f'**`{i}.{align} {action+space} | {date}`**'
            if len(logs) == 20:
                pages.append('\n'.join(logs))
                logs.clear()

            logs.append(log)
            i += 1
        
        if logs:
            pages.append('\n'.join(logs))
        
        page = 1
        embed.description = pages[0]
        embed.set_footer(text=f'Page {page}/{len(pages)}')

        msg = await ctx.send(embed=embed)

        if len(pages) > 1:
            emojis = (utils.emoji['start'], utils.emoji['previous'], utils.emoji['next'], utils.emoji['end'], utils.emoji['stop'])
            for emoji in emojis:
                await msg.add_reaction(emoji)

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=90, check=lambda reaction, user: str(reaction.emoji) in emojis and reaction.message.id == msg.id and not user.bot)
                
                    await reaction.remove(user)
                    emoji = str(reaction.emoji)
                    if user != ctx.author or emoji not in emojis:
                        continue
                    
                    if emoji == emojis[0]: # start
                        if page == 1:
                            continue
                        
                        page = 1
                    elif emoji == emojis[1]: # previous
                        if page == 1:
                            continue

                        page -= 1
                    elif emoji == emojis[2]: # next
                        if page == len(pages):
                            continue

                        page += 1
                    elif emoji == emojis[3]: # end
                        if page == len(pages):
                            continue

                        page = len(pages)
                    elif emoji == emojis[4]: # stop
                        raise asyncio.TimeoutError

                    embed.description = pages[page-1]
                    embed.set_footer(text=f'Page {page}/{len(pages)}')

                    await msg.edit(embed=embed)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    break

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='softban', aliases=[], usage='softban <member> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def softban(self, ctx, member: discord.Member, *, reason: str = None):
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

        embed = Embed(description=f'**{emoji["hammer"]} You have been softbanned by `{ctx.author}`.**', color=utils.Color.red)
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await member.ban(reason=reason, delete_message_days=7)
        await member.unban(reason=reason)

        await self._log(member, ctx.guild, 'softban', reason if reason else '')

        embed.description = f'**{emoji["hammer"]} {member} has been softbanned.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='unban', aliases=[], usage='unban <id> [reason]')
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def unban(self, ctx, id: int, *, reason: str = None):
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

        await self._log(user, ctx.guild, 'unban', reason if reason else '')

        embed = Embed(description=f'**{emoji["hammer"]} {user} has been unbanned.**', color=utils.Color.green)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='unmute', usage='unmute <member> [reason]')
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        '''Unmute a member.\n
        **Example:```yml\n.unmute @Tau#4272\n.unmute 608367259123187741 Mistakenly muted```**
        '''
        await ctx.message.delete()
        
        if member == ctx.author or member.bot:
            return

        if not self.bot.members.get((member.id, ctx.guild.id)):
            await self.bot.members.insert((member.id, ctx.guild.id))
        elif not self.bot.members[member.id, ctx.guild.id]['muted']:
            return await ctx.send(f'**{member.display_name}** has not been muted.', delete_after=5)

        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)
        await member.remove_roles(bind)

        if task := self.bot.mute_tasks.get((member.id, ctx.guild.id)):
            task.cancel()
            del self.bot.mute_tasks[member.id, ctx.guild.id]

        await self._log(member, ctx.guild, 'unmute', reason if reason else '')
        self.bot.members[member.id, ctx.guild.id]['muted'] = None
        async with self.bot.pool.acquire() as con:
            query = 'UPDATE members SET muted = $1 WHERE user_id = $2 AND guild_id = $3'
            await con.execute(query, None, member.id, ctx.guild.id)

        embed = Embed(description=f'**{emoji["sound"]} You have been unmuted by `{ctx.author}`.**')
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        embed.timestamp = datetime.datetime.utcnow()
        if reason:
            embed.add_field(name='Reason', value=f'*{reason}*')

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        embed.description = f'**{emoji["sound"]} {member.mention} has been unmuted.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)
    
    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='warn', usage='warn <member> <reason>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        '''Warn a member.\n
        **Example:```yml\n.warn @Tau#4272 for being Tau```**
        '''
        await ctx.message.delete()

        mod = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['mod_role'])
        admin = ctx.guild.get_role(self.bot.guilds_[ctx.guild.id]['admin_role'])

        if mod in member.roles or admin in member.roles or member.id == ctx.guild.owner_id:
            return await ctx.send(f'{ctx.author.mention} Mods and admins cannot be warned.', delete_after=5)

        await self._log(member, ctx.guild, 'warn', reason)

        embed = Embed(description=f'**{emoji["warn"]} You have been warned by `{ctx.author}`.**', color=utils.Color.gold)
        embed.set_author(name=ctx.guild, icon_url=ctx.guild.icon_url)
        embed.add_field(name='Reason', value=f'*{reason}*')

        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        embed.description = f'**{emoji["warn"]} {member.mention} has been warned.**'
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderation(bot))
import asyncio
import time
import re

from discord import Embed, File, PermissionOverwrite
from discord.ext import commands

import perms
from utils import autodetain, automute, findrole, res_member

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='detain', aliases=['bind'], description='Detains a member', usage='detain <mention>')
    async def detain(self, ctx, mention):
        '''Detain a member.
        This command replaces a ban functionality to implement
        a democratic moderation system. Detained members will
        be given the **`bind_role`** and will be blocked from
        accessing the guild with the exception of the case
        channel. Staff members will vote on whether the member
        shall be permenantly banned.

        *mention* can be a mention or a user ID.\n
        **Example:```yml\n.detain @Tau#4272\n.bind 608367259123187741```**
        '''
        member = await res_member(ctx)

        if member == ctx.author or member.bot:
            return

        mod = findrole(self.bot.guilds_[ctx.guild.id]['mod_role'], ctx.guild)
        admin = findrole(self.bot.guilds_[ctx.guild.id]['admin_role'], ctx.guild)
        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)

        await ctx.message.delete()

        await member.add_roles(bind)

        if member in mod.members or member in admin.members:
            return await ctx.send('Staff members cannot be detained.', delete_after=5)

        if self.bot.detains.get((member.id, ctx.guild.id)):
            return await ctx.send(f'**{member.display_name}** has already been detained.', delete_after=5)

        await ctx.send(f'**<:cuffs:678393038095122461> | {member.display_name}** has been detained.')

        overwrites = {
                ctx.guild.default_role: PermissionOverwrite(read_messages=False),
                mod: PermissionOverwrite(read_messages=True),
                admin: PermissionOverwrite(read_messages=True)
        }
        for cat in ctx.guild.categories:
            if cat.name.lower() == 'appeals':
                appeals = cat
                break
        else:
            appeals = await ctx.guild.create_category('appeals', overwrites=overwrites)

        now = int(time.time())
        date = time.strftime('%d.%m.%Y %H:%M:%S UTC', time.gmtime(now+86400))
        overwrites[member] = PermissionOverwrite(read_messages=True, send_messages=True, add_reactions=False)
        case = await ctx.guild.create_text_channel(name=f'case-{now:x}', category=appeals, overwrites=overwrites)

        desc = (f'You, **{member.display_name}**, have been detained by **{ctx.author.display_name}** '
                'for violating or infringing the server rules and are in danger of a permenant ban. '
                'Over the course of the next 24 hours, you may appeal the decision using this channel. '
                'This channel is only accessible to staff members and yourself to maintain confidentiality. '
                'Understand that leaving the server will result in an immediate ban.\n\n'
                'Staff members will each vote to affirm or reverse the decision to ban. '
                'A plurality vote or a tie is required to reverse the decision to ban.')
        embed = Embed(title=f'Case {now:x}', description=desc, color=0xff4e4e)
        embed.add_field(name='\u200b', value=':small_red_triangle: Reverse decision to ban', inline=True)
        embed.add_field(name='\u200b', value=':small_red_triangle_down: Affirm decision to ban', inline=True)
        embed.add_field(name='\u200b', value=f'**`Votes will be counted at: {date}`**', inline=False)
        msg = await case.send('@everyone', embed=embed)
        await msg.add_reaction('🔺')
        await msg.add_reaction('🔻')
        await msg.pin()

        await self.bot.detains.update((member.id, ctx.guild.id), 'channel_id', case.id)
        await self.bot.detains.update((member.id, ctx.guild.id), 'message_id', msg.id)
        await self.bot.detains.update((member.id, ctx.guild.id), 'detained', now+86400)
        await autodetain(self.bot, member, ctx.guild, msg, now+86400)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='delete', aliases=['del', 'purge'], usage='delete [count=1] [mentions]')
    async def delete(self, ctx, n=1.0):
        '''Delete messages from a channel.
        Specify *count* to delete multiple messages. The command message will not be included in this amount.
        *count* cannot be greater than 100 and messages that are more than 14 days old cannot be deleted.
        You can filter messages by user with *mentions*. Multiple users may be mentioned.\n
        **Example:```yml\n.delete 5\n.del 8 @Tau#4272```**
        '''
        n = int(n)
        if not 0 < n <= 100:
            return await ctx.send('*count* must be an integer greater than 0 and less than or equal to 100.')

        members = ctx.message.mentions

        await ctx.message.delete()

        messages = []
        async for msg in ctx.channel.history(limit=None):
            if msg.author in members or not members:
                messages.append(msg)
                if len(messages) == n:
                    break

        await ctx.channel.delete_messages(messages)

        content = f'Deleted **{n}** message'
        if n != 1:
            content += 's'
        await ctx.send(f'{content}!', delete_after=5)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='mute', aliases=['hush'], usage='mute <mention> [limit]')
    async def mute(self, ctx, mention, *limit):
        '''Mute a user.
        *mention* can also be a user ID.

        *limit* is how long to mute the user for.
        Suffix with *d*, *h*, or *m* to specify unit of time.
        If *limit* is omitted, the user will be muted indefinitely.
        Mute limits are capped at 6 months to prevent memory leaks.\n
        **Example:```yml\n.mute @Tau#4272 1 day\n.mute 608367259123187741 1d 12h 30m```**
        '''
        member = await res_member(ctx)
        
        match = re.search(r'<@(!?)([0-9]*)>', mention)
        if not match or member == ctx.author or member.bot:
            raise commands.MissingRequiredArgument

        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)
        
        await ctx.message.delete()

        if self.bot.mutes.get((member.id, ctx.guild.id)):
            return await ctx.send(f'**{member.display_name}** has already been muted.', delete_after=5)
        
        if limit:
            units = {
                'm': 60,
                'h': 3600,
                'd': 86400
            }
        
            t = ''.join(limit).lower().replace('and', '')
        
            limit = ''
            for c in t:
                if c in units.keys() or c.isdigit():
                    limit += c
        
            for u in units.keys():
                limit = limit.replace(u, u + ' ')
            limit = limit.split()

            time_ = []
            for u in units.keys():
                c = 0
                for i in limit:
                    if u in i:
                        c += int(i[:-1])
                time_.insert(0, f'{c}{u}')
            time_ = ', '.join(time_)

            for i, val in enumerate(limit):
                unit = val[-1]
                limit[i] = int(val[:-1]) * units[unit]
        
            limit = sum(limit)
            SEMIYEAR = 1555200
            if limit > SEMIYEAR:
                return await ctx.send(f'{member.mention} Mute limits are capped at 6 months to prevent memory leaks.')

            total = int(time.time()) + limit

            date = time.strftime('%d.%m.%Y %H:%M:%S UTC', time.gmtime(total))
            desc = f'**For: `{time_}`\nUntil: `{date}`**'

            self.bot.mute_tasks[member.id, ctx.guild.id] = self.bot.loop.create_task(automute(self.bot, member.id, ctx.guild.id, total))
        else:
            total = -1

        await self.bot.mutes.update((member.id, ctx.guild.id), 'muted', total)

        await member.add_roles(bind)

        embed = Embed(description=desc, color=0x1f2124) if limit else None
        await ctx.send(f'**<:mute:673362944280494110> | {member.display_name}** has been muted.', embed=embed)

    @commands.command(cls=perms.Lock, level=1, guild_only=True, name='unmute', usage='unmute <mention>')
    async def unmute(self, ctx):
        '''Unmute a user.
        *mention* can also be a user ID.\n
        **Example:```yml\n.unmute @Tau#4272\n.unmute 608367259123187741```**
        '''
        await ctx.message.delete()

        member = await res_member(ctx)
        
        if member == ctx.author or member.bot:
            return

        if not self.bot.mutes.get((member.id, ctx.guild.id)):
            return await ctx.send(f'**{member.display_name}** has not been muted.', delete_after=5)

        bind = findrole(self.bot.guilds_[ctx.guild.id]['bind_role'], ctx.guild)
        await member.remove_roles(bind)

        await self.bot.mutes.delete((member.id, ctx.guild.id))
        if task := self.bot.mute_tasks.get((member.id, ctx.guild.id)):
            task.cancel()
            del self.bot.mute_tasks[member.id, ctx.guild.id]

        await ctx.send(f'**<:sound:673362944280494080> | {member.display_name}** has been unmuted.')

def setup(bot):
    bot.add_cog(Moderation(bot))
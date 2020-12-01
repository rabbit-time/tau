import asyncio
import time
import datetime
import random
from typing import Union

import discord
from discord import Embed, File, AllowedMentions
from discord.ext import commands
from discord.ext.commands import command, guild_only, dm_only

import utils

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _remind(self, user, channel, reminder, timeout):
        now = datetime.datetime.utcnow()
        Δ = (timeout-now).total_seconds()
        await asyncio.sleep(Δ)

        embed = Embed(description=f'Remember to **{reminder}**!')
        embed.set_author(name=user.display_name, icon_url=user.avatar_url)
        embed.set_footer(text='Time\'s up!', icon_url='attachment://unknown.png')
        embed.timestamp = now

        await channel.send(f'Hey {user.mention}!', file=File('assets/clock.png', 'unknown.png'), embed=embed)

        async with self.bot.pool.acquire() as con:
            query = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
            await con.execute(query, user.id, channel.id, timeout, reminder)

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.pool.acquire() as con:
            records = await con.fetch('SELECT * FROM reminders')
            for user_id, channel_id, timeout, reminder in records:
                chan = self.bot.get_channel(channel_id)
                if chan:
                    member = chan.guild.get_member(user_id)
                    if member:
                        self.bot.loop.create_task(self._remind(member, chan, reminder, timeout))
                    else:
                        query = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
                        await con.execute(query, user_id, channel_id, timeout, reminder)

    @command(name='channel', aliases=['chan'], usage='channel <channel>')
    @commands.bot_has_permissions(external_emojis=True)
    @guild_only()
    async def channel(self, ctx, *, chan: Union[discord.VoiceChannel, discord.TextChannel] = None):
        '''Display info on a channel.\n
        **Example:```yml\n♤channel general```**
        '''
        chan = chan if chan else ctx.channel

        embed = Embed(color=utils.Color.sky)
        if chan.type == discord.ChannelType.text:
            nsfw = utils.emoji['on'] if chan.is_nsfw() else utils.emoji['off']

            url = f'https://discord.com/channels/{ctx.guild.id}/{chan.id}/'
            desc = (f'{utils.emoji["#"]} **[{chan}]({url})**\n\n'
                    f'**`nsfw    `** {nsfw}\n'
                    f'**`category` {chan.category}**\n'
                    f'**`position` {chan.position}**\n'
                    f'**`slowmode` {chan.slowmode_delay}**\n')
            embed.description = desc
        else:
            desc = (f'{utils.emoji["sound"]} **{chan}**\n\n'
                    f'**`bitrate   ` {chan.bitrate}**\n'
                    f'**`category  ` {chan.category}**\n'
                    f'**`position  ` {chan.position}**\n'
                    f'**`user_limit` {chan.user_limit}**')
            embed.description = desc
        embed.set_footer(text=f'ID: {chan.id}, created')
        embed.timestamp = chan.created_at

        await ctx.send(embed=embed)

    @command(name='color', usage='color <color>')
    async def color(self, ctx, *, color: discord.Color):
        '''Display info on a color.\n
        **Example:```yml\n♤color #8bb3f8```**
        '''
        buffer = utils.display_color(color)

        r, g, b = color.to_rgb()
        c, m, y, k = utils.rgb_to_cmyk(*color.to_rgb())
        h, s, l = utils.rgb_to_hsl(*color.to_rgb())
        h, s_, v = utils.rgb_to_hsv(*color.to_rgb())

        embed = Embed()
        embed.set_author(name=color)
        embed.add_field(name='RGB', value=f'{r}, {g}, {b}')
        embed.add_field(name='CMYK', value=f'{c:.0%}, {m:.0%}, {y:.0%}, {k:.0%}')
        embed.add_field(name='HSL', value=f'{round(h)}°, {s:.0%}, {l:.0%}')
        embed.add_field(name='HSV', value=f'{round(h)}°, {s_:.0%}, {v:.0%}')
        embed.add_field(name='\u200b', value='**[Color picker](https://www.google.com/search?q=color+picker)**', inline=False)
        embed.set_image(url='attachment://unknown.png')

        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

    @command(name='echo', aliases=['say'], usage='echo <text>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def echo(self, ctx, *, text: str):
        '''Echo a message.\n
        **Example:```yml\n♤echo ECHO!\n♤say hello!```**
        '''
        await ctx.message.delete()

        await ctx.send(text, allowed_mentions=AllowedMentions.none())

    @command(name='emoji', usage='emoji <emoji>')
    @commands.bot_has_permissions(external_emojis=True)
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        '''Display info on an emoji.
        Only applicable to custom emoji.\n
        **Example:```yml\n♤emoji 608367259123187741```**
        '''
        anime = utils.emoji['on'] if emoji.animated else utils.emoji['off']
        man = utils.emoji['on'] if emoji.managed else utils.emoji['off']
        info = (f'**`animated`** {anime}\n'
                f'**`managed `** {man}')

        embed = Embed(description=f'{emoji} **[{emoji.name}]({emoji.url})\n`{emoji}`**', color=utils.Color.sky)
        embed.set_thumbnail(url=emoji.url)
        embed.add_field(name='Information', value=info)
        embed.set_footer(text=f'ID: {emoji.id}, created')
        embed.timestamp = emoji.created_at

        await ctx.send(embed=embed)

    @commands.cooldown(2, 1800.0, type=commands.BucketType.user)
    @command(name='feedback', usage='feedback <message>')
    @dm_only()
    async def feedback(self, ctx, *, msg: str):
        '''Submit feedback to the developer.
        Serious responses only.\n
        **Example:```yml\n♤feedback This is a cool bot, but I'd like to see [...]```**
        '''
        now = datetime.datetime.utcnow()
        app_info = await self.bot.application_info()
        owner = app_info.owner
        try:
            embed = Embed(description=msg, color=utils.Color.sky)
            embed.set_author(name=f'Feedback from {ctx.author}', icon_url=ctx.author.avatar_url)
            embed.add_field(name='\u200b', value=f'**Reply with `.reply {ctx.author.id} <message>`**')
            embed.set_image(url='attachment://unknown.png')
            embed.set_footer(text=f'ID: {ctx.author.id}')
            embed.timestamp = now

            await owner.send(file=File('assets/bar.png', 'unknown.png'), embed=embed)
        except:
            files = [File('assets/reddot.png', 'unknown.png'), File('assets/redbar.png', 'unknown1.png')]
            desc = ('**Oops... something went wrong.**\nYour feedback was unable to be sent '
                    f'to the developer. Please try again later or send them a message directly: **`{owner}`**')
            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name='Submission failed', icon_url='attachment://unknown.png')
            embed.set_image(url='attachment://unknown1.png')
            embed.timestamp = now

            await ctx.send(files=files, embed=embed)
        else:
            files = [File('assets/bar.png', 'unknown.png'), File('assets/dot.png', 'unknown1.png')]
            embed.clear_fields()
            embed.description = f'**Your feedback was successfully submitted. Thank you!**'
            
            embed.set_author(name='Feedback submitted', icon_url='attachment://unknown1.png')
            embed.set_footer(text='')
            await ctx.send(files=files, embed=embed)
    
    @command(name='givexp', aliases=['xp'], usage='givexp <member> <amount>')
    @commands.is_owner()
    @guild_only()
    async def givexp(self, ctx, member: discord.Member, xp: int):
        '''Give XP to a member.
        Developer use only.\n
        **Example:```yml\n♤xp @Tau#4272 100```**
        '''
        if member.bot:
            return

        key = member.id, ctx.guild.id
        if not self.bot.members.get(key):
            await self.bot.members.insert(key)
        
        await self.bot.members.update(key, 'xp', xp+self.bot.members[key]['xp'])
        listeners = self.bot.cogs['Roles'].get_listeners()
        for name, coro in listeners:
            if name == 'Roles':
                await coro(ctx.message)
                break
    
    @command(name='reply', usage='reply <user> <message>')
    @commands.is_owner()
    @dm_only()
    async def reply(self, ctx, user_id: int, *, msg: str):
        '''Reply to feedback.
        Developer use only.\n
        **Example:```yml\n♤reply Thank you!```**
        '''
        user = self.bot.get_user(user_id)
        now = datetime.datetime.utcnow()
        try:
            embed = Embed(description=msg, color=utils.Color.sky)
            embed.set_author(name=f'Reply from {ctx.author.name}', icon_url=ctx.author.avatar_url)
            embed.set_image(url='attachment://unknown.png')
            embed.timestamp = now

            await user.send(file=File('assets/bar.png', 'unknown.png'), embed=embed)
        except:
            files = [File('assets/reddot.png', 'unknown.png'), File('assets/redbar.png', 'unknown1.png')]
            desc = ('**Oops... something went wrong.**\nYour reply was unable to be sent '
                    f'to the user. Please try again later or send them a message directly: **`{user}`**')
            embed = Embed(description=desc, color=utils.Color.red)
            embed.set_author(name='Reply failed', icon_url='attachment://unknown.png')
            embed.set_image(url='attachment://unknown1.png')
            embed.timestamp = now

            await ctx.send(files=files, embed=embed)
        else:
            files = [File('assets/bar.png', 'unknown.png'), File('assets/dot.png', 'unknown1.png')]
            embed.description = f'**Your reply was successfully sent to the user.**'
            embed.set_author(name='Reply delivered', icon_url='attachment://unknown1.png')

            await ctx.send(files=files, embed=embed)

    @command(name='random', aliases=['rng'], usage='random <lower> <upper>')
    @commands.bot_has_permissions(external_emojis=True)
    async def random(self, ctx, lower: int, upper: int):
        '''Randomly generate an integer between a lower and upper bound.\n
        **Example:```yml\n♤random 0 1\n♤rng 1 10```**
        '''
        embed = Embed(description=f'**You got {random.randint(lower, upper)}!**', color=random.choice(utils.Color.rainbow))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @command(name='remind', usage='remind <time> <reminder>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def remind(self, ctx, limit, *, reminder):
        '''Set a reminder.
        Reminders are capped at 6 months to prevent memory leaks.\n
        **Example:```yml\n♤remind 2h clean room\n♤remind 1h fix bugs```**
        '''
        time_, delta = utils.parse_time(limit)
        now = datetime.datetime.utcnow()

        SEMIYEAR = 1555200
        if delta.total_seconds() > SEMIYEAR:
            raise commands.BadArgument
        
        timeout = now + delta
        self.bot.loop.create_task(self._remind(ctx.author, ctx.channel, reminder, timeout))
        async with self.bot.pool.acquire() as con:
            query = 'INSERT INTO reminders VALUES ($1, $2, $3, $4)'
            await con.execute(query, ctx.author.id, ctx.channel.id, timeout, reminder)

        embed = Embed(description=f'Reminder to **{reminder}** has been set for {time_}!')
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=time_, icon_url='attachment://unknown.png')
        embed.timestamp = timeout

        await ctx.send(file=File('assets/clock.png', 'unknown.png'), embed=embed)

    @command(name='resend', aliases=['rs'], usage='resend <message>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def resend(self, ctx, msg: discord.Message):
        '''Resend a message.
        This is useful for getting rid of the "edited" indicator.
        To resend a message from another channel, use a message link instead of an ID.
        This works safely with role menus.\n
        **Example:```yml\n♤resend 694890918645465138```**
        '''
        await ctx.message.delete()
        
        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break
        
        files = []
        for a in msg.attachments:
            file = await a.to_file()
            files.append(file)

        rmenu = self.bot.rmenus.get((ctx.guild.id, msg.id))

        await msg.delete()
        
        new = await ctx.send(content=msg.content, files=files, embed=embed)

        if rmenu:
            for i in range(len(rmenu['role_ids'].split())):
                await new.add_reaction(utils.emoji[i+1])
                
            await self.bot.rmenus.update((ctx.guild.id, new.id), 'role_ids', rmenu['role_ids'])
            await self.bot.rmenus.update((ctx.guild.id, new.id), 'limit_', rmenu['limit_'])
            
    @command(name='role', usage='role <role>')
    @commands.bot_has_permissions(external_emojis=True)
    @guild_only()
    async def role(self, ctx, *, role: discord.Role):
        '''Display info on a role.\n
        **Example:```yml\n♤role Tau\n♤role 657766595321528349```**
        '''
        buffer = utils.display_color(role.color)

        perms = sorted((perm, value) for perm, value in iter(role.permissions))
        plen = len(max(perms, key=lambda p: len(p[0]))[0])
        
        half = len(perms) // 2
        fields = [''] * 2
        for i, tup in enumerate(perms):
            perm, value = tup
            tog = utils.emoji['on'] if value else utils.emoji['off']
            align = ' ' * (plen-len(perm))
            fields[i>half] += f'**`{perm}{align}`** {tog}\n'

        plural = 's' if len(role.members) != 1 else ''
        mention = role.mention if not role.is_default() else '@everyone'
        embed = Embed(description=f'**{mention}\n`{len(role.members)} member{plural}`**')
        embed.add_field(name='Permissions', value=fields[0])
        embed.add_field(name='\u200b', value=fields[1])
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'ID: {role.id}')
        
        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Utilities(bot))
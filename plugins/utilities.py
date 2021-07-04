import asyncio
import time
import datetime
from inspect import signature as sig
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

    async def _remind(self, ctx, reminder, timeout):
        now = datetime.datetime.utcnow()
        Δ = (timeout-now).total_seconds()
        await asyncio.sleep(Δ)

        try:
            msg = await ctx.channel.fetch_message(ctx.message.id)
            ref = msg.to_reference()
        except:
            ref = None

        files = [File('assets/dot.png', 'unknown.png'), File('assets/clock.png', 'unknown1.png')]
        embed = Embed(description=f'>>> {reminder}', color=utils.Color.sky)
        embed.set_author(name='Reminder', icon_url='attachment://unknown.png')
        embed.set_footer(text='Time\'s up!', icon_url='attachment://unknown1.png')
        embed.timestamp = timeout

        await ctx.channel.send(ctx.author.mention if not ref else None, files=files, embed=embed, reference=ref)

        async with self.bot.pool.acquire() as con:
            query = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
            await con.execute(query, ctx.author.id, ctx.channel.id, timeout, reminder)

    async def _emparse(self, ctx, embed: Embed, fields: tuple) -> tuple:
        i = 0
        content = None
        while i < len(fields):
            if fields[i] == 'content':
                content = fields[i]
                i += 2
                continue
            
            # get a function callback using a string that corresponds to its name
            embuilder = utils.EmbedBuilder(ctx)
            method = getattr(embuilder, fields[i], None)
            if method == None:
                raise commands.BadArgument
            
            # extract the number of parameters
            params = len(sig(method).parameters)
            
            # create the embed, catching any embed limit violations
            try:
                await method(embed, *fields[i+1:i+params])
                if len(embed) > 6000: raise utils.EmbedException('embed', 6000)
            except utils.EmbedException as err:
                embed.set_author(name=err.what(), icon_url='attachment://unknown.png')
                embed.color = utils.Color.red

                await ctx.reply(embed=embed, file=File('assets/reddot.png', 'unknown.png'))

            i += params
        
        return content

    @commands.Cog.listener()
    async def on_ready(self):
        async with self.bot.pool.acquire() as con:
            records = await con.fetch('SELECT * FROM reminders')
            for user_id, channel_id, timeout, reminder in records:
                chan = self.bot.get_channel(channel_id)
                if chan:
                    member = chan.guild.get_member(user_id)
                    if member:
                        class Object:
                            author = member
                            channel = chan
                        
                        self.bot.loop.create_task(self._remind(Object, reminder, timeout))
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
            nsfw = utils.Emoji.on if chan.is_nsfw() else utils.Emoji.off

            url = f'https://discord.com/channels/{ctx.guild.id}/{chan.id}/'
            desc = (f'{utils.Emoji.hash} **[{chan}]({url})**\n\n'
                    f'**`nsfw    `** {nsfw}\n'
                    f'**`category` {chan.category}**\n'
                    f'**`position` {chan.position}**\n'
                    f'**`slowmode` {chan.slowmode_delay}**\n')
            embed.description = desc
        else:
            desc = (f'{utils.Emoji.sound} **{chan}**\n\n'
                    f'**`bitrate   ` {chan.bitrate}**\n'
                    f'**`category  ` {chan.category}**\n'
                    f'**`position  ` {chan.position}**\n'
                    f'**`user_limit` {chan.user_limit}**')
            embed.description = desc
        embed.set_footer(text=f'ID: {chan.id}, created')
        embed.timestamp = chan.created_at

        await ctx.reply(embed=embed, mention_author=False)

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

        file = File(buffer, 'unknown.png')
        embed = Embed(description='**[Color picker](https://www.google.com/search?q=color+picker)**', color=color)
        embed.set_author(name=color)
        embed.add_field(name='RGB', value=f'{r}, {g}, {b}')
        embed.add_field(name='CMYK', value=f'{c:.0%}, {m:.0%}, {y:.0%}, {k:.0%}')
        embed.add_field(name='HSL', value=f'{round(h)}°, {s:.0%}, {l:.0%}')
        embed.add_field(name='HSV', value=f'{round(h)}°, {s_:.0%}, {v:.0%}')
        embed.set_image(url='attachment://unknown.png')

        await ctx.send(file=file, embed=embed, reference=ctx.message.to_reference(), mention_author=False)

    @command(name='echo', aliases=['say'], usage='echo <text>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def echo(self, ctx, *, text: str):
        '''Echo a message.\n
        **Example:```yml\n♤echo ECHO!\n♤say hello!```**
        '''
        await ctx.message.delete()
        
        await ctx.send(text, allowed_mentions=AllowedMentions.none())

    @command(name='embed', aliases=['em'], usage='embed <*fields>')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(external_emojis=True)
    async def embed(self, ctx, *fields):
        '''Create a new embed.
        Use double quotes any multi-word arguments.
        Here is the following format for different embed fields:
        **```yml
        author <name>
        authoricon <url>
        authorurl <url>
        color <color>
        content <text>
        desc <description>
        field <name> <value>
        inlinefield <name> <value>
        modfield <index> <name> <value>
        clearfields
        footer <text>
        footericon <url>
        image <url>
        thumbnail <url>
        title <text>
        ```**
        **Example:```yml\n♤embed desc "Hi"
        title "My Embed"
        field "Favorite Number" "3"
        footer "Made by a cool person"```**
        '''
        if not fields:
            raise commands.BadArgument

        embed = Embed()
        content = await self._emparse(ctx, embed, fields)

        await ctx.send(content, embed=embed)

    @command(name='modembed', aliases=['modem'], usage='modembed <message> <*fields>')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(external_emojis=True)
    async def modembed(self, ctx, msg: discord.Message, *fields):
        '''Modify an embed.
        Only valid for messages sent from this bot.
        See `♤cmd embed` for more details.\n
        **Example:```yml\n♤modembed 608367259123187741 
        desc "Hi"
        title "My Embed"
        field "Favorite Number" "3"
        footer "Made by a cool person"```**
        '''
        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break

        if not isinstance(embed, discord.Embed) or msg.author != ctx.guild.me:
            raise commands.BadArgument
        
        content = await self._emparse(ctx, embed, fields)

        await msg.edit(content=content, embed=embed)

    @command(name='emoji', usage='emoji <emoji>')
    @commands.bot_has_permissions(external_emojis=True)
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        '''Display info on an emoji.
        Only applicable to custom emoji.\n
        **Example:```yml\n♤emoji 608367259123187741```**
        '''
        anime = utils.Emoji.on if emoji.animated else utils.Emoji.off
        man = utils.Emoji.on if emoji.managed else utils.Emoji.off
        info = (f'**`animated`** {anime}\n'
                f'**`managed `** {man}')

        embed = Embed(description=f'{emoji} **[{emoji.name}]({emoji.url})\n`{emoji}`**', color=utils.Color.sky)
        embed.set_thumbnail(url=emoji.url)
        embed.add_field(name='Information', value=info)
        embed.set_footer(text=f'ID: {emoji.id}, created')
        embed.timestamp = emoji.created_at

        await ctx.reply(embed=embed, mention_author=False)

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

            await ctx.reply(files=files, embed=embed, mention_author=False)
        else:
            files = [File('assets/bar.png', 'unknown.png'), File('assets/dot.png', 'unknown1.png')]
            embed.clear_fields()
            embed.description = f'**Your feedback was successfully submitted. Thank you!**'
            
            embed.set_author(name='Feedback submitted', icon_url='attachment://unknown1.png')
            embed.set_footer(text='')
            await ctx.reply(files=files, embed=embed, mention_author=False)
    
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

            await ctx.reply(files=files, embed=embed, mention_author=False)
        else:
            files = [File('assets/bar.png', 'unknown.png'), File('assets/dot.png', 'unknown1.png')]
            embed.description = f'**Your reply was successfully sent to the user.**'
            embed.set_author(name='Reply delivered', icon_url='attachment://unknown1.png')

            await ctx.reply(files=files, embed=embed, mention_author=False)

    @command(name='random', aliases=['rng'], usage='random <lower> <upper>')
    @commands.bot_has_permissions(external_emojis=True)
    async def random(self, ctx, lower: int, upper: int):
        '''Randomly generate an integer between a lower and upper bound.\n
        **Example:```yml\n♤random 0 1\n♤rng 1 10```**
        '''
        embed = Embed(color=random.choice(utils.Color.rainbow)).set_author(name=f'You got {random.randint(lower, upper)}!')
        await ctx.reply(embed=embed, mention_author=False)

    @command(name='remind', usage='remind <time> <reminder>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def remind(self, ctx, limit, *, reminder):
        '''Set a reminder.
        Reminders are capped at 6 months to prevent abuse.\n
        **Example:```yml\n♤remind 2h clean room\n♤remind 1h fix bugs```**
        '''
        time_, delta = utils.parse_time(limit)
        now = datetime.datetime.utcnow()

        SEMIYEAR = 1555200
        if delta.total_seconds() > SEMIYEAR:
            raise commands.BadArgument
        
        timeout = now + delta
        self.bot.loop.create_task(self._remind(ctx, reminder, timeout))
        async with self.bot.pool.acquire() as con:
            query = 'INSERT INTO reminders VALUES ($1, $2, $3, $4)'
            await con.execute(query, ctx.author.id, ctx.channel.id, timeout, reminder)

        files = [File('assets/dot.png', 'unknown.png'), File('assets/clock.png', 'unknown1.png')]
        embed = Embed(description=f'>>> {reminder}', color=utils.Color.sky)
        embed.set_author(name='Reminder', icon_url='attachment://unknown.png')
        embed.set_footer(text=time_, icon_url='attachment://unknown1.png')
        embed.timestamp = timeout

        await ctx.reply(files=files, embed=embed, mention_author=False)

    @command(name='resend', aliases=['rs'], usage='resend <message>')
    @commands.has_guild_permissions(manage_guild=True)
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
        
        new = await ctx.send(content=msg.content, files=files, embed=embed)

        rmenu = self.bot.rmenus.get((msg.guild.id, msg.id))
        if rmenu:
            for emoji in rmenu['emojis']:
                try:
                    await new.add_reaction(emoji)
                except discord.NotFound:
                    return await new.delete()

            async with self.bot.pool.acquire() as con:
                self.bot.rmenus[ctx.guild.id, new.id] = rmenu
                del self.bot.rmenus[msg.guild.id, msg.id]

                stmt = (f'UPDATE role_menus SET guild_id = {ctx.guild.id}, message_id = {new.id} '
                        f'WHERE guild_id = {msg.guild.id} AND message_id = {msg.id}')
                await con.execute(stmt)

        await msg.delete()

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
            tog = utils.Emoji.on if value else utils.Emoji.off
            align = ' ' * (plen-len(perm))
            fields[i>half] += f'**`{perm}{align}`** {tog}\n'

        plural = 's' if len(role.members) != 1 else ''
        mention = role.mention if not role.is_default() else '@everyone'
        embed = Embed(description=f'**{mention}\n`{len(role.members)} member{plural}`**', color=role.color)
        embed.add_field(name='Permissions', value=fields[0])
        embed.add_field(name='\u200b', value=fields[1])
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'ID: {role.id}')
        
        await ctx.reply(file=File(buffer, 'unknown.png'), embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Utilities(bot))
import colorsys
import time
import datetime
import random

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown

import perms
import utils

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='color', aliases=[], usage='color <color>')
    async def color(self, ctx, *, color: discord.Color):
        '''Display info on a color.\n
        **Example:```yml\n.color #8bb3f8```**
        '''
        buffer = utils.display_color(color)

        r, g, b = color.to_rgb()
        c, m, y, k = utils.rgb_to_cmyk(*color.to_rgb())
        h, l, s = colorsys.rgb_to_hls(color.r/255, color.g/255, color.b/255)
        h, s, v = colorsys.rgb_to_hsv(color.r/255, color.g/255, color.b/255)

        embed = Embed()
        embed.set_author(name=color)
        embed.add_field(name='RGB', value=f'{r}, {g}, {b}')
        embed.add_field(name='CMYK', value=f'{c:.0%}, {m:.0%}, {y:.0%}, {k:.0%}')
        embed.add_field(name='HSL', value=f'{round(h*360)}°, {s:.0%}, {l:.0%}')
        embed.add_field(name='HSV', value=f'{round(h*360)}°, {s:.0%}, {v:.0%}')
        embed.set_image(url='attachment://unknown.png')

        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

    @commands.command(cls=perms.Lock, name='emoji', aliases=[], usage='emoji <emoji>')
    @commands.bot_has_permissions(external_emojis=True)
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        '''Display info on an emoji.
        Only applicable to custom emoji.\n
        **Example:```yml\n.emoji 608367259123187741```**
        '''
        anime = utils.emoji['on'] if emoji.animated else utils.emoji['off']
        man = utils.emoji['on'] if emoji.managed else utils.emoji['off']
        info = (f'**`animated`** {anime}\n'
                f'**`managed `** {man}')

        embed = Embed(description=f'{emoji} **[{emoji.name}]({emoji.url})\n`{emoji}`**', color=0x88b3f8)
        embed.set_thumbnail(url=emoji.url)
        embed.add_field(name='Information', value=info)
        embed.set_footer(text=f'ID: {emoji.id}, created')
        embed.timestamp = emoji.created_at

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='echo', aliases=['say'], usage='echo <text>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def echo(self, ctx, *, text: str):
        '''Echo a message.\n
        **Example:```yml\n.echo ECHO!\n.say hello!```**
        '''
        await ctx.message.delete()

        await ctx.send(text)

    @commands.command(cls=perms.Lock, name='random', aliases=['rng'], usage='random <lower> <upper>')
    @commands.bot_has_permissions(external_emojis=True)
    async def random(self, ctx, lower: int, upper: int):
        '''Randomly generate an integer between a lower and upper bound.\n
        **Example:```yml\n.random 0 1\n.rng 1 10```**
        '''
        colors = (0xff4e4e, 0xffa446, 0xffc049, 0x2aa198, 0x55b8f8, 0xc8aaff, 0xffadca)

        embed = Embed(description=f'**You got {random.randint(lower, upper)}!**', color=random.choice(colors))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='remind', aliases=[], usage='remind <time> <reminder>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def remind(self, ctx, limit, *, reminder):
        '''Set a reminder.
        Reminders are capped at 6 months to prevent memory leaks.\n
        **Example:```yml\n.remind 2h clean room\n.remind 1h fix bugs```**
        '''
        time_, delay = utils.parse_time(limit)
        now = int(time.time())

        SEMIYEAR = 1555200
        if delay > SEMIYEAR:
            raise commands.BadArgument
        
        await self.bot.reminders.update((ctx.author.id, delay+now), 'channel_id', ctx.channel.id)
        await self.bot.reminders.update((ctx.author.id, delay+now), 'reminder', reminder)
        self.bot.loop.create_task(utils.remind(self.bot, ctx.author, ctx.channel, reminder, delay+now))

        embed = Embed(description=f'Reminder to **{reminder}** has been set for {time_}!')
        embed.set_author(name=escape_markdown(ctx.author.display_name), icon_url=ctx.author.avatar_url)
        embed.set_footer(text=time_, icon_url='attachment://unknown.png')
        embed.timestamp = datetime.datetime.fromtimestamp(delay+now).astimezone(tz=datetime.timezone.utc)

        await ctx.send(file=File('assets/clock.png', 'unknown.png'), embed=embed)

    @commands.command(cls=perms.Lock, name='resend', aliases=['rs'], usage='resend <message>')
    @commands.bot_has_permissions(external_emojis=True, manage_messages=True)
    async def resend(self, ctx, msg: discord.Message):
        '''Resend a message.
        This is useful for getting rid of the "edited" indicator.
        To resend a message from another channel, use a message link instead of an ID.\n
        **Example:```yml\n.resend 694890918645465138```**
        '''
        await msg.delete()

        embed = None
        for e in msg.embeds:
            if e.type == 'rich':
                embed = e
                break

        await ctx.send(content=msg.content, embed=embed)

def setup(bot):
    bot.add_cog(Utilities(bot))
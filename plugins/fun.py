import asyncio
import random

from discord import Embed, File, AllowedMentions
from discord.ext import commands
from discord.ext.commands import command
from discord.utils import escape_markdown
import requests

import utils

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='8ball', usage='8ball [question]')
    async def _8ball(self, ctx, *, question: str = None):
        '''Ask the Magic 8-Ball a question.\n
        **Example:```yml\n♤8ball is Tau cool?```**
        '''
        responses = ['It is certain.', 'It is decidedly so.', 'Without a doubt.',
            'Yes – definitely.', 'You may rely on it.', 'As I see it, yes.',
            'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.',
            'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.',
            'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.',
            'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Very doubtful.']

        res = random.choice(responses)
        i = responses.index(res)
        if i < 10:
            color = utils.Color.green
        elif i < 15:
            color = utils.Color.gold
        else:
            color = utils.Color.red

        embed = Embed(color=color)
        embed.add_field(name=':8ball: Magic 8-Ball', value=f'**"{res}"**')

        await ctx.reply(embed=embed, mention_author=False)

    def _img(self, ctx, path: str, name: str = None) -> Embed:
        name = name if name else path.title()
        res = requests.get(f'https://some-random-api.ml/img/{path}')
        url = res.json()['link']

        embed = Embed(description=f'{utils.Emoji.link} **[{name}]({url})**', color=random.choice(utils.Color.rainbow))
        embed.set_image(url=url)

        return embed

    @command(name='bird', usage='bird')
    async def bird(self, ctx):
        '''Get a random bird.\n
        **Example:```yml\n♤bird```**
        '''
        await ctx.reply(embed=self._img(ctx, 'birb', 'Bird'), mention_author=False)

    @command(name='cat', usage='cat')
    async def cat(self, ctx):
        '''Get a random cat.\n
        **Example:```yml\n♤cat```**
        '''
        await ctx.reply(embed=self._img(ctx, 'cat'), mention_author=False)

    @command(name='dog', usage='dog')
    async def dog(self, ctx):
        '''Get a random dog.\n
        **Example:```yml\n♤dog```**
        '''
        await ctx.reply(embed=self._img(ctx, 'dog'), mention_author=False)

    @command(name='fox', usage='fox')
    async def fox(self, ctx):
        '''Get a random fox.\n
        **Example:```yml\n♤fox```**
        '''
        await ctx.reply(embed=self._img(ctx, 'fox'), mention_author=False)

    @command(name='koala', usage='koala')
    async def koala(self, ctx):
        '''Get a random koala.\n
        **Example:```yml\n♤koala```**
        '''
        await ctx.reply(embed=self._img(ctx, 'koala'), mention_author=False)

    @command(name='panda', usage='panda')
    async def panda(self, ctx):
        '''Get a random panda.\n
        **Example:```yml\n♤panda```**
        '''
        await ctx.reply(embed=self._img(ctx, 'panda'), mention_author=False)

    @command(name='redpanda', usage='redpanda')
    async def red_panda(self, ctx):
        '''Get a random red panda.\n
        **Example:```yml\n♤redpanda```**
        '''
        await ctx.reply(embed=self._img(ctx, 'red_panda', 'Red panda'), mention_author=False)

    @command(name='ping', aliases=['p'], usage='ping')
    async def ping(self, ctx):
        '''Pong!
        Display the latency.
        Note that this contains network latency and Discord API latency.\n
        **Example:```yml\n♤ping```**
        '''
        embed = Embed(color=utils.Color.gold)
        embed.set_author(name='Ping?')
        embed.add_field(name='Latency', value=f'**--.--**ms')

        ping = await ctx.reply(embed=embed, mention_author=False)

        await asyncio.sleep(0.2)

        embed.colour = utils.Color.green
        embed.set_author(name='Pong!')
        embed.set_field_at(0, name='Latency', value=f'**{self.bot.latency*1000:.2f}**ms')

        await ping.edit(embed=embed, allowed_mentions=AllowedMentions.none())

    @command(name='coin', aliases=['flip'], usage='coin [quantity=1]')
    @commands.bot_has_permissions(external_emojis=True)
    async def coin(self, ctx, n: int = 1):
        '''Flip a coin.
        Enter a positive integer for `quantity` to flip multiple coins.
        Max is 84.\n
        **Example:```yml\n♤coin\n♤flip 3```**
        '''
        if not 0 < n <= 84:
            raise commands.BadArgument

        val = random.choices(range(2), k=n)
        coin = utils.Emoji.coin0, utils.Emoji.coin1
        embed = Embed(description=f'{coin[val[0]]} **You got {["tails", "heads"][val[0]]}!**', color=utils.Color.gold)
        if n != 1:
            coins = ''
            for i, v in enumerate(val):
                coins += coin[v]
                if (i + 1) % 10 == 0:
                    coins += '\n'

            embed.description = f'**You got:\n\n{coins}**'
            embed.add_field(name='\u200b', value=f'**Heads: {val.count(1)}\nTails: {val.count(0)}**')

        await ctx.reply(embed=embed, mention_author=False)

    @command(name='dice', aliases=['die', 'roll'], usage='dice [quantity=1]')
    async def dice(self, ctx, n: int = 1):
        '''Roll a die.
        Enter a positive integer for `quantity` to roll multiple dice.
        Max is 84.\n
        **Example:```yml\n♤dice\n♤roll 3```**
        '''
        if not 0 < n <= 84:
            raise commands.BadArgument

        val = random.choices(range(6), k=n)
        die = utils.Emoji.dice[val[0]+1]
        embed = Embed(description=f'{die} **You got {val[0]+1}!**', color=utils.Color.red)
        if n != 1:
            dice = ''
            for i, v in enumerate(val):
                dice += utils.Emoji.dice[v+1]
                if (i + 1) % 10 == 0:
                    dice += '\n'

            embed.description = f'**You got:\n\n{dice}**'
            for i in range(6):
                embed.add_field(name=utils.Emoji.dice[v+1], value=f'**{val.count(i)}**')

        await ctx.reply(embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Fun(bot))

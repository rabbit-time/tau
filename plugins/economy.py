import datetime
import random

import discord
from discord import Embed, File
from discord.ext import commands

import perms
import utils

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='balance', aliases=['acc', 'bal'], usage='balance [member]')
    async def balance(self, ctx, *, member: discord.Member = None):
        '''Display user account balance.
        This only works with members within the guild.\n
        **Example:```yml\n.balance\n.bal @Tau#4272\n.acc 608367259123187741```**
        '''
        if not member:
            member = ctx.author

        if member.bot:
            return

        bal = self.bot.users_[member.id]['tickets']
        embed = Embed(description=f'{utils.emoji["tickets"]}**{bal}**')
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='give', usage='give <member> <quantity>')
    async def give(self, ctx, member: discord.Member, qty):
        '''Give credits to another user.
        `quantity` can also be '\\*' or 'all'\n
        **Example:```yml\n.give @Tau#4272 420 \n.give 608367259123187741 69```**
        '''
        if member.bot:
            return

        bal = self.bot.users_[ctx.author.id]['tickets']
        qty = bal if qty == '*' or qty == 'all' else int(qty) if qty.isdigit() and 0 < int(qty) <= bal else None
        if not qty:
            return await ctx.send('Invalid *qty*.')

        await self.bot.users_.update(ctx.author.id, 'tickets', bal-qty)

        bal = self.bot.users_[member.id]['tickets']
        await self.bot.users_.update(member.id, 'tickets', bal+qty)

        await ctx.send(f'**{ctx.author.display_name}** gave {utils.emoji["tickets"]}**{qty}** to **{member.display_name}**!')

    @commands.cooldown(1, 86400.0, type=commands.BucketType.user)
    @commands.command(cls=perms.Lock, name='credits', aliases=['daily'], usage='tickets')
    async def credits(self, ctx):
        '''Collect your daily credits.
        Has a cooldown of 24 hours.\n
        **Example:```yml\n.credits```**
        '''
        msgs = ['Here are your credits!', 'Gosh, you\'re just using me for money, aren\'t you?', ':money_with_wings: :money_with_wings:',
        'So, when do I get *my* credits?', 'Collecting your government benefits I see... :eyes:', 'credits for all!',
        '<insert unfunny joke here, i ran out>', 'Yes, I\'m the Automatic Tau Machine...',
        'Here are your credits! Have a wonderful day!', 'Between you and me, I have an endless supply of this stuff.',
        'Fun fact: I give double the amount of credits on Sundays!', 'Here you go!']

        bal = self.bot.users_[ctx.author.id]['tickets']
        amt = 20
        if datetime.datetime.today().weekday() == 6:
            amt *= 2
        await self.bot.users_.update(ctx.author.id, 'tickets', bal+amt)

        desc = f'You have collected **{amt}** credits for a new balance of {utils.emoji["tickets"]}**{bal+amt}**!'
        embed = Embed(description=desc)

        await ctx.send(ctx.author.mention + ' ' + random.choice(msgs), embed=embed)

    @credits.error
    async def credits_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('You\'ve already collected your daily credits!')

def setup(bot):
    bot.add_cog(Economy(bot))
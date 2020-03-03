import datetime
import random

from discord import Embed, File
from discord.ext import commands

import perms
from utils import res_member, emoji

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, name='balance', aliases=['acc', 'bal'], usage='balance [mention]')
    async def balance(self, ctx):
        '''Display user account balance.
        In addition to a mention, *mention* can also be substituted with a user ID.
        Although, this only works with members within the guild.\n
        **Example:```yml\n.balance\n.bal @Tau#4272\n.acc 608367259123187741```**
        '''
        member = await res_member(ctx)

        if not member or member.bot:
            return

        bal = self.bot.users_[member.id]['tickets']
        embed = Embed(description=f'{emoji["tickets"]}**{bal}**')
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='give', usage='give <amt> <mention>')
    async def give(self, ctx, amt):
        '''Give tickets to another user.
        *mention* can also be a user ID.
        *amt* can also be '\\*' or 'all'\n
        **Example:```yml\n.give 420 @Tau#4272\n.give 69 608367259123187741```**
        '''
        member = await res_member(ctx)

        if not member or member.bot:
            return

        bal = self.bot.users_[ctx.author.id]['tickets']
        amt = bal if amt == '*' or amt == 'all' else int(amt) if amt.isdigit() and 0 < int(amt) <= bal else None
        if not amt:
            return await ctx.send('Invalid *amt*.')

        await self.bot.users_.update(ctx.author.id, 'tickets', bal-amt)

        bal = self.bot.users_[member.id]['tickets']
        await self.bot.users_.update(member.id, 'tickets', bal+amt)

        await ctx.send(f'**{ctx.author.display_name}** gave {emoji["tickets"]}**{amt}** to **{member.display_name}**!')

    @commands.cooldown(1, 86400.0, type=commands.BucketType.user)
    @commands.command(cls=perms.Lock, name='tickets', aliases=['credits', 'daily', 'tic'], usage='tickets')
    async def tickets(self, ctx):
        '''Collect your daily tickets.
        Has a cooldown of 24 hours.\n
        **Example:```yml\n.tickets```**
        '''
        msgs = ['Here are your tickets!', 'Gosh, you\'re just using me for money, aren\'t you?', ':money_with_wings: :money_with_wings:',
        'So, when do I get *my* tickets?', 'Collecting your government benefits I see... :eyes:', 'Tickets for all!',
        'Have some tickets! Perhaps see an action movie or win a game of Battlefield!', 'Yes, I\'m the Automatic Tau Machine...',
        'Here are your tickets! Have a wonderful day!', 'Between you and me, I have an endless supply of this stuff.',
        'Fun fact: I give double the amount of tickets on Sundays!', 'Here you go!']

        bal = self.bot.users_[ctx.author.id]['tickets']
        amt = 20
        if datetime.datetime.today().weekday() == 6:
            amt *= 2
        await self.bot.users_.update(ctx.author.id, 'tickets', bal+amt)

        desc = f'You have collected {amt} tickets for a new balance of {emoji["tickets"]}**{bal+amt}**!'
        embed = Embed(description=desc)

        await ctx.send(ctx.author.mention + ' ' + random.choice(msgs), embed=embed)

    @tickets.error
    async def tickets_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('You\'ve already collected your daily tickets!')

def setup(bot):
    bot.add_cog(Economy(bot))
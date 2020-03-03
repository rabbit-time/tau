from discord import Embed, File
from discord.ext.commands import Command

import config

levels = {
    'User': 'all users',
    'Mod': 'members with guild\'s mod role',
    'Admin': 'members with guild\'s admin role',
    'Guild Owner': 'the owner of the guild',
    'Bot Admin': 'developers of the bot',
    'Bot Owner': 'the owner of the bot'
}

class Lock(Command):
    def __init__(self, command, level=0, guild_only=False, **kwargs):
        self.level = level
        self.guild_only = guild_only
        super().__init__(command, **kwargs)

def perm(ctx):
    if (uid := ctx.author.id) == config.owner_id:
        return 5
    elif uid in config.admins:
        return 4
    elif ctx.guild:
        roles = [r.name for r in ctx.author.roles]
        if uid == ctx.guild.owner.id:
            return 3
        elif ctx.bot.guilds_[ctx.guild.id]['admin_role'] in roles:
            return 2
        elif ctx.bot.guilds_[ctx.guild.id]['mod_role'] in roles:
            return 1
        else:
            return 0
    else:
        return 0

async def require(ctx):
    if not ctx.guild and ctx.command.guild_only:
        desc = f'Oops! **`{ctx.command.name}`** is only available within guilds.'
        embed = Embed(description=desc)

        await ctx.send(f'Hey {ctx.author.mention}!', embed=embed)
        return False
    if (level := perm(ctx)) >= ctx.command.level:
        return True
    else:
        prefix = ctx.bot.guilds_[ctx.guild.id]['prefix'] if ctx.guild else ctx.bot.guilds_.default['prefix']
        names = ''
        for i, item in enumerate(levels.items()):
            k, v = item
            names += f'**`{i}`** {k} ー *{v}*\n'
        desc = (f'**Sorry, but you don\'t have permission to use this command.**\n\n'
        f'This command requires a permission level of **`{ctx.command.level}`**, whereas your level is only **`{level}`**. '
        f'If you think this is a mistake, please report it to my developers.')
        embed = Embed(description=desc, color=0xff4e4e)
        embed.add_field(name='Permission Levels', value=names)
        embed.set_footer(text=f'Pro tip! You can call {prefix}level at any time to check your perm level.', icon_url='attachment://unknown.png')

        await ctx.send(f'Hey {ctx.author.mention}!', file=File('assets/info.png', 'unknown.png'), embed=embed)
        return False
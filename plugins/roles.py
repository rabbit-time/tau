import asyncio
import io

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import find
from PIL import Image, ImageDraw, ImageFont

import perms
import utils

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, level=0, guild_only=True, name='role', aliases=[], usage='role <name|id>')
    async def role(self, ctx, *content):
        '''Displays role info.\n
        **Example:```yml\n.role Tau\n.role 657766595321528349```**
        '''
        content = ' '.join(content)
        role = find(lambda r: r.name == content, ctx.guild.roles)
        if not role:
            role_id = int(content) if content.isdigit() else 0
            role = ctx.guild.get_role(role_id)

        if not role:
            await ctx.message.delete()
            return await ctx.send(f'{ctx.author.mention} Sorry! A role named \'{content}\' could not be found.', delete_after=5)

        im = Image.new('RGB', (1200, 400), role.color.to_rgb())
        draw = ImageDraw.Draw(im)

        font = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 250)
        
        x, y = im.width, im.height
        w, h = font.getsize(str(role.color))
        # Around 6,000,000 just happened to be the sweet spot for white text
        fill = 'black' if role.color.value > 6000000 else 'white'
        draw.text((x//2-w//2, y//2-h//2), str(role.color), font=font, fill=fill)

        buffer = io.BytesIO()
        im.save(buffer, 'png')

        buffer.seek(0)

        perms = [(perm, value) for perm, value in iter(role.permissions)]
        perms.sort()
        plen = len(max(perms, key=lambda p: len(p[0]))[0])
        
        half = len(perms) // 2
        fields = ['', '']
        for i, tup in enumerate(perms):
            perm, value = tup
            tog = utils.emoji['on'] if value else utils.emoji['off']
            align = ' ' * (plen-len(perm))
            fields[i > half] += f'**`{perm}{align}`** {tog}\n'

        plural = 's' if len(role.members) != 1 else ''
        mention = role.mention if not role.is_default() else '@everyone'
        embed = Embed(description=f'**{mention}\n`{len(role.members)} member{plural}`**')
        embed.add_field(name='Permissions', value=fields[0])
        embed.add_field(name='\u200b', value=fields[1])
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'ID: {role.id}')
        
        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

    @commands.command(cls=perms.Lock, level=2, guild_only=True, name='rolemenu', aliases=['rmenu'], usage='rolemenu <title> | <color> | <*roles>')
    async def rolemenu(self, ctx, *data):
        '''Create a role menu.
        Role menus are powered by message reactions and can hold up to 15 roles. 
        Arguments must be separated by pipes: `|`
        *title* must be no more than 256 characters long.
        *color* must be a color represented in hexadecimal format.
        *roles* must be a list of role IDs delimited by spaces.\n
        **Example:```yml\n .rolemenu Color Roles | #8bb3f8 | 546836599141302272```**
        '''
        await ctx.message.delete()

        title, color, role_ids = ' '.join(data).split('|')
        title = title.strip()
        color = color.strip('# ')
        role_ids = role_ids.strip()

        try:
            color = int(color, 16)
        except ValueError:
            return await ctx.send(f'{ctx.author.mention} `color` must be a valid hex code.', delete_after=5)

        if len(role_ids.split(' ')) > 15:
            return await ctx.send(f'{ctx.author.mention} Maximum of 15 roles cannot be exceeded.', delete_after=5)
        elif len(title) > 256:
            return await ctx.send(f'{ctx.author.mention} `title` must be no longer than 256 characters.', delete_after=5)

        roles = []
        for role_id in role_ids.split(' '):
            role = ctx.guild.get_role(int(role_id))
            if not role:
                return await ctx.send(f'{ctx.author.mention} One or more roles could not be resolved: `{role_id}` is invalid.', delete_after=5)

            roles.append(role)

        desc = ''
        for i, role in enumerate(roles):
            desc += f'**{i+1}.** {str(role)}\n'
        embed = Embed(title=title, description=desc.strip('\n'), color=color)
        menu = await ctx.send(embed=embed)

        ids = ''
        for i, role in enumerate(roles):
            await menu.add_reaction(utils.emoji[i+1])
            ids += str(role.id) + ' '

        await self.bot.rmenus.update((ctx.guild.id, menu.id), 'role_ids', ids)

def setup(bot):
    bot.add_cog(Roles(bot))
import io
import random

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests

import perms
from utils import emoji, level, levelxp

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, guild_only=True, name='server', aliases=['serverinfo'], usage='server')
    @commands.bot_has_permissions(external_emojis=True)
    async def server(self, ctx):
        '''Display server profile.
        If the server has a banner, it will be displayed here.
        This profile cannot be customized.\n
        **Example:```yml\n.server```**
        '''
        guild = ctx.guild

        bots = 0
        statuses = dict(online=0, idle=0, dnd=0, streaming=0, offline=0)
        for member in guild.members:
            if member.bot: bots += 1
            if member.activity and member.activity.type == 'streaming':
                statuses['streaming'] += 1
                continue
            statuses[str(member.status)] += 1

        desc = (f'**{escape_markdown(str(guild.owner))}** {emoji["owner"]}\n\n'
        f'**Region:** {guild.region}\n'
        f'**Verification:** {guild.verification_level}\n\n')
        
        emojis = guild.emojis
        n = random.sample(emojis, 10 if len(emojis) > 10 else len(emojis)) 
        emojis = ''.join(str(e) for e in n)

        stats = f'**Humans:** `{guild.member_count-bots}` **Bots:** `{bots}`\n'
        for key in list(statuses.keys()):
            stats += f'{emoji[key]} `{statuses[key]}` '

        embed = Embed(description=desc)
        embed.set_author(name=guild.name, icon_url=guild.owner.avatar_url)
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name=f'Members `{guild.member_count}`', value=stats, inline=False)
        embed.add_field(name=f'Emoji `{len(guild.emojis)}`', value=emojis, inline=False)
        
        embed.set_image(url=guild.banner_url)
        embed.set_footer(text=f'ID: {guild.id}, created')
        embed.timestamp = guild.created_at

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='leaderboard', aliases=['lb'], usage='leaderboard')
    async def leaderboard(self, ctx):
        '''Display leaderboard.\n
        **Example:```yml\n.lb```**
        '''
        cur = await self.bot.con.execute('SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10')
        records = await cur.fetchall()
        
        embed = Embed(title='Leaderboard')
        inline = False
        for i, record in enumerate(records):
            user_id, xp = record
            user = await self.bot.fetch_user(user_id)
            embed.add_field(name=f'**{i+1}.** {user}', value=f'**```yml\nLevel: {level(xp)}\nXP: {xp}```**', inline=inline)
            inline = True

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='profile', aliases=['card', 'info', 'user'], usage='profile [member]')
    @commands.bot_has_permissions(attach_files=True, external_emojis=True, manage_messages=True)
    async def profile(self, ctx, *, member: discord.Member = None):
        '''Display profile card.
        The accent color and the bio features may be customized.
        This only works with members within the server.\n
        **Example:```yml\n.profile @Tau#4272\n.profile 608367259123187741```**
        '''
        if not member:
            member = ctx.author

        if member.id == self.bot.user.id:
            ctx.command = self.bot.get_command('tau')
            return await self.bot.invoke(ctx)

        if member.bot:
            return

        message = await ctx.send(emoji['loading'])

        res = requests.get(str(member.avatar_url))
        with Image.open('assets/profile.png') as template, \
             Image.open('assets/border.png') as border, \
             Image.open(io.BytesIO(res.content)) as avatar:
            # Copy the template and initialize the draw object
            im = template.copy()
            draw = ImageDraw.Draw(im)

            xp = self.bot.users_[member.id]['xp']
            lvl = level(self.bot.users_[member.id]['xp'])
            accent = self.bot.users_[member.id]['accent']
            font = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 200)
            font2 = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 250)
            bigfont = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 500)

            # Circular mask for avatar
            size = (512, 512)
            mask = Image.new('L', size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + size, fill=255)
            avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
            
            # Avatar
            w, h = avatar.size
            im.paste(avatar, (594-w//2, 378-h//2), mask)

            # Level
            w, h = bigfont.getsize(str(lvl))
            xo, yo = font.getoffset(str(lvl))
            draw.text((594-w/2-xo/2, 930-h/2-yo/2), str(lvl), font=bigfont, fill=accent)

            # Fetch the rank of the member
            cur = await self.bot.con.execute('SELECT user_id FROM users ORDER BY xp DESC')
            rank = 1
            while True:
                uid = await cur.fetchone()
                if uid[0] == member.id:
                    break
                rank += 1

            # To iterate over the different texts, I decided to use a
            # list of 2-tuples where the first index is the value of
            # the midpoint of the corresponding image on the y-axis
            # and the other is the integer value.
            text = [
                (252, rank), # Global rank
                (624, xp), # XP
                (978, self.bot.users_[member.id]['tickets']) # Tickets
            ]
            for y, val in text:
                # Python has this neat trick to automatically interpolate
                # commas into integers if they're long enough.
                msg = f'{val:,}'

                # The text becomes taller, since the commas dip below the rest
                # of the letters. boost is to keep the text aligned with the
                # image. This will break if the font size is changed, as it
                # is a hard coded value.
                boost = 0
                if ',' in msg:
                    boost = 22

                _, h = font.getsize(msg)
                _, offset = font.getoffset(msg)
                draw.text((1600, y-h/2-offset/2+boost), msg, font=font, fill=accent)

            # Progress bar
            # Calculate the length of the progress bar as a
            # percentage of the xp to next level
            currentxp = xp - levelxp(lvl)
            totalxp = levelxp(lvl + 1) - levelxp(lvl)
            ratio = currentxp / totalxp
            pos = 2500 * ratio + 129
            draw.rectangle([129, 1264, pos, 1666], fill=accent)

            # Progress bar text
            msg = f'{currentxp}/{totalxp}'
            x, _ = im.size
            w, h = font.getsize(msg)
            _, offset = font.getoffset(msg)
            draw.text((x/2-w/2, 1465-h/2-offset/2), msg, font=font2, fill=f'#ffffff')

            # Finalize by pasting the progress bar border
            # to prevent the corners of the rectangle
            # from jutting out.
            final = Image.alpha_composite(im, border)

            buffer = io.BytesIO()
            final.save(buffer, 'png')

            buffer.seek(0)

        desc = f'{emoji[str(member.status)]} **{escape_markdown(member.display_name)}\n`{member}`**\n\n'
        if bio := self.bot.users_[member.id]["bio"]:
            desc += f'**```yml\n{bio}```**'
        
        embed = Embed(description=desc)
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'ID: {member.id}, created')
        embed.timestamp = member.created_at

        await message.delete()
        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

def setup(bot):
    bot.add_cog(Social(bot))
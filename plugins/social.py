import datetime
import io
import json
import random

import discord
from discord import Embed, File
from discord.ext import commands
from discord.ext.commands import command, guild_only
from discord.utils import escape_markdown
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import pprint

import ccp
import config
import utils
from utils import Emoji, level, levelxp

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._cd = commands.CooldownMapping.from_cooldown(1, 86400.0, commands.BucketType.user)

    def get_gif(self, query: str) -> str:
        query = query.replace(' ', '%20')
        filters = 'contentfilter=medium&mediafilter=minimal&limit=1'
        res = requests.get(f'https://api.tenor.com/v1/random?q={query}&key={config.tenor_api_key}&{filters}')
        if res.status_code == 200:
            obj = json.loads(res.content)
            url = obj['results'][0]['media'][0]['gif']['url']
            return url
        
        return ccp.error('Failed to reach Tenor servers')
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        
        # birthday stuff
        bday = datetime.date.fromisoformat(self.bot.users_[msg.author.id]['birthday'])
        today = datetime.date.today()
        if today.month == bday.month and today.day == bday.day:
            bucket = self._cd.get_bucket(msg)
            limited = bucket.update_rate_limit()
            if not limited:
                embed = Embed(color=utils.Color.pinky)
                embed.set_author(name=f'Happy birthday, {msg.author.display_name}!', icon_url='attachment://unknown.png')

                await msg.reply(file=File('assets/cake.png', 'unknown.png'), embed=embed)

    @command(name='birthday', aliases=['bday'], usage='birthday <mm/dd/yyyy>')
    async def birthday(self, ctx, date: str):
        '''Set your birthday.
        I will wish you happy birthday when the day comes!\n
        **Example:```yml\n♤birthday 1/1/2000```**
        '''
        m, d, y = date.split('/')
        if len(y) == 2:
            y = f'20{y}'
        
        bday = datetime.date(int(y), int(m), int(d))

        await self.bot.users_.update(ctx.author.id, 'birthday', str(bday))
        
        embed = Embed(color=utils.Color.pinky)
        embed.set_author(name=f'Birthday has been set to {date}', icon_url='attachment://unknown.png')

        await ctx.reply(file=File('assets/cake.png', 'unknown.png'), embed=embed, mention_author=False)

    @command(name='boop', usage='boop <member>')
    @guild_only()
    async def boop(self, ctx, member: discord.Member):
        '''Boop someone!\n
        **Example:```yml\n♤boop @Tau#4272```**
        '''
        gif = self.get_gif('anime boop nose')
        if gif:
            recipient = 'themselves' if ctx.author == member else member.display_name
            embed = Embed(color=utils.Color.lilac)
            embed.set_author(name=f'{ctx.author.display_name} booped {recipient}!', icon_url=ctx.author.avatar_url)
            embed.set_image(url=gif)
            
            await ctx.send(embed=embed)

    @command(name='hug', usage='hug <member>')
    @guild_only()
    async def hug(self, ctx, member: discord.Member):
        '''Hug someone!\n
        **Example:```yml\n♤hug @Tau#4272```**
        '''
        gif = self.get_gif('anime hug cute')
        if gif:
            recipient = 'themselves' if ctx.author == member else member.display_name
            embed = Embed(color=utils.Color.lilac)
            embed.set_author(name=f'{ctx.author.display_name} hugged {recipient}!', icon_url=ctx.author.avatar_url)
            embed.set_image(url=gif)
            
            await ctx.send(embed=embed)
    
    @command(name='kiss', usage='kiss <member>')
    @guild_only()
    async def kiss(self, ctx, member: discord.Member):
        '''Kiss someone!\n
        **Example:```yml\n♤kiss @Tau#4272```**
        '''
        gif = self.get_gif('anime kiss')
        if gif:
            recipient = 'themselves' if ctx.author == member else member.display_name
            embed = Embed(color=utils.Color.pinky)
            embed.set_author(name=f'{ctx.author.display_name} kissed {recipient}!', icon_url=ctx.author.avatar_url)
            embed.set_image(url=gif)
            
            await ctx.send(embed=embed)

    @command(name='pat', aliases=['headpat'], usage='pat <member>')
    @guild_only()
    async def pat(self, ctx, member: discord.Member):
        '''Headpat someone!\n
        **Example:```yml\n♤pat @Tau#4272```**
        '''
        gif = self.get_gif('anime headpat')
        if gif:
            recipient = 'themselves' if ctx.author == member else member.display_name
            embed = Embed(color=utils.Color.lilac)
            embed.set_author(name=f'{ctx.author.display_name} patted {recipient}!', icon_url=ctx.author.avatar_url)
            embed.set_image(url=gif)
            
            await ctx.send(embed=embed)
    
    @command(name='slap', usage='slap <member>')
    @guild_only()
    async def slap(self, ctx, member: discord.Member):
        '''Slap someone! (not too hard tho)\n
        **Example:```yml\n♤slap @Tau#4272```**
        '''
        gif = self.get_gif('anime slap')
        if gif:
            recipient = 'themselves' if ctx.author == member else member.display_name
            embed = Embed(color=utils.Color.red)
            embed.set_author(name=f'{ctx.author.display_name} slapped {recipient}!', icon_url=ctx.author.avatar_url)
            embed.set_image(url=gif)
            
            await ctx.send(embed=embed)

    @command(name='server', aliases=['serverinfo'], usage='server')
    @commands.bot_has_permissions(external_emojis=True)
    @guild_only()
    async def server(self, ctx):
        '''Display server profile.
        If the server has a banner, it will be displayed here.
        This profile cannot be customized.\n
        **Example:```yml\n♤server```**
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

        desc = (f'{guild.owner.mention} {Emoji.owner}\n\n'
        f'**Region:** {guild.region}\n'
        f'**Verification:** {guild.verification_level}\n\n')
        
        emojis = guild.emojis
        n = random.sample(emojis, 10 if len(emojis) > 10 else len(emojis)) 
        emojis = ''.join(str(e) for e in n)

        stats = f'**Humans:** `{guild.member_count-bots}` **Bots:** `{bots}`\n'
        for key in list(statuses.keys()):
            stats += f'{Emoji.statuses[key]} `{statuses[key]}` '

        embed = Embed(description=desc)
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.add_field(name=f'Members `{guild.member_count}`', value=stats, inline=False)
        embed.add_field(name=f'Emoji `{len(guild.emojis)}`', value=emojis, inline=False)
        
        embed.set_image(url=guild.banner_url)
        embed.set_footer(text=f'ID: {guild.id}, created')
        embed.timestamp = guild.created_at

        await ctx.send(embed=embed)

    @command(name='leaderboard', aliases=['lb'], usage='leaderboard')
    @guild_only()
    async def leaderboard(self, ctx):
        '''Display leaderboard.\n
        **Example:```yml\n♤lb```**
        '''
        async with self.bot.pool.acquire() as con:
            records = await con.fetch(f'SELECT user_id, xp FROM members WHERE guild_id = {ctx.guild.id} ORDER BY xp DESC')
            highscores = []
            for record in records:
                user_id, xp = record.values()
                member = ctx.guild.get_member(user_id)
                if member:
                    highscores.append((member, xp))
                    if len(highscores) == 10:
                        break

        embed = Embed(color=utils.Color.sky)
        embed.set_author(name='Leaderboard', icon_url='attachment://unknown.png')
        inline = False
        for i, score in enumerate(highscores):
            member, xp = score
            name = escape_markdown(str(member))
            embed.add_field(name=f'**{i+1}.** {name}', value=f'**```yml\nLevel: {level(xp)}\nXP: {xp}```**', inline=inline)
            inline = True

        await ctx.send(file=File('assets/dot.png', 'unknown.png'), embed=embed)

    @command(name='profile', aliases=['card', 'info', 'user'], usage='profile [member]')
    @commands.bot_has_permissions(attach_files=True, external_emojis=True, manage_messages=True)
    @guild_only()
    async def profile(self, ctx, *, member: discord.Member = None):
        '''Display profile card.
        The accent color and the bio features may be customized.
        This only works with members within the server.\n
        **Example:```yml\n♤profile @Tau#4272\n♤profile 608367259123187741```**
        '''
        if not member:
            member = ctx.author

        if member.id == self.bot.user.id:
            ctx.command = self.bot.get_command('tau')
            return await self.bot.invoke(ctx)

        if member.bot:
            return

        message = await ctx.send(Emoji.loading)

        res = requests.get(str(member.avatar_url))
        with Image.open('assets/profile.png') as template, \
             Image.open('assets/border.png') as border, \
             Image.open(io.BytesIO(res.content)) as avatar:
            # Copy the template and initialize the draw object
            im = template.copy()
            draw = ImageDraw.Draw(im)

            xp = self.bot.members[member.id, ctx.guild.id]['xp']
            lvl = level(xp)
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
            async with self.bot.pool.acquire() as con:
                async with con.transaction():
                    rank = 1
                    async for record in con.cursor('SELECT user_id FROM members ORDER BY xp DESC'):
                        if record['user_id'] == member.id:
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

        # decorators
        dec = []
        if member == ctx.guild.owner:
            dec.append(Emoji.owner)

        if member.premium_since:
            dec.append(Emoji.boost)

        dec = ' '.join(dec)

        desc = f'{Emoji.statuses[str(member.status)]} **{escape_markdown(member.display_name)} {dec}\n`{member}`**\n\n'
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
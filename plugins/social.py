import io

import requests
import discord
from discord import Embed, File
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps

import perms
from utils import res_member, level, levelxp

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(cls=perms.Lock, guild_only=True, name='guild', aliases=['guildinfo'], usage='guild')
    async def guild(self, ctx):
        '''Display guild profile.
        If the server has a banner, it will be displayed here.
        This profile cannot be customized.\n
        **Example:```yml\n.guild```**
        '''
        guild = ctx.guild

        statuses = dict(online=0, idle=0, dnd=0, offline=0)
        for member in guild.members:
            statuses[str(member.status)] += 1

        desc = (f'**{guild.name}**\n'
        f'**`{guild.owner.name}#{guild.owner.discriminator}`**\n\n'
        f'**Region:** {str(guild.region)}\n'
        f'**Verification:** {str(guild.verification_level)}\n'
        f'**Members:** {guild.member_count}\n'
        f'<:online:659931852660015104> {statuses["online"]}\n'
        f'<:idle:659932829508960256> {statuses["idle"]}\n'
        f'<:dnd:659932885062516746> {statuses["dnd"]}\n'
        f'<:offline:659932900405411842> {statuses["offline"]}')
        embed = Embed(description=desc, color=0x1f2124)
        embed.set_footer(text=f'ID: {guild.id}')
        embed.set_thumbnail(url=guild.icon_url)
        if guild.banner_url:
            embed.set_image(url=guild.banner_url)
        
        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, name='leaderboard', aliases=['lb'], usage='leaderboard')
    async def leaderboard(self, ctx):
        '''Display leaderboard.\n
        **Example:```yml\n.lb```**
        '''
        cur = await self.bot.con.execute('SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10')
        records = await cur.fetchall()
        lb = ''
        for i, record in enumerate(records):
            user_id, xp = record
            user = await self.bot.fetch_user(user_id)
            lb += f'**{i+1}.** {user.name}#{user.discriminator} ー {xp} XP\n'

        embed = Embed(title='Leaderboard', description=lb.strip('\n'), color=0x1f2124)

        await ctx.send(embed=embed)

    @commands.command(cls=perms.Lock, guild_only=True, name='profile', aliases=['card', 'info', 'user'], usage='profile [mention]')
    async def profile(self, ctx):
        '''Display profile card.
        The accent color and the bio features may be customized.
        In addition to a mention, *mention* can also be substituted with a user ID.
        Although, this only works with members within the guild.\n
        **Example:```yml\n.profile @Tau#4272\n.profile 608367259123187741```**
        '''
        member = await res_member(ctx)
        if member.id == self.bot.user.id:
            ctx.command = self.bot.get_command('tau')
            return await self.bot.invoke(ctx)

        if not member or member.bot:
            return

        res = requests.get(str(member.avatar_url))
        with Image.open('assets/profile.png') as template, \
             Image.open('assets/border.png') as border, \
             Image.open('assets/avatar_border.png') as avatar_border, \
             Image.open(io.BytesIO(res.content)) as avatar:
            # Copy the template and initialize the draw object
            im = template.copy()
            draw = ImageDraw.Draw(im)

            xp = self.bot.users_[member.id]['xp']
            lvl = level(self.bot.users_[member.id]['xp'])
            accent = self.bot.users_[member.id]['accent']
            font = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 250)
            bigfont = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 500)

            # Avatar
            size = (512, 512)
            mask = Image.new('L', size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0) + size, fill=255)
            avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
            
            # Avatar border
            x, y = avatar_border.size
            w, h = avatar.size
            avatar_border.paste(avatar, ((x-w)//2, (y-h)//2), mask)
            im.alpha_composite(avatar_border, (594-x//2, 378-y//2))

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
                (632, xp), # XP
                (1016, self.bot.users_[member.id]['tickets']) # Tickets
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
            draw.text((x/2-w/2, 1465-h/2-offset/2), msg, font=font, fill=f'#ffffff')


            # Finalize by pasting the progress bar border
            # to prevent the corners of the rectangle
            # from jutting out.
            final = Image.alpha_composite(im, border)

            buffer = io.BytesIO()
            final.save(buffer, 'png')

            buffer.seek(0)

        status = {
            'online': '<:online:659931852660015104>',
            'idle': '<:idle:659932829508960256>',
            'dnd': '<:dnd:659932885062516746>',
            'offline': '<:offline:659932900405411842>'
        }

        desc = (f'{status[str(member.status)]} **{member.display_name}\n'
        f'`{member.name}#{member.discriminator}`\n\n'
        f'```yml\n{self.bot.users_[member.id]["bio"]}```**')
        embed = Embed(description=desc, color=0x1f2124)
        embed.set_image(url='attachment://unknown.png')
        embed.set_footer(text=f'ID: {member.id}')

        await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)

        '''
        memo = '📝'
        x = '❌'
        bio = self.bot.users_[ctx.author.id]['bio']
        menu_embed = Embed(title=member.display_name, description='**Please select one of the below to edit.**', color=0x1f2124)
        menu_embed.add_field(name='\u200b', value='**Accent:\nBio:**')
        menu_embed.add_field(name='\u200b', value=f'{self.bot.users_[ctx.author.id]["accent"]}\n{bio if len(bio) < 64 else bio[:64] + "..."}')
        try:
            flag = True
            while flag:
                msg = await ctx.send(file=File(buffer, 'unknown.png'), embed=embed)
                await msg.add_reaction(memo)
                await self.bot.wait_for('reaction_add', timeout=90, check=lambda reaction, user: str(reaction.emoji) == memo and user == ctx.author)
                await msg.delete()

                msg = await ctx.send(embed=menu_embed)
                await msg.add_reaction(x)
                
                while True:
                    on_msg = self.bot.wait_for('message', check=lambda msg: msg.content.startswith('edit') and len(msg.content.split()) > 2 and msg.author == ctx.author)
                    on_react = self.bot.wait_for('reaction_add', check=lambda reaction, user: str(reaction.emoji) == x and user == ctx.author)
                    done, pending = await asyncio.wait([on_msg, on_react], timeout=90, return_when=asyncio.FIRST_COMPLETED)
                    task = asyncio.create_task(on_msg)
                    for future in pending:
                        future.cancel()
                    if task in done:
                        content = done.pop().result().content
                        sep = content.split()
                        if sep[1] == 'accent':
                            # Matches if string is a hex color code
                            code = sep[2]
                            match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', code)
                            if match:
                                await self.bot.users_.update(ctx.author.id, 'accent', code)
                            else:
                                await ctx.send('Must be a hex color code.')
                        elif sep[1] == 'bio':
                            if '"' not in content:
                                await self.bot.users_.update(ctx.author.id, 'bio', ' '.join(sep[2:]))
                        else:
                            ctx.send(f'`{sep[1]}` is not editable.')
                    else:
                        await msg.delete()
                        flag = False
                        break
        except asyncio.TimeoutError:
            await msg.clear_reactions()
        else:
            for future in pending:
                future.cancel()
        '''

def setup(bot):
    bot.add_cog(Social(bot))
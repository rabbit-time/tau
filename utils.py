import asyncio
import datetime
import io
import time

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown
from PIL import Image, ImageDraw, ImageFont

# Emoji taken from a private emoji server.
# These must be redefined if you fork, or
# everything is going to break.
emoji = {
    'progress': '<:progress:683525894530138171>',
    'tickets': '<:credits:702269510488686663>',
    'sound': '<:sound:673362944280494080>',
    'mute': '<:mute:673362944280494110>',
    'cuffs': '<:cuffs:678393038095122461>',
    'on': '<:toggleon:686105837294452736>',
    'off': '<:toggleoff:686105824065880150>',
    'settings': '<:settings:686113054001594372>',
    'online': '<:online:659931852660015104>',
    'idle': '<:idle:659932829508960256>',
    'dnd': '<:dnd:659932885062516746>',
    'streaming': '<:streaming:697272348679733288>',
    'offline': '<:offline:659932900405411842>',
    'owner': '<:owner:697338812971483187>',
    'loading': '<a:loading:688977787528544301>',
    'coin0': '<:0_:702492300877496320>',
    'coin1': '<:1_:702492300894535750>',
    '#': '<:hash:702696629446115378>',
    1: '<:01:683462884625481802>',
    2: '<:02:683462884650516492>',
    3: '<:03:683462884378148865>',
    4: '<:04:683462884755505173>',
    5: '<:05:683462884340006963>',
    6: '<:06:683462884696916021>',
    7: '<:07:683462884730339509>',
    8: '<:08:683462884793385058>',
    9: '<:09:683462884726145052>',
    10: '<:10:683462884709367818>',
    11: '<:11:683535077615206419>',
    12: '<:12:683535077765808128>',
    13: '<:13:683535077816532992>',
    14: '<:14:683535077715869773>',
    15: '<:15:683535077828984907>',
}

class RoleNotFound(Exception):
    '''Exception: Role could not be found'''

def display_color(color: discord.Color) -> io.BytesIO:
    im = Image.new('RGB', (1200, 400), color.to_rgb())
    draw = ImageDraw.Draw(im)

    font = ImageFont.truetype('assets/font/Comfortaa-Bold.ttf', 250)

    x, y = im.width, im.height
    w, h = font.getsize(str(color))
    # Around 6,000,000 just happened to be the sweet spot for white text
    fill = 'black' if color.value > 6000000 else 'white'
    draw.text((x//2-w//2, y//2-h//2), str(color), font=font, fill=fill)

    buffer = io.BytesIO()
    im.save(buffer, 'png')

    buffer.seek(0)

    return buffer

def rgb_to_cmyk(r: int, g: int, b: int):
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 1

    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255

    k = min(c, m, y)
    c = (c - k) / (1 - k)
    m = (m - k) / (1 - k)
    y = (y - k) / (1 - k)

    return c, m, y, k

async def res_member(ctx):
    msg = ctx.message
    if (uid := msg.content.split()[-1]).isdigit():
        if member := ctx.guild.get_member(int(uid)):
            return member
    return msg.mentions[0] if msg.mentions else msg.author

def level(xp):
    return int(((5 ** (2/3)) * (xp ** (2/3))) / 100) + 1

def levelxp(lvl):
    return int(200 * (lvl - 1) ** 1.5) + 1 if lvl != 1 else 0

def findrole(id, guild):
    role = guild.get_role(id)
    if not role:
        raise RoleNotFound
    return role

def parse_time(text):
    units = {
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    time_= ''
    for char in text:
        if char in units.keys() or char.isdigit():
            time_ += char

    try:
        limit = int(time_[:-1])
        unit = units[time_[-1]]
    except:
        raise commands.BadArgument

    limit *= unit

    return time_, limit
        
async def remind(bot, user, channel, reminder, remind_time):
    now = int(time.time())
    delay = remind_time - now if remind_time > now else 0
    await asyncio.sleep(delay)

    embed = Embed(description=f'Remember to **{reminder}**!')
    embed.set_author(name=escape_markdown(user.display_name), icon_url=user.avatar_url)
    embed.set_footer(text='Time\'s up!', icon_url='attachment://unknown.png')
    embed.timestamp = datetime.datetime.utcnow()

    await channel.send(f'Hey {user.mention}!', file=File('assets/clock.png', 'unknown.png'), embed=embed)

    await bot.reminders.delete((user.id, remind_time))

async def automute(bot, user_id, guild_id, unmute_time):
    now = int(time.time())
    delay = unmute_time - now if unmute_time > now else 0
    await asyncio.sleep(delay)

    try:
        guild = bot.get_guild(guild_id)
        member = await guild.fetch_member(user_id)
        bind = guild.get_role(bot.guilds_[guild_id]['bind_role'])
        if bot.members[user_id, guild_id]['detained'] == -1:
            await member.remove_roles(bind)
    except:
        pass

    await bot.members.update((user_id, guild_id), 'muted', -1)
    del bot.mute_tasks[user_id, guild_id]

async def tally(msg, emoji1, emoji2):
    votes = list(filter(lambda r: str(r.emoji) in (emoji1, emoji2), msg.reactions))
    if len(votes) != 2:
        return [], []

    upvote, downvote = votes   
    upvotes = await upvote.users().flatten()
    downvotes = await downvote.users().flatten()
    for ls in (upvotes, downvotes):
        if msg.guild.me in ls:
            ls.remove(msg.guild.me)

    return upvotes, downvotes

async def autodetain(bot, member, guild, msg, timeout):
    mod = guild.get_role(bot.guilds_[guild.id]['mod_role'])
    admin = guild.get_role(bot.guilds_[guild.id]['admin_role'])
    bind = guild.get_role(bot.guilds_[guild.id]['bind_role'])
    if not mod or not admin or not bind:
        return

    def check(reaction):
        return str(reaction.emoji) in ('🔺', '🔻') and reaction.message_id == msg.id and not reaction.member.bot

    try:
        dupe = mod.members + admin.members
        staff = []
        for mem in dupe:
            if mem not in staff and not mem.bot:
                staff.append(mem)

        upvotes, downvotes = await tally(msg, '🔺', '🔻')
        votes = len(upvotes) + len(downvotes)
        if votes == len(staff):
            raise asyncio.TimeoutError

        while True:
            now = int(time.time())
            on_react = asyncio.create_task(bot.wait_for('raw_reaction_add', check=check))
            on_leave = asyncio.create_task(bot.wait_for('member_remove', check=lambda m: m.guild.id == guild.id and m.id == member.id))
            done, pending = await asyncio.wait([on_react, on_leave], timeout=abs(timeout-now), return_when=asyncio.FIRST_COMPLETED)
            
            for future in pending:
                future.cancel()
            
            if on_leave in done:
                member = done.pop().result()
                votes = -1
                raise asyncio.TimeoutError
            
            reaction = done.pop().result()
            user = reaction.member

            msg = await msg.channel.fetch_message(reaction.message_id)
            upvotes, downvotes = await tally(msg, '🔺', '🔻')

            if (user not in staff and user != guild.owner) or (user in upvotes and user in downvotes):
                await msg.remove_reaction(reaction.emoji, user)
                continue

            votes = len(upvotes) + len(downvotes)
            if votes == len(staff):
                raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        num = 'all' if votes == len(staff) else votes
        if len(upvotes) >= len(downvotes) and votes != -1:
            ban = False
            res = f'yml\n+ {member.display_name} will not be banned'
            color = 0x2aa198
        else:
            ban = True
            res = f'diff\n- {member.display_name} has been banned'
            color = 0xff4e4e

        decision = 'affirmed' if ban else 'reversed'
        desc = f'The votes of {num} staff members have been tallied.' if votes != -1 else f'**{member.display_name}** has left the guild.'
        embed = Embed(title='Final Verdict', description=desc, color=color)
        if votes != -1:
            embed.add_field(name='\u200b', value=f':small_red_triangle: **{len(upvotes)}**', inline=True)
            embed.add_field(name='\u200b', value=f':small_red_triangle_down: **{len(downvotes)}**', inline=True)
        embed.add_field(name='\u200b', value=f'**The decision has been {decision}.```{res}```**', inline=False)
        await msg.channel.send(embed=embed)

        if ban:
            await member.ban(delete_message_days=0)
        else:
            await member.remove_roles(bind)

        await bot.members.update((member.id, guild.id), 'detained', -1)

async def before(ctx):
    member = await res_member(ctx)
    if not ctx.bot.users_.get(member.id):
        await ctx.bot.users_.insert(member.id)
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
    'sound': '<:sound:702809258974249011>',
    'mute': '<:mute:702809258915397672>',
    'cuffs': '<:cuffs:678393038095122461>',
    'hammer': '<:hammer:702793803677040692>',
    'warn': '<:warn:706214120151711844>',
    'on': '<:toggleon:686105837294452736>',
    'off': '<:toggleoff:686105824065880150>',
    'settings': '<:settings:686113054001594372>',
    'online': '<:online:659931852660015104>',
    'idle': '<:idle:659932829508960256>',
    'dnd': '<:dnd:659932885062516746>',
    'streaming': '<:streaming:697272348679733288>',
    'offline': '<:offline:659932900405411842>',
    'owner': '<:owner:697338812971483187>',
    'boost': '<:boost:708098202339115119>',
    'loading': '<a:loading:688977787528544301>',
    'coin0': '<:0_:702492300877496320>',
    'coin1': '<:1_:702492300894535750>',
    'die1': '<:d1:703190416606101535>',
    'die2': '<:d2:703190416820011049>',
    'die3': '<:d3:703190416924606484>',
    'die4': '<:d4:703190416962355252>',
    'die5': '<:d5:703190416987783269>',
    'die6': '<:d6:703190416933257232>',
    '#': '<:hash:702696629446115378>',
    'start': '<:start:706610361960497172>',
    'previous': '<:previous:706610510199652412>',
    'next': '<:next:706610889188573194>',
    'end': '<:end:706610923346853938>',
    'stop': '<:stop:706610934763749426>',
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

class Color:
    gold = 0xfbb041
    green = 0x2aa198
    sky = 0x88b3f8
    red = 0xf94a4a
    rainbow = (red, 0xffa446, 0xffc049, green, 0x55b8f8, 0xc8aaff, 0xffadca)

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

def rgb_to_cmyk(r: float, g: float, b: float):
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

def cmyk_to_rgb(c: float, m: float, y: float, k: float):
    r = (1 - c) * (1 - k) * 255
    g = (1 - m) * (1 - k) * 255
    b = (1 - y) * (1 - k) * 255
    
    return r, g, b

def rgb_to_hsl(r: float, g: float, b: float):
    r /= 255
    g /= 255
    b /= 255

    cmax = max(r, g, b)
    cmin = min(r, g, b)

    Δ = cmax - cmin
    l = (cmax + cmin) / 2

    if Δ == 0:
        h = s = 0
    else:
        s = Δ / (1 - abs(2*l-1))
        if cmax == r:
            h = (g - b) / Δ % 6
        if cmax == g:
            h = (b - r) / Δ + 2
        if cmax == b:
            h = (r - g) / Δ + 4
    
    h *= 60
    
    return h, s, l

def rgb_to_hsv(r: float, g: float, b: float):
    r /= 255
    g /= 255
    b /= 255

    cmax = v = max(r, g, b)
    cmin = min(r, g, b)

    Δ = cmax - cmin

    if Δ == 0:
        h = s = 0
    else:
        s = Δ / cmax
        if cmax == r:
            h = (g - b) / Δ % 6
        if cmax == g:
            h = (b - r) / Δ + 2
        if cmax == b:
            h = (r - g) / Δ + 4
    
    h *= 60
    
    return h, s, v

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
    time_ = ''
    for char in text:
        if char in 'mhd' or char.isdigit():
            time_ += char

    try:
        delay = int(time_[:-1])
        unit = time_[-1]
    except:
        raise commands.BadArgument

    if unit == 'm':
        delta = datetime.timedelta(minutes=delay)
    if unit == 'h':
        delta = datetime.timedelta(hours=delay)
    if unit == 'd':
        delta = datetime.timedelta(days=delay)

    return time_, delta
        
async def remind(bot, user, channel, reminder, timeout):
    now = datetime.datetime.utcnow()
    Δ = (timeout-now).total_seconds()
    await asyncio.sleep(Δ)

    embed = Embed(description=f'Remember to **{reminder}**!')
    embed.set_author(name=escape_markdown(user.display_name), icon_url=user.avatar_url)
    embed.set_footer(text='Time\'s up!', icon_url='attachment://unknown.png')
    embed.timestamp = now

    await channel.send(f'Hey {user.mention}!', file=File('assets/clock.png', 'unknown.png'), embed=embed)

    async with bot.pool.acquire() as con:
        query = 'DELETE FROM reminders WHERE user_id = $1 AND channel_id = $2 AND time = $3 AND reminder = $4'
        await con.execute(query, user.id, channel.id, timeout, reminder)

async def automute(bot, user_id, guild_id, timeout: datetime):
    now = datetime.datetime.utcnow()
    Δ = (timeout-now).total_seconds()
    await asyncio.sleep(Δ)

    guild = bot.get_guild(guild_id)
    if guild:
        member = guild.get_member(user_id)
        bind = guild.get_role(bot.guilds_[guild_id]['bind_role'])
        if member and bind:
            await member.remove_roles(bind)

    del bot.mute_tasks[user_id, guild_id]
    bot.members[user_id, guild_id]['muted'] = None
    async with bot.pool.acquire() as con:
        query = 'UPDATE members SET muted = $1 WHERE user_id = $2 AND guild_id = $3'
        await con.execute(query, None, user_id, guild_id)

async def before(ctx):
    if not ctx.bot.users_.get(ctx.author.id):
        await ctx.bot.users_.insert(ctx.author.id)

    if ctx.guild:
        for kw in list(ctx.kwargs.values()):
            if isinstance(kw, discord.Member) and not ctx.bot.users_.get(kw.id):
                await ctx.bot.users_.insert(kw.id)

# Default database values

_def_guild = {
    'prefix': '.',
    'system_channel': 0,
    'starboard_channel': 0,
    'star_quantity': 3,
    'welcome_message': 'Hi @mention, welcome to @guild!',
    'goodbye_message': 'Bye @user!',
    'welcome_messages': False,
    'goodbye_messages': False,
    'levelup_messages': False,
    'autorole': 0,
    'mod_role': 0,
    'admin_role': 0,
    'bind_role': 0
}

_def_user = {
    'tickets': 200,
    'xp': 0,
    'accent': '#8bb3f8',
    'bio': ''
}

_def_member = {
    'xp': 0,
    'muted': None
}

_def_role_menu = {
    'role_ids': ''
}

_def_rank = {
    'role_ids': ''
}

_def_star = {
    'star_id': 0
}

_def_reminder = {
    'channel_id': 0,
    'reminder': '',
}

_def_rule = {
    'rule': ''
}

_def_modlog = {
    'action': '',
    'time': 0,
    'reason': ''
}

guilds_schema = ('guild_id bigint PRIMARY KEY, '
                 'prefix text, '
                 'system_channel bigint, '
                 'starboard_channel bigint, '
                 'star_quantity smallint, '
                 'welcome_message text, '
                 'goodbye_message text, '
                 'welcome_messages bool, '
                 'goodbye_messages bool, '
                 'levelup_messages bool, '
                 'autorole bigint, '
                 'mod_role bigint, '
                 'admin_role bigint, '
                 'bind_role bigint')

users_schema = ('user_id bigint PRIMARY KEY, '
                'tickets bigint, '
                'xp bigint, '
                'accent char(7), '
                'bio text')
    
members_schema = ('user_id bigint, '
                  'guild_id bigint, '
                  'xp bigint, '
                  'muted timestamp')

role_menus_schema = ('guild_id bigint, '
                     'message_id bigint, '
                     'role_ids text')

ranks_schema = ('guild_id bigint PRIMARY KEY, '
                'role_ids text')

stars_schema = ('message_id bigint PRIMARY KEY, '
                'star_id bigint')

reminders_schema = ('user_id bigint, '
                    'channel_id bigint, '
                    'time timestamp, '
                    'reminder text')

rules_schema = ('guild_id bigint, '
                'index_ smallint, '
                'rule text')

modlog_schema = ('user_id bigint, '
                 'guild_id bigint, '
                 'action text, '
                 'time bigint, '
                 'reason text')
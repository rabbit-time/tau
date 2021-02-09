import asyncio
import datetime
import io
import time

import discord
from discord import Embed, File
from discord.ext import commands
from discord.utils import escape_markdown, find
from PIL import Image, ImageDraw, ImageFont

# Emoji taken from a private emoji server.
# These must be redefined if you fork, or
# everything is going to break.
class Emoji:
    credits = '<:credits:702269510488686663>'
    sound = '<:sound:702809258974249011>'
    mute = '<:mute:702809258915397672>'
    hammer = '<:hammer:702793803677040692>'
    warn = '<:warn:706214120151711844>'
    on = '<:toggleon:686105837294452736>'
    off = '<:toggleoff:686105824065880150>'
    settings = '<:settings:686113054001594372>'
    statuses = {
        'online': '<:online:659931852660015104>',
        'idle': '<:idle:659932829508960256>',
        'dnd': '<:dnd:659932885062516746>',
        'streaming': '<:streaming:697272348679733288>',
        'offline': '<:offline:659932900405411842>'
    }
    owner = '<:owner:697338812971483187>'
    boost = '<:boost:708098202339115119>'
    loading = '<a:loading:688977787528544301>'
    coin0 = '<:0_:784503048566210573>'
    coin1 = '<:1_:784503048453095485>'
    dice = (
        '<:d1:703190416606101535>',
        '<:d2:703190416820011049>',
        '<:d3:703190416924606484>',
        '<:d4:703190416962355252>',
        '<:d5:703190416987783269>',
        '<:d6:703190416933257232>'
    )
    hash = '<:hash:702696629446115378>'
    start = '<:start:706610361960497172>'
    previous = '<:previous:706610510199652412>'
    next = '<:next:706610889188573194>'
    end = '<:end:706610923346853938>'
    stop = '<:stop:706610934763749426>'
    trash = '<:trashcan:797688643987701820>'
    link = '<:link:797723082134650900>'

class Color:
    gold = 0xffc669
    green = 0x57c998
    yellow = 0xffc20c
    sky = 0x88b3f8
    cyan = 0x68dbff
    lilac = 0xc4a8ff
    pinky = 0xffb0e6
    red = 0xf94a4a
    rainbow = (red, 0xffa446, gold, green, cyan, lilac, pinky)

class RoleNotFound(Exception):
    '''Exception: Role could not be found'''

def is_dm_only(cmd: commands.Command) -> bool:
    res = find(lambda ch: ch.__qualname__.startswith('dm_only'), cmd.checks)
    return res != None

def is_guild_only(cmd: commands.Command) -> bool:
    res = find(lambda ch: ch.__qualname__.startswith('guild_only'), cmd.checks)
    return res != None

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

async def before(ctx):
    if not ctx.bot.users_.get(ctx.author.id) and not ctx.author.bot:
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
    'welcome_message': 'Hi @name, welcome to @server!',
    'goodbye_message': 'Bye @name!',
    'welcome_messages': False,
    'goodbye_messages': False,
    'levelup_messages': False,
    'autorole': 0,
    'mute_role': 0,
    'automod': False,
    'verify_role': 0,
    'log_channel': 0
}

_def_user = {
    'tickets': 200,
    'accent': '#8bb3f8',
    'bio': '',
    'birthday': None
}

_def_member = {
    'xp': 0,
    'muted': None
}

_def_role_menu = {
    'role_ids': [],
    'emojis': [],
    'limit_': 0
}

_def_rank = {
    'role_ids': [],
    'levels': []
}

_def_star = {
    'star_id': 0
}

_def_reminder = {
    'channel_id': 0,
    'reminder': '',
}

_def_tag = {
    'embed': '',
    'content': ''
}

_def_modlog = {
    'url': '',
    'action': '',
    'time': None,
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
                 'mute_role bigint, '
                 'automod bool, '
                 'verify_role bigint, '
                 'log_channel bigint')

users_schema = ('user_id bigint PRIMARY KEY, '
                'tickets bigint, '
                'accent char(7), '
                'bio text, '
                'birthday date')

members_schema = ('user_id bigint, '
                  'guild_id bigint, '
                  'xp bigint, '
                  'muted timestamp')

role_menus_schema = ('guild_id bigint, '
                     'message_id bigint, '
                     'role_ids bigint[], '
                     'emojis text[], '
                     'limit_ bigint')

ranks_schema = ('guild_id bigint PRIMARY KEY, '
                'role_ids bigint[], '
                'levels bigint[]')

stars_schema = ('message_id bigint PRIMARY KEY, '
                'star_id bigint')

reminders_schema = ('user_id bigint, '
                    'channel_id bigint, '
                    'time timestamp, '
                    'reminder text')

tags_schema = ('guild_id bigint, '
               'name text, '
               'embed text, '
               'content text')

modlog_schema = ('user_id bigint, '
                 'guild_id bigint, '
                 'url text, '
                 'action text, '
                 'time timestamp, '
                 'reason text')

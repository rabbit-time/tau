# Tau Copyright 2019-2020 The Apache Software Foundation

import asyncio
import os
import sys
import time
from collections.abc import Iterable

import aiosqlite
import discord
from discord.ext import commands

import ccp
import config
import utils
import perms

# Checks the version of python
if sys.version_info[0] < 3 or sys.version_info[1] < 8: 
    raise Exception('Python 3.8.0 or higher is required')

bot = commands.Bot(command_prefix=lambda bot, msg: bot.guilds_[msg.guild.id]['prefix'] if msg.guild else bot.guilds_.default['prefix'], help_command=None)

bot.mute_tasks = {}
bot.suppressed = {}
bot.start_time = time.time()

bot.add_check(perms.require, call_once=True)
bot.add_check(lambda ctx: ctx.author not in bot.suppressed.keys() or bot.suppressed.get(ctx.author) != ctx.channel, call_once=True)

bot.before_invoke(utils.before)

# Sums all lines of code in the project for display
bot.code = 0
for dir, _, files in os.walk('.'):
    for file in files:
        if '__' not in file and file.endswith('.py'):
            with open(f'{dir}/{file}', encoding='utf8') as py:
                bot.code += len(py.readlines())

class aobject(object):
    '''Inheriting this class allows async class constructors.'''
    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

class Cache(aobject):
    async def __init__(self, table: str, pk: str, schema: str, default: dict):
        await bot.con.execute(f'CREATE TABLE IF NOT EXISTS {table} ({schema})')
        
        pknum = len(pk.split(', '))
        cur = await bot.con.execute(f'SELECT * FROM {table}')
        cache = {}
        records = await cur.fetchall()
        for record in records:
            index = record[0] if pknum == 1 else record[:pknum]
            cache[index] = {k: record[i+pknum] for i, k in enumerate(default.keys())}

        await bot.con.commit()

        self.table = table
        self.pk = pk
        self._records = cache
        self.default = default.copy()

    def __getitem__(self, key: any):
        return self._records[key]

    def get(self, key: any, default: any = None):
        return self._records.get(key, default)

    def keys(self):
        return self._records.keys()

    def values(self):
        return self._records.values()

    async def delete(self, index: any):
        '''Deletes a record in the database and the cache.'''   
        del self._records[index]
        if isinstance(index, Iterable):
            condition = self.pk.replace(', ', ' = ? AND ')
            await bot.con.execute(f'DELETE FROM {self.table} WHERE {condition} = ?', index)
        else:
            await bot.con.execute(f'DELETE FROM {self.table} WHERE {self.pk} = ?', (index,))
        await bot.con.commit()

    async def insert(self, index: any):
        '''Creates a new record in the database and the cache.'''
        self._records[index] = self.default.copy()

        index = (index,) if not isinstance(index, tuple) else index
        val = index + tuple(self.default.values())
        n = ('?, ' * (len(self.default)+len(index))).strip(', ')
        
        await bot.con.execute(f'INSERT INTO {self.table} VALUES ({n})', tuple(val))
        await bot.con.commit()

    async def update(self, index: any, key: any, val: any):
        '''Updates both the database and the cache. If the record does not exist, it will be created.'''
        if not self._records.get(index):
            await self.insert(index)
        
        self._records[index][key] = val
        if isinstance(val, str):
            val = f'\'{val}\''

        if isinstance(index, Iterable):
            condition = self.pk.replace(', ', ' = ? AND ')
            await bot.con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {condition} = ?', index)
        else:
            await bot.con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {self.pk} = ?', (index,))
        await bot.con.commit()

async def init():
    if not os.path.exists('srv'):
        os.mkdir('srv')
    bot.con = await aiosqlite.connect('srv/db.sqlite3')

    bot.guilds_ = await Cache('guilds', 'guild_id', config.guilds_schema, config._def_guild)
    bot.users_ = await Cache('users', 'user_id', config.users_schema, config._def_user)
    bot.mutes = await Cache('mutes', 'user_id, guild_id', config.mutes_schema, config._def_mute)
    bot.detains = await Cache('detains', 'user_id, guild_id', config.detains_schema, config._def_detain)
    bot.rmenus = await Cache('role_menus', 'guild_id, message_id', config.role_menus_schema, config._def_role_menu)
    
    # Loads plugins and events
    files = [f'plugins.{file[:-3]}' for file in os.listdir('plugins') if '__' not in file] 
    files += [f'events.{file[:-3]}' for file in os.listdir('events') if '__' not in file]
    for file in files:
        ccp.log('Loading', file)
        bot.load_extension(file)
    ccp.done()

loop = asyncio.get_event_loop()                                                                                                                                                                                                                                       
loop.run_until_complete(init())

bot.run(config.token)
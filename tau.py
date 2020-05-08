# Tau Copyright 2019-2020 The Apache Software Foundation

import asyncio
import asyncpg
import os
import sys
import time
from collections.abc import Iterable

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
bot.boot = True

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
        async with bot.pool.acquire() as con:
            await con.execute(f'CREATE TABLE IF NOT EXISTS {table} ({schema})')
            records = await con.fetch(f'SELECT * FROM {table}')
        
        cache = {}
        for record in records:
            pktup = tuple(pk.split(', '))
            index = record[pk] if len(pk.split(', ')) == 1 else tuple(v for k, v in record.items() if k in pktup)
            cache[index] = dict(record)
            for key in pktup:
                del cache[index][key]

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
        
        async with bot.pool.acquire() as con:
            if isinstance(index, Iterable):
                condition = ' AND '.join(f'{k} = ${i+1}' for i, k in enumerate(self.pk.split(', ')))
                await con.execute(f'DELETE FROM {self.table} WHERE {condition}', *index)
            else:
                await con.execute(f'DELETE FROM {self.table} WHERE {self.pk} = $1', index)

    async def insert(self, index: any):
        '''Creates a new record in the database and the cache.'''
        self._records[index] = self.default.copy()

        index = (index,) if not isinstance(index, tuple) else index
        val = index + tuple(self.default.values())
        n = ', '.join(f'${i+1}' for i in range(len(self.default)+len(index)))
        
        async with bot.pool.acquire() as con:
            await con.execute(f'INSERT INTO {self.table} VALUES ({n})', *tuple(val))

    async def update(self, index: any, key: any, val: any):
        '''Updates both the database and the cache. If the record does not exist, it will be created.'''
        if not self._records.get(index):
            await self.insert(index)
        
        self._records[index][key] = val
        if isinstance(val, str):
            val = val.replace('\'', '\'\'')
            val = f'\'{val}\''

        async with bot.pool.acquire() as con:
            if isinstance(index, Iterable):
                condition = ' AND '.join(f'{k} = ${i+1}' for i, k in enumerate(self.pk.split(', ')))
                await con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {condition}', *index)
            else:
                await con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {self.pk} = $1', index)

async def init():
    bot.pool = await asyncpg.create_pool(user='tau', password=config.passwd, database='tau', host='127.0.0.1')

    bot.guilds_ = await Cache('guilds', 'guild_id', utils.guilds_schema, utils._def_guild)
    bot.users_ = await Cache('users', 'user_id', utils.users_schema, utils._def_user)
    bot.members = await Cache('members', 'user_id, guild_id', utils.members_schema, utils._def_member)
    bot.rmenus = await Cache('role_menus', 'guild_id, message_id', utils.role_menus_schema, utils._def_role_menu)
    bot.ranks = await Cache('ranks', 'guild_id', utils.ranks_schema, utils._def_rank)
    bot.stars = await Cache('stars', 'message_id', utils.stars_schema, utils._def_star)
    bot.reminders = await Cache('reminders', 'user_id, time', utils.reminders_schema, utils._def_reminder)
    bot.rules = await Cache('rules', 'guild_id, index_', utils.rules_schema, utils._def_rule)
    bot.modlog = await Cache('modlog', 'user_id, guild_id', utils.modlog_schema, utils._def_modlog)

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
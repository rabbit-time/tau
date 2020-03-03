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

class Cache:
    def __init__(self, table: str, indexname: str, records: dict, default: dict):
        self.table = table
        self.indexname = indexname
        self.__records = records
        self.default = default.copy()

    def __getitem__(self, key: any):
        return self.__records[key]

    def get(self, key: any, default: any = None):
        return self.__records.get(key, default)

    def keys(self):
        return self.__records.keys()

    def values(self):
        return self.__records.values()

    async def delete(self, index: any):
        '''Deletes a record in the database and the cache.'''   
        del self.__records[index]
        if isinstance(index, Iterable):
            condition = self.indexname.replace(', ', ' = ? AND ')
            await bot.con.execute(f'DELETE FROM {self.table} WHERE {condition} = ?', index)
        else:
            await bot.con.execute(f'DELETE FROM {self.table} WHERE {self.indexname} = ?', (index,))
        await bot.con.commit()

    async def insert(self, index: any):
        '''Creates a new record in the database and the cache.'''
        self.__records[index] = self.default.copy()

        index = (index,) if not isinstance(index, tuple) else index
        val = index + tuple(self.default.values())
        n = ('?, ' * (len(self.default)+len(index))).strip(', ')
        
        await bot.con.execute(f'INSERT INTO {self.table} VALUES ({n})', tuple(val))
        await bot.con.commit()

    async def update(self, index: any, key: any, val: any):
        '''Updates both the database and the cache. If the record does not exist, it will be created.'''
        if not self.__records.get(index):
            await self.insert(index)
        
        self.__records[index][key] = val
        if isinstance(val, str):
            val = f'\'{val}\''

        if isinstance(index, Iterable):
            condition = self.indexname.replace(', ', ' = ? AND ')
            await bot.con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {condition} = ?', index)
        else:
            await bot.con.execute(f'UPDATE {self.table} SET {key} = {val} WHERE {self.indexname} = ?', (index,))
        await bot.con.commit()

async def init():
    bot.con = await aiosqlite.connect('srv/db.sqlite3')

    _schema = ('guild_id unsigned bigint PRIMARY KEY, '
               'prefix varchar(255), '
               'system_channel varchar(255), '
               'welcome_message varchar(255), '
               'goodbye_message varchar(255), '
               'welcome_messages bool, '
               'goodbye_messages bool, '
               'levelup_messages bool, '
               'mod_role unsigned bigint, '
               'admin_role unsigned bigint, '
               'bind_role unsigned bigint')
    await bot.con.execute(f'CREATE TABLE IF NOT EXISTS guilds ({_schema})')

    cur = await bot.con.execute('SELECT * FROM guilds')
    _guilds = {}
    records = await cur.fetchall()
    for record in records:
        _guilds[record[0]] = {k: record[i+1] for i, k in enumerate(config._def_guild.keys())}

    _schema = ('user_id unsigned bigint PRIMARY KEY, '
               'tickets bigint, '
               'xp unsigned bigint, '
               'accent char(7), '
               'bio varchar(2000)')
    await bot.con.execute(f'CREATE TABLE IF NOT EXISTS users ({_schema})')

    cur = await bot.con.execute('SELECT * FROM users')
    _users = {}
    records = await cur.fetchall()
    for record in records:
        _users[record[0]] = {k: record[i+1] for i, k in enumerate(config._def_user.keys())}
    
    _schema = ('user_id unsigned bigint, '
               'guild_id unsigned bigint, '
               'muted bigint')
    await bot.con.execute(f'CREATE TABLE IF NOT EXISTS mutes ({_schema})')

    cur = await bot.con.execute('SELECT * FROM mutes')
    _mutes = {}
    records = await cur.fetchall()
    for record in records:
        _mutes[record[:2]] = {k: record[i+2] for i, k in enumerate(config._def_mute.keys())}

    _schema = ('user_id unsigned bigint, '
               'guild_id unsigned bigint, '
               'channel_id unsigned bigint, '
               'message_id unsigned bigint, '
               'detained bigint')
    await bot.con.execute(f'CREATE TABLE IF NOT EXISTS detains ({_schema})')

    cur = await bot.con.execute('SELECT * FROM detains')
    _detains = {}
    records = await cur.fetchall()
    for record in records:
        _detains[record[:2]] = {k: record[i+2] for i, k in enumerate(config._def_detain.keys())}

    _schema = ('guild_id unsigned bigint, '
               'message_id unsigned bigint, '
               'role_ids varchar(250)')
    await bot.con.execute(f'CREATE TABLE IF NOT EXISTS role_menus ({_schema})')

    cur = await bot.con.execute('SELECT * FROM role_menus')
    _role_menus = {}
    records = await cur.fetchall()
    for record in records:
        _role_menus[record[:2]] = {k: record[i+2] for i, k in enumerate(config._def_role_menu.keys())}

    await bot.con.commit()

    bot.guilds_ = Cache('guilds', 'guild_id', _guilds, config._def_guild)
    bot.users_ = Cache('users', 'user_id', _users, config._def_user)
    bot.mutes = Cache('mutes', 'user_id, guild_id', _mutes, config._def_mute)
    bot.detains = Cache('detains', 'user_id, guild_id', _detains, config._def_detain)
    bot.rmenus = Cache('role_menus', 'guild_id, message_id', _role_menus, config._def_role_menu)
    
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
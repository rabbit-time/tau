import asyncio
from datetime import datetime
from logging import Formatter
import os
import sys

import asyncpg
import psutil
import discord
from discord import Activity
from discord.ext.commands import Bot
from discord.utils import oauth_url
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

from utils import Config, CustomCommandTree
from utils.guilds import GuildHandler
from utils.members import MemberTracker, ModRecords
from utils.reminders import ReminderHandler
from utils.role_menus import RoleMenuHandler
from utils.starboards import StarboardHandler
from utils.tags import TagHandler

# Checks the version of python
if sys.version_info[0] < 3 or sys.version_info[1] < 10:
    raise Exception('Python >=3.10.0 is required.')


class Tau(Bot):
    __slots__ = 'conf', 'activity', 'boot_time', 'console', 'mod_records', '_synced', 'url', 'pool', 'guild_confs', 'members', 'reminders', 'role_menus', 'starboards', 'tags'

    url: str
    pool: asyncpg.pool.Pool

    guild_confs: GuildHandler
    members: MemberTracker
    reminders: ReminderHandler
    role_menus: RoleMenuHandler
    starboards: StarboardHandler
    tags: TagHandler

    def __init__(self):
        self.conf = Config.from_json('config.json')

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix='.',
            application_id=self.conf.id,
            help_command=None,
            case_insensitive=True,
            intents=intents,
            tree_cls=CustomCommandTree
        )

        self.activity = Activity(name=f'/help', type=discord.ActivityType.listening)
        self.boot_time = discord.utils.utcnow()
        self.console = Console(tab_size=4, log_time_format='%m.%d.%y %I:%M %p', log_path=False)
        self.mod_records = ModRecords(self)
        self._synced = asyncio.Event()

    @staticmethod
    def memory_usage() -> float:
        '''Returns memory usage in Megabytes'''
        pid = os.getpid()
        process = psutil.Process(pid)
        memory: float = process.memory_info()[0]  # Mem usage in bytes

        return round(memory/1000/1000, 2)  # Conversion to Megabytes

    async def setup_hook(self):
        # Load extensions
        with Progress(
            TextColumn(datetime.now().strftime('%m.%d.%y %I:%M %p'), style='cyan'),
            TextColumn('[progress.description]{task.description}'),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            extensions = [file for file in os.listdir('./src/ext') if '__' not in file and file.endswith('.py')]
            task = progress.add_task('Loading extensions', total=len(extensions))
            for extension in extensions:
                await asyncio.sleep(0.1)

                progress.update(task, description=f'Loading ./src/ext/{extension}', advance=1)

                await self.load_extension(f'ext.{extension[:-3]}')

                self.console.log(f'Loaded ./src/ext/{extension}')

        self.console.log('Syncing...')
        asyncio.create_task(self.sync())

    async def sync(self):
        await self.wait_until_ready()

        self.url = oauth_url(client_id=self.user.id, permissions=discord.Permissions(permissions=8))
        self.pool = await asyncpg.create_pool(user='tau', password=self.conf.passwd, database='tau', host='127.0.0.1')

        self.guild_confs = await GuildHandler(self)
        self.members = await MemberTracker(self)
        self.reminders = await ReminderHandler(self)
        self.role_menus = await RoleMenuHandler(self)
        self.starboards = await StarboardHandler(self)
        self.tags = await TagHandler(self)

        await self.tree.sync()

        self._synced.set()

        self.console.log('Done', style='#ffb38c')
        self.console.log(f'{self.user.name} is online!')
        self.console.log(f'URL: {self.url}')

    async def wait_until_synced(self):
        await self._synced.wait()

    @property
    def synced(self) -> bool:
        return self._synced.is_set()


bot = Tau()
bot.run(
    bot.conf.token,
    log_handler=RichHandler(
        console=bot.console,
        markup=True,
        show_level=False,
        show_path=False
    ),
    log_formatter=Formatter(
        fmt='%(message)s',
        datefmt='%m.%d.%y %I:%M %p'
    )
)

owner_id = 'your_user_id'
admins = () # Bot admins (perm level 4)
invite = 'https://discord.gg/invite' # Invite to server
repo = 'https://github.com/Lumen-01/tau' # GitHub repo link
token = 'DISCORD API TOKEN'
version = '1.1.0'

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
    'muted': -1
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

guilds_schema = ('guild_id unsigned bigint PRIMARY KEY, '
                 'prefix varchar(255), '
                 'system_channel unsigned bigint, '
                 'starboard_channel unsigned bigint, '
                 'star_quantity unsigned tinyint, '
                 'welcome_message varchar(255), '
                 'goodbye_message varchar(255), '
                 'welcome_messages bool, '
                 'goodbye_messages bool, '
                 'levelup_messages bool, '
                 'autorole unsigned bigint, '
                 'mod_role unsigned bigint, '
                 'admin_role unsigned bigint, '
                 'bind_role unsigned bigint')

users_schema = ('user_id unsigned bigint PRIMARY KEY, '
                'tickets bigint, '
                'xp unsigned bigint, '
                'accent char(7), '
                'bio varchar(2000)')

members_schema = ('user_id unsigned bigint, '
                  'guild_id unsigned bigint, '
                  'xp unsigned bigint, '
                  'muted bigint')

role_menus_schema = ('guild_id unsigned bigint, '
                     'message_id unsigned bigint, '
                     'role_ids varchar(250)')

ranks_schema = ('guild_id unsigned bigint PRIMARY KEY, '
                'role_ids varchar(60000)')

stars_schema = ('message_id unsigned bigint PRIMARY KEY, '
                'star_id unsigned bigint')

reminders_schema = ('user_id unsigned bigint, '
                    'time unsigned bigint, '
                    'channel_id unsigned bigint, '
                    'reminder varchar(2048)')

rules_schema = ('guild_id unsigned bigint, '
                'index_ unsigned tinyint, '
                'rule varchar(2000)')

modlog_schema = ('user_id unsigned bigint, '
                 'guild_id unsigned bigint, '
                 'action tinytext, '
                 'time unsigned bigint, '
                 'reason varchar(2048)')
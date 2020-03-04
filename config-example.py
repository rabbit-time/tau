owner_id = 'your_user_id'
admins = () # Bot admins (perm level 4)
invite = 'https://discord.gg/invite' # Invite to server
repo = 'https://github.com/Lumen-01/tau' # GitHub repo link
token = 'DISCORD API TOKEN'
version = '1.0.0'

# Default database values

_def_guild = {
    'prefix': '.',
    'system_channel': 'general',
    'welcome_message': 'Welcome @user! Please enjoy your stay in @guild!',
    'goodbye_message': 'Bye @user!',
    'welcome_messages': False,
    'goodbye_messages': False,
    'levelup_messages': False,
    'mod_role': 0,
    'admin_role': 0,
    'bind_role': 0
}

_def_user = {
    'tickets': 200,
    'xp': 0,
    'accent': '#8bb3f8',
    'bio': 'This is my bio :)'
}

_def_mute = {
    'muted': -1
}

_def_detain = {
    'channel_id': 0,
    'message_id': 0,
    'detained': -1
}

_def_role_menu = {
    'role_ids': ''
}

guilds_schema = ('guild_id unsigned bigint PRIMARY KEY, '
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

users_schema = ('user_id unsigned bigint PRIMARY KEY, '
                'tickets bigint, '
                'xp unsigned bigint, '
                'accent char(7), '
                'bio varchar(2000)')
    
mutes_schema = ('user_id unsigned bigint, '
                'guild_id unsigned bigint, '
                'muted bigint')

detains_schema = ('user_id unsigned bigint, '
                  'guild_id unsigned bigint, '
                  'channel_id unsigned bigint, '
                  'message_id unsigned bigint, '
                  'detained bigint')

role_menus_schema = ('guild_id unsigned bigint, '
                     'message_id unsigned bigint, '
                     'role_ids varchar(250)')
# **Tau**

A general purpose Discord bot and a personal passion project of mine.

+ **[Add it to my server!](https://discord.com/oauth2/authorize?client_id=608367259123187741&scope=bot&permissions=8)**

## Features

+ Server management
+ XP progression system
+ Rank roles
+ Economy system
+ Embed creation
+ GIF commands
+ Informational commands
+ Mod Logging
+ Reminders
+ Starboard
+ Tag system

## Installation
### Install Python >=3.10.0

+ **[python.org/downloads](https://www.python.org/downloads/)**

### Initialize the database

First, install the latest version of PostgreSQL here: **[postgresql.org/downloads](https://www.postgresql.org/download/)**

Next, run `psql` on the command line and run the following statements:

```sql
-- Replace passwd with a secure password 
CREATE ROLE tau LOGIN PASSWORD 'passwd';
CREATE DATABASE tau WITH OWNER tau;
```

### Create the config file

In `./src`, create a file called `config.json` and add the following config:

```js
// Currently, all values are required
{
    "name": "Tau", // The application name displayed in some commands
    "repository": "https://github.com/emisdumb/tau",
    "version": "3.0.0",

    "id": 0, // The application ID
    "passwd": "", // The password used for Postgres
    "token": "", // Discord API Token
    "tenor_api_key": "", // Tenor API Key
    "developer_guild_id": 0 // For access to developer commands
}
```

### Install dependencies

To install the rest of the dependencies, simply run `pip install -U -r requirements.txt` in the project folder.

### Configure intents

Finally, head into the **[Discord developer portal](https://discord.com/developers/applications/)**, select your application, then enable all Privileged Intents under the *Bot* tab.

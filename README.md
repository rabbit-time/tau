# **Tau**

A general purpose Discord bot and a personal passion project of mine.

+ **[Add it to my server!](https://discord.com/oauth2/authorize?client_id=608367259123187741&scope=bot&permissions=8)**

## Features

+ Server management
+ Rank roles
+ XP and leveling system
+ Currency
+ Information commands
+ Fun commands
+ Starboard
+ and much more...

## Installation

I would kindly ask that this bot isn't run as a separate instance. I am a firm believer in open source software and wanted to provide the source code publicly. In any case, here is the installation procedure.

### Install Python >=3.8.x

+ **[python.org/downloads](https://www.python.org/downloads/)**

### Initialize the database

First, install the latest version of PostgreSQL here: **[postgresql.org/downloads](https://www.postgresql.org/download/)**

Next, type `psql` on the command line and run the following statements:

```sql
-- Replace passwd with a secure password 
CREATE ROLE tau LOGIN PASSWORD 'passwd';
CREATE DATABASE tau WITH OWNER tau;
```

### Create the config file

In the project folder, create a file called `config.py` and copy the following code and fill out the values of each variable:

```py
admins = (000000000000000000, 000000000000000000) # Bot admins (perm level 4)
passwd = 'passwd' # PostgreSQL password
invite = 'https://discord.gg/invite' # Invite to server
repo = 'https://github.com/Lumen-01/tau' # GitHub repo link
token = 'DISCORD API TOKEN'
tenor_api_key = 'TENOR API KEY'
version = '2.1.0'
```

### Install dependencies

To install the rest of the requirements, simply run `pip install -U -r depn.txt` in the project folder.

### Configure intents

Finally, head into the **[Discord developer portal](https://discord.com/developers/applications/)**, select your application, then enable all Privileged Intents under the *Bot* tab like so:

![intents.png](https://cdn.discordapp.com/attachments/597739781568331776/779243312736894986/intents.png)
